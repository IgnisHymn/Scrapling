"""主入口文件 - TikTok小游戏爬虫"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import SpiderConfig
from excel_reader import ExcelReader
from login import TikTokLogin
from page_parser import PageParser
from report import ReportGenerator
from utils.browser import BrowserManager


async def run_spider():
    """运行爬虫"""
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
        return
    
    # 2. 初始化报告生成器
    report_gen = ReportGenerator(config.REPORT_DIR)
    
    # 3. 启动浏览器
    print("正在启动浏览器...")
    browser_manager = BrowserManager(config)
    context = await browser_manager.start()
    
    all_data = []
    
    try:
        page = await context.new_page()
        
        # 4. 自动登录
        print("\n" + "=" * 40)
        print("正在登录TikTok开发者平台...")
        print("=" * 40)
        login = TikTokLogin(page, config)
        await login.login()
        
        parser = PageParser(page, config.IFRAME_TITLE)
        
        # 5. 遍历所有游戏并爬取数据
        print("\n" + "=" * 40)
        print("开始爬取游戏数据...")
        print("=" * 40)
        
        for i, app in enumerate(apps, 1):
            app_name = app["name"]
            app_id = app["app_id"]
            
            print(f"\n[{i}/{len(apps)}] 处理游戏: {app_name} (ID: {app_id})")
            
            app_data = {
                "name": app_name,
                "app_id": app_id,
                "monetization": {},
                "dashboard": {}
            }
            
            # 访问变现数据页面
            monetization_url = f"{base_url}/{app_id}/monetization?tab=iaa"
            print(f"  访问变现页面: {monetization_url}")
            try:
                await page.goto(monetization_url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(5)
                
                # 获取iframe
                target_frame = await parser.get_target_frame()
                if target_frame:
                    print(f"  找到目标iframe")
                    # 在iframe中选择日期
                    await parser.select_date_in_iframe(target_frame)
                    # 从iframe中获取数据
                    app_data["monetization"] = await parser.get_data_from_iframe(target_frame)
                    print(f"  变现数据提取完成")
                else:
                    print(f"  未找到目标iframe")
                    app_data["monetization"] = {"error": "未找到iframe"}
            except Exception as e:
                print(f"  变现页面解析失败: {e}")
                app_data["monetization"] = {"error": str(e)}
            
            # 访问数据仪表板页面
            dashboard_url = f"{base_url}/{app_id}/data-dashboard"
            print(f"  访问仪表板页面: {dashboard_url}")
            try:
                await page.goto(dashboard_url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(3)
                
                # 获取iframe
                target_frame = await parser.get_target_frame()
                if target_frame:
                    print(f"  找到目标iframe")
                    # 在iframe中选择日期
                    await parser.select_date_in_iframe(target_frame)
                    # 从iframe中获取数据
                    app_data["dashboard"] = await parser.get_data_from_iframe(target_frame)
                    print(f"  仪表板数据提取完成")
                else:
                    print(f"  未找到目标iframe")
                    app_data["dashboard"] = {"error": "未找到iframe"}
            except Exception as e:
                print(f"  仪表板页面解析失败: {e}")
                app_data["dashboard"] = {"error": str(e)}
            
            all_data.append(app_data)
        
        # 6. 保存原始数据
        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_file = config.OUTPUT_DIR / f"tiktok_games_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"\n原始数据已保存: {output_file}")
        
        # 7. 生成HTML报告
        report_path = report_gen.generate(all_data)
        print(f"HTML报告已生成: {report_path}")
        
    except Exception as e:
        print(f"爬虫运行出错: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await browser_manager.close()


def main():
    """主函数"""
    print("=" * 60)
    print(f"TikTok小游戏爬虫 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    asyncio.run(run_spider())
    
    print("\n" + "=" * 60)
    print("爬虫运行完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
