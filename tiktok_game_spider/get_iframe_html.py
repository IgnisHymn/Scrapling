"""获取iframe HTML内容并分析"""
import asyncio
from playwright.async_api import async_playwright


async def get_iframe_html():
    print("=" * 60)
    print("获取iframe HTML内容")
    print("=" * 60)
    
    EMAIL = "tlciber37@gmail.com"
    PASSWORD = "122334Xbt!"
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()
    
    # 登录
    print("\n[1] 登录...")
    await page.goto("https://developers.tiktok.com/login", wait_until="networkidle")
    await asyncio.sleep(2)
    await page.locator('input[data-e2e="TUXTextInput"][name="email"]').fill(EMAIL)
    await asyncio.sleep(0.5)
    await page.locator('input[data-e2e="TUXPasswordInput"][name="password"]').fill(PASSWORD)
    await asyncio.sleep(0.5)
    await page.wait_for_selector('button[type="submit"]:not([disabled])', timeout=10000)
    await page.locator('button[data-e2e="TUXButton"][type="submit"]').click()
    await asyncio.sleep(5)
    
    # 访问目标页面
    print("[2] 访问目标页面...")
    await page.goto("https://developers.tiktok.com/portal/game/7655169914772260880/monetization", wait_until="networkidle")
    await asyncio.sleep(5)
    
    # 获取目标iframe
    frames = page.frames
    target_frame = None
    for frame in frames:
        if "developers.us.tiktok.com" in frame.url:
            target_frame = frame
            break
    
    if target_frame:
        print("[3] 获取iframe HTML...")
        
        # 等待iframe内容加载
        await asyncio.sleep(3)
        
        # 获取HTML
        html = await target_frame.content()
        
        # 保存到文件
        with open("iframe_content.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  HTML已保存到 iframe_content.html ({len(html)} 字节)")
        
        # 尝试等待更长时间后再次获取inner_text
        print("\n[4] 等待5秒后重试 inner_text...")
        await asyncio.sleep(5)
        
        try:
            text = await target_frame.locator("body").inner_text()
            print(f"  inner_text长度: {len(text)}")
            if text:
                print(f"  内容: {text[:500]}")
        except Exception as e:
            print(f"  失败: {e}")
        
        # 尝试获取特定元素
        print("\n[5] 尝试获取页面元素...")
        try:
            # 尝试获取所有div
            divs = await target_frame.query_selector_all("div")
            print(f"  找到 {len(divs)} 个div")
            
            # 尝试获取所有文本节点
            all_text = await target_frame.evaluate("""
                () => {
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    const texts = [];
                    while (walker.nextNode()) {
                        const text = walker.currentNode.textContent.trim();
                        if (text) texts.push(text);
                    }
                    return texts.join('\\n');
                }
            """)
            print(f"  文本节点内容长度: {len(all_text)}")
            if all_text:
                print(f"  内容预览:\n{all_text[:500]}")
        except Exception as e:
            print(f"  失败: {e}")
    else:
        print("未找到目标iframe")
    
    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)
    
    await asyncio.sleep(10)
    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(get_iframe_html())
