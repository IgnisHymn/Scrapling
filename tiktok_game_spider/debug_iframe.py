"""iframe调试工具 - 分析页面中的iframe结构"""
import asyncio
from playwright.async_api import async_playwright


async def debug_iframe():
    """调试iframe结构"""
    print("=" * 60)
    print("iframe调试工具")
    print("=" * 60)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()
    
    url = input("\n请输入要调试的URL: ").strip()
    if not url:
        url = "https://developers.tiktok.com/portal/game/test/monetization"
    
    print(f"\n正在访问: {url}")
    await page.goto(url, wait_until="networkidle")
    await asyncio.sleep(3)  # 等待iframe加载
    
    print("\n" + "=" * 60)
    print("页面iframe分析")
    print("=" * 60)
    
    # 方法1: 获取所有iframe元素
    print("\n[方法1] 查找所有iframe元素:")
    iframes = await page.query_selector_all("iframe")
    print(f"找到 {len(iframes)} 个iframe元素")
    
    for i, iframe in enumerate(iframes):
        title = await iframe.get_attribute("title")
        name = await iframe.get_attribute("name")
        src = await iframe.get_attribute("src")
        print(f"\n  iframe[{i}]:")
        print(f"    title: {title}")
        print(f"    name: {name}")
        print(f"    src: {src[:100] if src else 'None'}...")
    
    # 方法2: 获取所有frame对象
    print("\n[方法2] 页面frame对象:")
    frames = page.frames
    print(f"页面共有 {len(frames)} 个frame")
    
    for i, frame in enumerate(frames):
        print(f"\n  frame[{i}]:")
        print(f"    name: '{frame.name}'")
        print(f"    title: '{frame.title}'")
        print(f"    url: {frame.url[:80]}...")
    
    # 方法3: 尝试不同的选择器
    print("\n[方法3] 测试不同的选择器:")
    selectors = [
        "iframe",
        "iframe[title]",
        "iframe[title*='TikTok']",
        "iframe[title*='embedded']",
        "iframe[title*='view']",
        "iframe[name]",
        "iframe[src]",
        "iframe[title='TikTok for Developers embedded view']",
    ]
    
    for selector in selectors:
        try:
            elements = await page.query_selector_all(selector)
            print(f"  '{selector}' -> 找到 {len(elements)} 个")
        except Exception as e:
            print(f"  '{selector}' -> 错误: {e}")
    
    # 方法4: 获取页面HTML片段（只看iframe部分）
    print("\n[方法4] iframe相关HTML:")
    iframe_html = await page.evaluate("""
        () => {
            const iframes = document.querySelectorAll('iframe');
            return Array.from(iframes).map(f => f.outerHTML).join('\\n');
        }
    """)
    print(iframe_html[:2000] if iframe_html else "未找到iframe")
    
    # 方法5: 检查是否有shadow DOM
    print("\n[方法5] 检查shadow DOM:")
    shadow_hosts = await page.evaluate("""
        () => {
            const hosts = [];
            document.querySelectorAll('*').forEach(el => {
                if (el.shadowRoot) {
                    hosts.push({
                        tag: el.tagName,
                        id: el.id,
                        class: el.className
                    });
                }
            });
            return hosts;
        }
    """)
    if shadow_hosts:
        print(f"找到 {len(shadow_hosts)} 个shadow host:")
        for host in shadow_hosts[:5]:
            print(f"  <{host['tag']}> id='{host['id']}' class='{host['class']}'")
    else:
        print("未找到shadow DOM")
    
    print("\n" + "=" * 60)
    print("调试完成！请将以上信息告诉我")
    print("=" * 60)
    
    input("\n按回车关闭浏览器...")
    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(debug_iframe())
