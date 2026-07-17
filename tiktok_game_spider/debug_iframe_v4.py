"""调试iframe - 正确获取frame"""
import asyncio
from playwright.async_api import async_playwright


async def debug_iframe():
    print("=" * 60)
    print("iframe访问调试（最终版）")
    print("=" * 60)
    
    EMAIL = "tlciber37@gmail.com"
    PASSWORD = "122334Xbt!"
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()
    
    # 登录
    print("\n[步骤1] 登录...")
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
    print("\n[步骤2] 访问目标页面...")
    await page.goto("https://developers.tiktok.com/portal/game/7655169914772260880/monetization", wait_until="networkidle")
    await asyncio.sleep(5)
    
    # 获取所有frame
    print("\n[步骤3] 获取所有frame...")
    frames = page.frames
    print(f"共有 {len(frames)} 个frame:")
    
    target_frame = None
    for i, frame in enumerate(frames):
        print(f"\n  frame[{i}]:")
        print(f"    name: '{frame.name}'")
        print(f"    url: '{frame.url[:80]}...'")
        
        # 找到目标iframe（通过URL判断）
        if "developers.us.tiktok.com" in frame.url:
            target_frame = frame
            print(f"    >>> 这是目标iframe!")
    
    if target_frame:
        print("\n[步骤4] 测试获取iframe内容...")
        
        # 方法1: inner_text
        print("\n  方法1: locator('body').inner_text()")
        try:
            text = await target_frame.locator("body").inner_text()
            print(f"    成功! 长度: {len(text)}")
            print(f"    预览: {text[:300]}")
        except Exception as e:
            print(f"    失败: {e}")
        
        # 方法2: evaluate
        print("\n  方法2: evaluate('() => document.body.innerText')")
        try:
            text = await target_frame.evaluate("() => document.body.innerText")
            print(f"    成功! 长度: {len(text)}")
            print(f"    预览: {text[:300]}")
        except Exception as e:
            print(f"    失败: {e}")
        
        # 方法3: content
        print("\n  方法3: content()")
        try:
            html = await target_frame.content()
            print(f"    成功! 长度: {len(html)}")
        except Exception as e:
            print(f"    失败: {e}")
        
        # 方法4: query_selector
        print("\n  方法4: query_selector_all('table')")
        try:
            tables = await target_frame.query_selector_all("table")
            print(f"    找到 {len(tables)} 个表格")
        except Exception as e:
            print(f"    失败: {e}")
    else:
        print("\n未找到目标iframe")
    
    print("\n" + "=" * 60)
    print("调试完成，浏览器将保持打开30秒")
    print("=" * 60)
    
    await asyncio.sleep(30)
    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(debug_iframe())
