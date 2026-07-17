"""浏览器交互工具 - 手动操作并记录选择器"""
import asyncio
from playwright.async_api import async_playwright


async def interactive_browser():
    """启动交互式浏览器，手动操作后记录页面结构"""
    print("=" * 60)
    print("交互式浏览器模式")
    print("=" * 60)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()
    
    # 导航到目标页面
    url = input("\n请输入要访问的URL (或按回车使用默认): ").strip()
    if not url:
        url = "https://developers.tiktok.com/login"
    
    print(f"\n正在访问: {url}")
    await page.goto(url)
    
    print("\n" + "=" * 60)
    print("浏览器已打开，请手动操作")
    print("=" * 60)
    
    while True:
        print("\n可用命令:")
        print("  1. 输入 'url <新URL>' - 导航到新页面")
        print("  2. 输入 'html' - 获取当前页面HTML")
        print("  3. 输入 'text' - 获取当前页面文本")
        print("  4. 输入 'frames' - 列出所有iframe")
        print("  5. 输入 'frame <title>' - 获取指定iframe内容")
        print("  6. 输入 'selector <选择器>' - 测试选择器")
        print("  7. 输入 'screenshot' - 截图")
        print("  8. 输入 'quit' - 退出")
        
        cmd = input("\n请输入命令: ").strip()
        
        if cmd.startswith("url "):
            new_url = cmd[4:].strip()
            print(f"导航到: {new_url}")
            await page.goto(new_url)
            
        elif cmd == "html":
            html = await page.content()
            with open("page.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("HTML已保存到 page.html")
            
        elif cmd == "text":
            text = await page.inner_text("body")
            print(f"\n页面文本:\n{text[:2000]}...")
            
        elif cmd == "frames":
            frames = page.frames
            print(f"\n页面共有 {len(frames)} 个frame:")
            for i, frame in enumerate(frames):
                print(f"  [{i}] name='{frame.name}', title='{frame.title}'")
                
        elif cmd.startswith("frame "):
            frame_title = cmd[6:].strip()
            frame = page.frame(title=frame_title)
            if frame:
                html = await frame.content()
                with open("frame.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"iframe内容已保存到 frame.html")
            else:
                print(f"未找到title='{frame_title}'的iframe")
                
        elif cmd.startswith("selector "):
            selector = cmd[9:].strip()
            try:
                elements = await page.locator(selector).all()
                print(f"找到 {len(elements)} 个元素")
                for i, elem in enumerate(elements[:5]):
                    text = await elem.inner_text()
                    print(f"  [{i}] {text[:100]}")
            except Exception as e:
                print(f"选择器错误: {e}")
                
        elif cmd == "screenshot":
            await page.screenshot(path="screenshot.png")
            print("截图已保存到 screenshot.png")
            
        elif cmd == "quit":
            break
            
        else:
            print("未知命令")
    
    await browser.close()
    await playwright.stop()
    print("浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(interactive_browser())
