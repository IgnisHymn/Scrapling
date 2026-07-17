"""TikTok开发者平台登录模块"""
import asyncio
from playwright.async_api import Page


class TikTokLogin:
    """TikTok开发者平台自动登录
    
    TikTok登录页面元素选择器（基于data-e2e属性，最稳定）：
    - 邮箱输入框: input[data-e2e="TUXTextInput"][name="email"]
    - 密码输入框: input[data-e2e="TUXPasswordInput"][name="password"]
    - 登录按钮: button[data-e2e="TUXButton"][type="submit"]
    
    注意：登录按钮初始为disabled状态，需要等待输入完成后才会启用
    """
    
    def __init__(self, page: Page, config):
        self.page = page
        self.config = config
    
    async def login(self):
        """执行自动登录"""
        print("正在访问登录页面...")
        await self.page.goto(self.config.LOGIN_URL, wait_until="networkidle")
        await asyncio.sleep(2)
        
        # 等待登录表单加载
        await self.page.wait_for_selector('[data-e2e="Form"]', timeout=10000)
        print("登录表单已加载")
        
        # 输入邮箱（使用data-e2e属性，最稳定）
        print("正在输入登录信息...")
        email_input = self.page.locator('input[data-e2e="TUXTextInput"][name="email"]')
        await email_input.click()
        await email_input.fill(self.config.LOGIN_EMAIL)
        await asyncio.sleep(0.5)
        
        # 输入密码
        password_input = self.page.locator('input[data-e2e="TUXPasswordInput"][name="password"]')
        await password_input.click()
        await password_input.fill(self.config.LOGIN_PASSWORD)
        await asyncio.sleep(0.5)
        
        # 等待登录按钮变为可用（初始状态是disabled）
        print("等待登录按钮启用...")
        await self.page.wait_for_selector('button[type="submit"]:not([disabled])', timeout=10000)
        
        # 点击登录按钮
        print("正在登录...")
        submit_btn = self.page.locator('button[data-e2e="TUXButton"][type="submit"]')
        await submit_btn.click()
        
        # 等待页面跳转（登录成功后会跳转到portal页面）
        try:
            await self.page.wait_for_url('**/portal**', timeout=30000)
            print("登录成功！")
            return True
        except Exception as e:
            # 如果没有跳转，可能需要验证码
            current_url = self.page.url
            if "login" in current_url.lower():
                print("可能需要验证码或其他验证，请手动完成登录...")
                await self._wait_for_user_input()
                return True
            else:
                print(f"登录可能已完成，当前URL: {current_url}")
                return True
    
    async def _wait_for_user_input(self):
        """等待用户手动完成验证"""
        # 在浏览器中显示提示
        await self.page.evaluate("""
            () => {
                const div = document.createElement('div');
                div.style.cssText = 'position:fixed;top:10px;right:10px;background:#ff4757;color:white;padding:20px;border-radius:8px;z-index:99999;font-size:16px;box-shadow:0 4px 12px rgba(0,0,0,0.3);font-family:Arial,sans-serif;';
                div.innerHTML = '<strong>需要手动验证</strong><br>请完成验证后等待自动继续...';
                document.body.appendChild(div);
            }
        """)
        
        # 等待URL变化（表示登录成功）
        initial_url = self.page.url
        while self.page.url == initial_url or "login" in self.page.url.lower():
            await asyncio.sleep(1)
        
        print("检测到页面跳转，登录完成！")
    
    async def is_logged_in(self):
        """检查是否已登录"""
        try:
            # 检查URL是否包含portal
            if "portal" in self.page.url:
                return True
            # 检查是否有用户头像或其他登录标志
            user_avatar = self.page.locator("[class*='avatar'], [class*='user-icon']").first
            return await user_avatar.is_visible(timeout=3000)
        except:
            return False
