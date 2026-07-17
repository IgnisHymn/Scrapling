"""调试iframe访问 - 自动登录版本"""
import asyncio
from playwright.async_api import async_playwright


async def debug_iframe():
    """调试iframe访问"""
    print("=" * 60)
    print("iframe访问调试（自动登录版）")
    print("=" * 60)
    
    # 登录凭据
    EMAIL = "tlciber37@gmail.com"
    PASSWORD = "122334Xbt!"
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()
    
    # 自动登录
    print("\n[步骤1] 自动登录...")
    await page.goto("https://developers.tiktok.com/login", wait_until="networkidle")
    await asyncio.sleep(2)
    
    # 填写邮箱
    email_input = page.locator('input[data-e2e="TUXTextInput"][name="email"]')
    await email_input.fill(EMAIL)
    await asyncio.sleep(0.5)
    
    # 填写密码
    password_input = page.locator('input[data-e2e="TUXPasswordInput"][name="password"]')
    await password_input.fill(PASSWORD)
    await asyncio.sleep(0.5)
    
    # 等待按钮启用并点击
    await page.wait_for_selector('button[type="submit"]:not([disabled])', timeout=10000)
    await page.locator('button[data-e2e="TUXButton"][type="submit"]').click()
    
    # 等待登录完成
    print("等待登录完成...")
    await page.wait_for_url("**/portal**", timeout=30000)
    print("登录成功！")
    
    # 访问包含iframe的页面
    print("\n[步骤2] 访问包含iframe的页面...")
    test_url = "https://developers.tiktok.com/portal/game/7655169914772260880/monetization"
    await page.goto(test_url, wait_until="networkidle")
    await asyncio.sleep(3)
    
    # 获取iframe信息
    print("\n[步骤3] 分析iframe...")
    iframes = page.frames
    print(f"页面共有 {len(iframes)} 个frame:")
    for i, frame in enumerate(iframes):
        print(f"  [{i}] name='{frame.name}', title='{frame.title}', url='{frame.url[:60]}...'")
    
    # 找到目标iframe
    iframe = page.frame(title="TikTok for Developers embedded view")
    if iframe:
        print(f"\n找到目标iframe!")
        print(f"  URL: {iframe.url}")
        
        # 尝试方法1: 通过frame对象获取内容
        print("\n[步骤4] 测试方法1: 通过frame对象获取内容")
        try:
            body_text = await iframe.locator("body").inner_text()
            print(f"  成功! 内容长度: {len(body_text)}")
            print(f"  内容预览: {body_text[:200]}...")
        except Exception as e:
            print(f"  失败: {e}")
        
        # 尝试方法2: 获取frame的HTML
        print("\n[步骤5] 测试方法2: 获取frame的HTML")
        try:
            html = await iframe.locator("body").inner_html()
            print(f"  成功! HTML长度: {len(html)}")
        except Exception as e:
            print(f"  失败: {e}")
        
        # 尝试方法3: 评估JavaScript获取内容
        print("\n[步骤6] 测试方法3: 通过JavaScript获取")
        try:
            content = await iframe.evaluate("() => document.body.innerText")
            print(f"  成功! 内容长度: {len(content)}")
            print(f"  内容预览: {content[:200]}...")
        except Exception as e:
            print(f"  失败: {e}")
    else:
        print("\n未找到目标iframe")
        print("尝试列出所有iframe的详细信息...")
        for frame in page.frames:
            print(f"\n  frame.name = '{frame.name}'")
            print(f"  frame.title = '{frame.title}'")
            print(f"  frame.url = '{frame.url}'")
    
    print("\n" + "=" * 60)
    print("调试完成，浏览器保持打开")
    print("请手动检查页面，然后关闭浏览器窗口")
    print("=" * 60)
    
    # 保持浏览器打开，让用户手动关闭
    try:
        await asyncio.sleep(300)  # 等待5分钟
    except:
        pass
    
    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(debug_iframe())
