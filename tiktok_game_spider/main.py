"""主入口文件 - TikTok小游戏爬虫"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import SpiderConfig
from excel_reader import ExcelReader
from login import TikTokLogin
from page_parser import PageParser
from report import ExcelSaver
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
    
    # 2. 初始化Excel保存器
    excel_saver = ExcelSaver(config.DAYS_REPORT_PATH)
    
    # 3. 启动浏览器
    print("正在启动浏览器...")
    browser_manager = BrowserManager(config)
    context = await browser_manager.start()
    
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
            
            monetization_data = {}
            dashboard_data = {}
            date_str = None
            
            # 访问变现数据页面
            monetization_url = f"{base_url}/{app_id}/monetization?tab=iaa"
            print(f"  访问变现页面: {monetization_url}")
            try:
                await page.goto(monetization_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(7)

                # 获取iframe
                target_frame = await parser.get_target_frame()
                if target_frame:
                    print(f"  找到目标iframe")
                    # 在iframe中选择日期
                    date_str = await parser.select_date_in_iframe(target_frame)
                    # 从iframe中获取All区域变现数据
                    monetization_data = await parser.get_monetization_data(target_frame)
                    print(f"  All区域变现数据提取完成")
                    
                    # 切换到US区域获取US数据
                    print(f"  切换到US区域...")
                    await parser.select_region_us(target_frame)
                    us_data = await parser.get_us_monetization_data(target_frame)
                    monetization_data["eCPM（US）"] = us_data.get("eCPM", "N/A")
                    monetization_data["广告收入（US）"] = us_data.get("Ad revenue", "N/A")
                    print(f"  US区域数据提取完成")
                else:
                    print(f"  未找到目标iframe")
            except Exception as e:
                print(f"  变现页面解析失败: {e}")
            
            # 访问数据仪表板页面
            dashboard_url = f"{base_url}/{app_id}/data-dashboard"
            print(f"  访问仪表板页面: {dashboard_url}")
            try:
                await page.goto(dashboard_url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(7)
                
                # 获取iframe
                target_frame = await parser.get_target_frame()
                if target_frame:
                    print(f"  找到目标iframe")
                    # 在iframe中选择日期
                    if not date_str:
                        date_str = await parser.select_date_in_iframe(target_frame)
                    else:
                        await parser.select_date_in_iframe(target_frame)
                    # 从iframe中获取Users数据
                    dashboard_data = await parser.get_dashboard_data(target_frame)
                    print(f"  Users数据提取完成")
                    
                    # 切换到Performance标签
                    print(f"  切换到Performance标签...")
                    await parser.click_performance_tab(target_frame)
                    # 选择相同日期范围
                    if date_str:
                        await parser.select_date_in_iframe(target_frame)
                    # 获取Performance数据
                    perf_data = await parser.get_performance_data(target_frame)
                    dashboard_data["启动成功率"] = perf_data.get("Launch success rate", "N/A")
                    dashboard_data["首次平均启动速度"] = perf_data.get("Average first-time launch speed", "N/A")
                    dashboard_data["平均启动速度"] = perf_data.get("Average launch speed", "N/A")
                    print(f"  Performance数据提取完成")
                else:
                    print(f"  未找到目标iframe")
            except Exception as e:
                print(f"  仪表板页面解析失败: {e}")
            
            # 保存数据到Excel
            if date_str:
                excel_saver.save_data(app_name, date_str, monetization_data, dashboard_data)
                print(f"  数据已保存到 {app_name} sheet")
            else:
                print(f"  跳过保存：未获取到日期")
        
        print("\n" + "=" * 40)
        print("所有游戏数据爬取完成!")
        print("=" * 40)
        
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
