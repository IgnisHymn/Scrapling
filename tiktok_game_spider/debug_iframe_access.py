"""调试iframe访问问题"""
import asyncio
from playwright.async_api import async_playwright


async def debug_iframe_access():
    """调试iframe访问"""
    print("=" * 60)
    print("iframe访问调试")
    print("=" * 60)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()
    
    # 先登录
    print("\n[步骤1] 请手动登录TikTok开发者平台")
    await page.goto("https://developers.tiktok.com/login")
    input("登录完成后按回车继续...")
    
    # 访问包含iframe的页面
    print("\n[步骤2] 访问包含iframe的页面")
    test_url = input("请输入包含iframe的URL: ").strip()
    if not test_url:
        test_url = "https://developers.tiktok.com/portal/game/7661875562146711560/monetization"
    
    await page.goto(test_url, wait_until="networkidle")
    await asyncio.sleep(3)
    
    # 获取iframe信息
    print("\n[步骤3] 分析iframe")
    iframe = page.frame(title="TikTok for Developers embedded view")
    if iframe:
        print(f"找到iframe!")
        print(f"  URL: {iframe.url}")
        
        # 尝试方法1: 在当前页面直接访问iframe URL
        print("\n[步骤4] 测试直接访问iframe URL")
        iframe_url = iframe.url
        print(f"  原始URL: {iframe_url}")
        
        # 修复HTML实体
        fixed_url = iframe_url.replace("&amp;", "&")
        print(f"  修复后URL: {fixed_url}")
        
        choice = input("\n是否尝试直接访问? (y/n): ").strip()
        if choice.lower() == 'y':
            await page.goto(fixed_url, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # 检查是否404
            title = await page.title()
            print(f"\n  页面标题: {title}")
            
            if "404" in title or "not found" in title.lower():
                print("  结果: 404错误")
                
                # 尝试方法2: 在新标签页打开
                print("\n[步骤5] 尝试在新标签页打开")
                new_page = await context.new_page()
                await new_page.goto(fixed_url, wait_until="networkidle")
                await asyncio.sleep(2)
                new_title = await new_page.title()
                print(f"  新标签页标题: {new_title}")
                
                if "404" in new_title:
                    print("  结果: 仍然404")
                    print("\n  可能原因:")
                    print("  1. URL需要特定的Referer头")
                    print("  2. URL有防盗链保护")
                    print("  3. 需要从iframe上下文中加载")
                else:
                    print("  结果: 成功!")
                    body_text = await new_page.locator("body").inner_text()
                    print(f"  内容: {body_text[:500]}...")
                
                await new_page.close()
            else:
                print("  结果: 成功!")
                body_text = await page.locator("body").inner_text()
                print(f"  内容: {body_text[:500]}...")
        
        # 尝试方法3: 通过frame对象访问
        print("\n[步骤6] 测试通过frame对象访问")
        iframe = page.frame(title="TikTok for Developers embedded view")
        if iframe:
            try:
                content = await iframe.content()
                print(f"  frame.content() 成功，长度: {len(content)}")
                print(f"  内容预览: {content[:300]}...")
            except Exception as e:
                print(f"  frame.content() 失败: {e}")
            
            try:
                body_text = await iframe.locator("body").inner_text()
                print(f"  frame.locator('body') 成功")
                print(f"  文本: {body_text[:300]}...")
            except Exception as e:
                print(f"  frame.locator('body') 失败: {e}")
    else:
        print("未找到iframe")
    
    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)
    
    input("\n按回车关闭浏览器...")
    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(debug_iframe_access())
