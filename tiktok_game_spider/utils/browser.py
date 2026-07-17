"""浏览器配置工具"""
from playwright.async_api import async_playwright


class BrowserManager:
    """管理浏览器实例"""
    
    def __init__(self, config):
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None
    
    async def start(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.config.HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        
        return self.context
    
    async def close(self):
        """关闭浏览器"""
        if self.context:
            try:
                await self.context.close()
            except:
                pass
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
        if self.playwright:
            try:
                await self.playwright.stop()
            except:
                pass
