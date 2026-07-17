"""iframe交互脚本 - 选择筛选条件并获取数据"""
import asyncio
from playwright.async_api import async_playwright


async def interactive_iframe():
    print("=" * 60)
    print("iframe交互脚本")
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
    await page.goto("https://developers.tiktok.com/portal/game/7655169914772260880/monetization?tab=iaa", wait_until="networkidle")
    await asyncio.sleep(5)
    
    # 获取目标iframe
    frames = page.frames
    target_frame = None
    for frame in frames:
        if "developers.us.tiktok.com" in frame.url:
            target_frame = frame
            break
    
    if not target_frame:
        print("未找到目标iframe")
        return
    
    print("[3] 找到目标iframe!")
    
    # 交互循环
    while True:
        print("\n" + "=" * 60)
        print("可用操作:")
        print("  1. 点击 'Users' tab")
        print("  2. 点击 'Orders' tab")
        print("  3. 选择日期范围")
        print("  4. 选择操作系统")
        print("  5. 选择区域")
        print("  6. 获取当前页面数据")
        print("  7. 获取页面HTML")
        print("  8. 打印页面文本")
        print("  0. 退出")
        
        choice = input("\n请选择操作: ").strip()
        
        if choice == "1":
            print("\n点击 'Users' tab...")
            try:
                btn = target_frame.locator('button[aria-label="Users"]')
                await btn.click()
                await asyncio.sleep(2)
                print("已切换到 Users")
            except Exception as e:
                print(f"失败: {e}")
                
        elif choice == "2":
            print("\n点击 'Orders' tab...")
            try:
                btn = target_frame.locator('button[aria-label="Orders"]')
                await btn.click()
                await asyncio.sleep(2)
                print("已切换到 Orders")
            except Exception as e:
                print(f"失败: {e}")
                
        elif choice == "3":
            print("\n选择日期范围...")
            try:
                # 找到Date range下拉菜单
                date_select = target_frame.locator('[role="combobox"]').first
                await date_select.click()
                await asyncio.sleep(1)
                
                # 显示可用选项
                options = await target_frame.locator('[role="option"]').all()
                print("可用选项:")
                for i, opt in enumerate(options):
                    text = await opt.inner_text()
                    print(f"  {i+1}. {text}")
                
                opt_choice = input("选择选项编号: ").strip()
                if opt_choice.isdigit() and 1 <= int(opt_choice) <= len(options):
                    selected_opt = options[int(opt_choice)-1]
                    opt_text = await selected_opt.inner_text()
                    await selected_opt.click()
                    await asyncio.sleep(2)
                    
                    # 如果选择的是 Custom，进入日期选择流程
                    if "custom" in opt_text.lower():
                        print("\n进入自定义日期选择...")
                        await asyncio.sleep(1)
                        
                        # 点击日期按钮打开日历
                        date_picker = target_frame.locator('.TUXDatePicker-button')
                        await date_picker.click()
                        await asyncio.sleep(1)
                        
                        # 获取可用日期
                        available_dates = await target_frame.locator(
                            '.TUXCalendar-dateButton:not([disabled])'
                        ).all()
                        
                        if not available_dates:
                            print("没有可选日期")
                        else:
                            # 显示可用日期
                            print("\n可选日期:")
                            for i, d in enumerate(available_dates):
                                date_text = await d.locator('.TUXCalendar-dateCircle').inner_text()
                                print(f"  {i+1}. {date_text}")
                            
                            # 选择开始日期
                            start_choice = input("\n选择开始日期编号: ").strip()
                            if start_choice.isdigit() and 1 <= int(start_choice) <= len(available_dates):
                                await available_dates[int(start_choice)-1].click()
                                await asyncio.sleep(1)
                                
                                # 选择结束日期
                                end_choice = input("选择结束日期编号: ").strip()
                                if end_choice.isdigit() and 1 <= int(end_choice) <= len(available_dates):
                                    await available_dates[int(end_choice)-1].click()
                                    await asyncio.sleep(1)
                                    
                                    # 点击 Confirm
                                    confirm_btn = target_frame.locator('.TUXCalendar-confirm-button')
                                    await confirm_btn.click()
                                    await asyncio.sleep(2)
                                    print("日期范围已确认")
                    else:
                        print("已选择")
            except Exception as e:
                print(f"失败: {e}")
                
        elif choice == "4":
            print("\n选择操作系统...")
            try:
                # 找到Operating system下拉菜单
                selects = await target_frame.locator('[role="combobox"]').all()
                if len(selects) >= 2:
                    await selects[1].click()
                    await asyncio.sleep(1)
                    
                    options = await target_frame.locator('[role="option"]').all()
                    print("可用选项:")
                    for i, opt in enumerate(options):
                        text = await opt.inner_text()
                        print(f"  {i+1}. {text}")
                    
                    opt_choice = input("选择选项编号: ").strip()
                    if opt_choice.isdigit() and 1 <= int(opt_choice) <= len(options):
                        await options[int(opt_choice)-1].click()
                        await asyncio.sleep(2)
                        print("已选择")
            except Exception as e:
                print(f"失败: {e}")
                
        elif choice == "5":
            print("\n选择区域...")
            try:
                selects = await target_frame.locator('[role="combobox"]').all()
                if len(selects) >= 3:
                    await selects[2].click()
                    await asyncio.sleep(1)
                    
                    options = await target_frame.locator('[role="option"]').all()
                    print("可用选项:")
                    for i, opt in enumerate(options):
                        text = await opt.inner_text()
                        print(f"  {i+1}. {text}")
                    
                    opt_choice = input("选择选项编号: ").strip()
                    if opt_choice.isdigit() and 1 <= int(opt_choice) <= len(options):
                        await options[int(opt_choice)-1].click()
                        await asyncio.sleep(2)
                        print("已选择")
            except Exception as e:
                print(f"失败: {e}")
                
        elif choice == "6":
            print("\n获取当前页面数据...")
            try:
                text = await target_frame.locator("body").inner_text()
                print(f"\n页面内容:\n{text}")
            except Exception as e:
                print(f"失败: {e}")
                
        elif choice == "7":
            print("\n获取页面HTML...")
            try:
                html = await target_frame.content()
                with open("iframe_content.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print("HTML已保存到 iframe_content.html")
            except Exception as e:
                print(f"失败: {e}")
                
        elif choice == "8":
            print("\n打印页面文本...")
            try:
                text = await target_frame.evaluate("() => document.body.innerText")
                print(f"\n{text}")
            except Exception as e:
                print(f"失败: {e}")
                
        elif choice == "0":
            print("退出")
            break
            
        else:
            print("无效选择")
    
    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(interactive_iframe())
