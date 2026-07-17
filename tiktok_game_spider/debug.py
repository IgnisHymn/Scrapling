"""调试工具 - 用于分析页面结构，找到稳定的元素定位方式"""
import asyncio
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from config import SpiderConfig
from utils.browser import BrowserManager
from page_parser import PageParser


async def debug_page(url):
    """调试页面，输出iframe内容"""
    config = SpiderConfig()
    config.HEADLESS = False  # 调试时显示浏览器
    
    print("=" * 60)
    print(f"调试模式 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"目标URL: {url}")
    print()
    
    browser_manager = BrowserManager(config)
    context = await browser_manager.start_with_profile()
    
    try:
        page = await context.new_page()
        
        print("正在加载页面...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)  # 等待iframe加载
        
        # 获取所有iframe信息
        frames = page.frames
        print(f"\n页面共有 {len(frames)} 个frame:")
        for i, frame in enumerate(frames):
            print(f"  [{i}] name='{frame.name}', title='{frame.title}', url='{frame.url[:80]}...'")
        
        # 获取目标iframe内容
        parser = PageParser(page, config.IFRAME_TITLE)
        
        print("\n获取iframe结构...")
        structure = await parser.get_frame_structure()
        print(f"页面结构:\n{structure}")
        
        print("\n获取iframe文本内容...")
        text = await parser.extract_all_text_from_frame()
        
        # 保存调试信息
        debug_dir = Path(__file__).parent / "debug"
        debug_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存文本内容
        text_file = debug_dir / f"frame_text_{timestamp}.txt"
        text_file.write_text(text, encoding="utf-8")
        print(f"文本内容已保存: {text_file}")
        
        # 保存HTML内容
        html = await parser.get_frame_html()
        html_file = debug_dir / f"frame_html_{timestamp}.html"
        html_file.write_text(html, encoding="utf-8")
        print(f"HTML内容已保存: {html_file}")
        
        print("\n" + "=" * 60)
        print("调试完成! 请查看保存的文件分析页面结构")
        print("=" * 60)
        
        input("\n按回车关闭浏览器...")
        
    except Exception as e:
        print(f"调试出错: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车关闭浏览器...")
        
    finally:
        await browser_manager.close()


if __name__ == "__main__":
    # 测试URL - 替换为实际的app_id
    test_app_id = input("请输入要调试的app_id (或按回车使用默认值): ").strip()
    if not test_app_id:
        test_app_id = "YOUR_APP_ID"
    
    test_url = f"https://developers.tiktok.com/portal/game/{test_app_id}/monetization"
    asyncio.run(debug_page(test_url))
