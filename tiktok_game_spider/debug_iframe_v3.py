"""调试iframe访问 - 处理登录跳转"""
import asyncio
from playwright.async_api import async_playwright


async def debug_iframe():
    """调试iframe访问"""
    print("=" * 60)
    print("iframe访问调试")
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
    
    email_input = page.locator('input[data-e2e="TUXTextInput"][name="email"]')
    await email_input.fill(EMAIL)
    await asyncio.sleep(0.5)
    
    password_input = page.locator('input[data-e2e="TUXPasswordInput"][name="password"]')
    await password_input.fill(PASSWORD)
    await asyncio.sleep(0.5)
    
    await page.wait_for_selector('button[type="submit"]:not([disabled])', timeout=10000)
    await page.locator('button[data-e2e="TUXButton"][type="submit"]').click()
    
    # 等待页面跳转（不指定URL）
    print("等待登录完成...")
    await asyncio.sleep(5)
    
    current_url = page.url
    print(f"登录后URL: {current_url}")
    
    # 检查是否需要验证码
    if "login" in current_url.lower():
        print("\n可能需要验证码，请手动完成验证...")
        input("验证完成后按回车继续...")
    
    # 访问目标页面
    print("\n[步骤2] 访问目标页面...")
    test_url = "https://developers.tiktok.com/portal/game/7655169914772260880/monetization"
    await page.goto(test_url, wait_until="networkidle")
    await asyncio.sleep(5)
    
    print(f"当前URL: {page.url}")
    
    # 分析iframe
    print("\n[步骤3] 分析iframe...")
    iframes = page.frames
    print(f"页面共有 {len(iframes)} 个frame:")
    for i, frame in enumerate(iframes):
        print(f"  [{i}] name='{frame.name}', title='{frame.title}'")
        print(f"       url='{frame.url[:80]}...'")
    
    # 找到目标iframe
    iframe = page.frame(title="TikTok for Developers embedded view")
    if iframe:
        print(f"\n找到目标iframe!")
        
        # 测试方法1
        print("\n[测试1] iframe.locator('body').inner_text()")
        try:
            text = await iframe.locator("body").inner_text()
            print(f"  成功! 长度: {len(text)}")
            print(f"  预览: {text[:200]}")
        except Exception as e:
            print(f"  失败: {e}")
        
        # 测试方法2
        print("\n[测试2] iframe.evaluate('() => document.body.innerText')")
        try:
            text = await iframe.evaluate("() => document.body.innerText")
            print(f"  成功! 长度: {len(text)}")
            print(f"  预览: {text[:200]}")
        except Exception as e:
            print(f"  失败: {e}")
        
        # 测试方法3
        print("\n[测试3] iframe.content()")
        try:
            html = await iframe.content()
            print(f"  成功! 长度: {len(html)}")
        except Exception as e:
            print(f"  失败: {e}")
    else:
        print("\n未找到iframe，尝试获取页面内容...")
        body_text = await page.locator("body").inner_text()
        print(f"页面文本: {body_text[:500]}")
    
    print("\n" + "=" * 60)
    print("调试完成，浏览器将保持打开30秒")
    print("=" * 60)
    
    await asyncio.sleep(30)
    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(debug_iframe())
