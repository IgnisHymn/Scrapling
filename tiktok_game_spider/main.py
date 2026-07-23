"""主入口文件 - TikTok小游戏爬虫"""
import asyncio
import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import SpiderConfig
from excel_reader import ExcelReader
from login import TikTokLogin
from page_parser import PageParser
from report import ExcelSaver
from feishu_sync import FeishuSync
from utils.browser import BrowserManager

# 锁文件路径
LOCK_FILE = Path(__file__).parent / "output" / ".tiktok_report.lock"


async def run_spider() -> tuple[int, list[dict]]:
    """运行爬虫，返回 (游戏数量, 失败游戏列表)"""
    config = SpiderConfig()
    
    # 1. 读取Excel配置
    print("正在读取Excel配置...")
    excel_reader = ExcelReader(config.EXCEL_PATH)
    apps = excel_reader.read_apps()
    base_url = excel_reader.read_base_url()
    
    print(f"读取到 {len(apps)} 个游戏配置")
    print(f"基础URL: {base_url}")
    
    if not apps:
        print("错误: 未读取到任何游戏配置，请检查Excel文件")
        return 0, []
    
    # 2. 初始化Excel保存器
    excel_saver = ExcelSaver(config.DAYS_REPORT_PATH)
    
    # 初始化飞书同步
    feishu_sync = FeishuSync()
    
    # 3. 启动浏览器
    print("正在启动浏览器...")
    browser_manager = BrowserManager(config)
    context = await browser_manager.start()
    
    failed_games = []  # 记录失败的游戏
    
    # 定义处理单个游戏的函数
    async def process_game(app_name: str, app_id: str) -> bool:
        """处理单个游戏，返回是否成功"""
        nonlocal page, parser
        
        monetization_data = {}
        dashboard_data = {}
        date_str = None
        has_error = False
        
        # 访问变现数据页面
        monetization_url = f"{base_url}/{app_id}/monetization?tab=iaa"
        print(f"  访问变现页面: {monetization_url}")
        try:
            await page.goto(monetization_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_selector('iframe[title="TikTok for Developers embedded view"]', timeout=30000)

            target_frame = await parser.get_target_frame()
            if target_frame:
                print(f"  找到目标iframe")
                date_str = await parser.select_date_in_iframe(target_frame)
                monetization_data = await parser.get_monetization_data(target_frame)
                print(f"  All区域变现数据提取完成")
                
                print(f"  切换到US区域...")
                await parser.select_region_us(target_frame)
                us_data = await parser.get_us_monetization_data(target_frame)
                monetization_data["eCPM（US）"] = us_data.get("eCPM", "N/A")
                monetization_data["广告收入（US）"] = us_data.get("Ad revenue", "N/A")
                print(f"  US区域数据提取完成")
            else:
                print(f"  未找到目标iframe")
                has_error = True
        except Exception as e:
            print(f"  变现页面解析失败: {e}")
            has_error = True
        
        # 访问数据仪表板页面
        dashboard_url = f"{base_url}/{app_id}/data-dashboard"
        print(f"  访问仪表板页面: {dashboard_url}")
        try:
            await page.goto(dashboard_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_selector('iframe[title="TikTok for Developers embedded view"]', timeout=30000)
            
            target_frame = await parser.get_target_frame()
            if target_frame:
                print(f"  找到目标iframe")
                if not date_str:
                    date_str = await parser.select_date_in_iframe(target_frame)
                else:
                    await parser.select_date_in_iframe(target_frame)
                dashboard_data = await parser.get_dashboard_data(target_frame)
                print(f"  Users数据提取完成")
                
                print(f"  切换到Performance标签...")
                await parser.click_performance_tab(target_frame)
                if date_str:
                    await parser.select_date_in_iframe(target_frame)
                perf_data = await parser.get_performance_data(target_frame)
                dashboard_data["启动成功率"] = perf_data.get("Launch success rate", "N/A")
                dashboard_data["首次平均启动速度"] = perf_data.get("Average first-time launch speed", "N/A")
                dashboard_data["平均启动速度"] = perf_data.get("Average launch speed", "N/A")
                print(f"  Performance数据提取完成")
            else:
                print(f"  未找到目标iframe")
                has_error = True
        except Exception as e:
            print(f"  仪表板页面解析失败: {e}")
            has_error = True
        
        # 保存数据到Excel
        if date_str:
            try:
                excel_saver.save_data(app_name, date_str, monetization_data, dashboard_data)
                print(f"  数据已保存到 {app_name} sheet")
            except Exception as e:
                print(f"  Excel 保存失败（可能被占用）: {e}")
            
            try:
                feishu_sync.sync_game_data(app_name, date_str, monetization_data, dashboard_data)
            except Exception as e:
                print(f"  飞书同步失败: {e}")
        else:
            print(f"  跳过保存：未获取到日期")
            has_error = True
        
        return not has_error
    
    try:
        page = await context.new_page()
        
        # 4. 自动登录
        print("\n" + "=" * 40)
        print("正在登录TikTok开发者平台...")
        print("=" * 40)
        login = TikTokLogin(page, config)
        await login.login()
        
        # 登录成功后保存浏览器状态
        await browser_manager.save_state()
        
        parser = PageParser(page, config.IFRAME_TITLE)
        
        # 5. 遍历所有游戏并爬取数据
        print("\n" + "=" * 40)
        print("开始爬取游戏数据...")
        print("=" * 40)
        
        for i, app in enumerate(apps, 1):
            app_name = app["name"]
            app_id = app["app_id"]
            
            print(f"\n[{i}/{len(apps)}] 处理游戏: {app_name} (ID: {app_id})")
            
            success = await process_game(app_name, app_id)
            
            if not success:
                failed_games.append({"name": app_name, "app_id": app_id})
                print(f"  [失败] {app_name} 处理失败，跳过继续下一个游戏")
        
        print("\n" + "=" * 40)
        print("所有游戏数据爬取完成!")
        if failed_games:
            print(f"失败游戏: {len(failed_games)} 个")
        print("=" * 40)
        
    except Exception as e:
        print(f"爬虫运行出错: {e}")
        import traceback
        traceback.print_exc()
        raise  # 重新抛出，让 main() 知道失败了
        
    finally:
        await browser_manager.close()
    
    return len(apps), failed_games


def send_feishu_notification(success, duration, game_count, output_path, error_msg=None):
    """发送飞书通知"""
    openclaw_config_path = Path.home() / ".openclaw" / "openclaw.json"
    try:
        with open(openclaw_config_path, "r", encoding="utf-8") as f:
            openclaw_config = json.load(f)
        app_id = openclaw_config.get("channels", {}).get("feishu", {}).get("appId")
        app_secret = openclaw_config.get("channels", {}).get("feishu", {}).get("appSecret")
    except Exception:
        print("无法读取 OpenClaw 配置，跳过飞书通知")
        return

    if not app_id or not app_secret:
        print("飞书配置缺少 appId 或 appSecret，跳过飞书通知")
        return

    chat_id = "oc_f4d01fa850e2449c97a51cbabae073f3"
    timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    status_icon = "✅" if success else "❌"
    status_text = "成功" if success else "失败"

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "TikTok 小游戏爬虫报告"},
            "template": "blue" if success else "red"
        },
        "elements": [
            {
                "tag": "div",
                "fields": [
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**执行状态**\n{status_icon} {status_text}"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**执行耗时**\n{duration} 秒"}}
                ]
            },
            {"tag": "hr"},
            {
                "tag": "div",
                "fields": [
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**游戏数量**\n{game_count}"}}
                ]
            },
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"**输出文件**\n`{output_path}`"}
            }
        ]
    }

    if error_msg:
        card["elements"].append({"tag": "hr"})
        card["elements"].append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"**错误信息**\n{error_msg}"}
        })

    card["elements"].append({"tag": "hr"})
    card["elements"].append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": f"处理时间: {timestamp}"}]
    })

    try:
        token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        token_data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
        token_req = urllib.request.Request(token_url, data=token_data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(token_req) as resp:
            token_result = json.loads(resp.read())
        if token_result.get("code") != 0:
            print(f"获取飞书token失败: {token_result}")
            return
        token = token_result["tenant_access_token"]

        msg_url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
        msg_data = json.dumps({
            "receive_id": chat_id,
            "msg_type": "interactive",
            "content": json.dumps(card)
        }).encode()
        msg_req = urllib.request.Request(msg_url, data=msg_data, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        })
        with urllib.request.urlopen(msg_req) as resp:
            msg_result = json.loads(resp.read())
        if msg_result.get("code") == 0:
            print("飞书通知发送成功")
        else:
            print(f"飞书通知发送失败: {msg_result}")
    except Exception as e:
        print(f"飞书通知发送异常: {e}")


def save_failed_games(failed_games: list[dict], output_dir: Path):
    """保存失败游戏列表到 JSON 文件"""
    if not failed_games:
        return
    failed_file = output_dir / "failed_games.json"
    try:
        with open(failed_file, "w", encoding="utf-8") as f:
            json.dump(failed_games, f, ensure_ascii=False, indent=2)
        print(f"失败游戏列表已保存到: {failed_file}")
    except Exception as e:
        print(f"保存失败游戏列表出错: {e}")


def acquire_lock() -> bool:
    """获取锁，如果已锁定则返回 False"""
    if LOCK_FILE.exists():
        # 检查锁文件是否过期（超过 30 分钟认为是残留锁）
        try:
            lock_time = LOCK_FILE.stat().st_mtime
            if (time.time() - lock_time) > 1800:  # 30 分钟
                print("发现过期锁文件，清理中...")
                LOCK_FILE.unlink()
            else:
                return False
        except:
            return False
    
    # 创建锁文件
    try:
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOCK_FILE.write_text(str(os.getpid()))
        return True
    except:
        return False


def release_lock():
    """释放锁"""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except:
        pass


def main():
    """主函数"""
    # 检查锁
    if not acquire_lock():
        print("另一个 tiktok-report 任务正在运行，本次跳过")
        print("如需强制运行，请删除锁文件: " + str(LOCK_FILE))
        # 发送跳过通知
        send_feishu_notification(
            success=False,
            duration="0",
            game_count=0,
            output_path="",
            error_msg="任务被跳过：另一个实例正在运行"
        )
        return
    
    try:
        start_time = datetime.now()
        print("=" * 60)
        print(f"TikTok小游戏爬虫 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        success = False
        game_count = 0
        failed_games = []
        config = SpiderConfig()
        output_path = Path(config.DAYS_REPORT_PATH)
        network_path = Path(config.DAYS_REPORT_NETWORK_PATH)
        error_msg = None

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            game_count, failed_games = asyncio.run(run_spider())
            success = True
        except Exception as e:
            error_msg = str(e)
            print(f"爬虫运行出错: {e}")

        # 保存失败游戏列表
        save_failed_games(failed_games, output_path.parent)

        # Copy to network share
        if success:
            import shutil
            try:
                network_path.parent.mkdir(parents=True, exist_ok=True)
                lock_file = network_path.parent / f"~${network_path.name}"
                if lock_file.exists():
                    try:
                        lock_file.unlink()
                    except:
                        pass
                shutil.copy2(output_path, network_path)
                print(f"已复制到网络路径: {network_path}")
            except Exception as e:
                print(f"复制到网络路径失败: {e}")
                error_msg = f"数据已保存到本地但复制到网络失败: {e}"
        
        duration = (datetime.now() - start_time).total_seconds()

        print("\n" + "=" * 60)
        print("爬虫运行完成!" if success else "爬虫运行失败!")
        if failed_games:
            print(f"失败游戏: {len(failed_games)} 个")
        print("=" * 60)

        # 构建通知消息
        notify_path = network_path if success else output_path
        if failed_games:
            failed_names = ", ".join(g["name"] for g in failed_games)
            extra_msg = f"失败游戏 ({len(failed_games)}): {failed_names}"
            error_msg = f"{error_msg}\n{extra_msg}" if error_msg else extra_msg
        
        send_feishu_notification(success, f"{duration:.2f}", game_count, notify_path, error_msg)
    
    finally:
        release_lock()


if __name__ == "__main__":
    main()
