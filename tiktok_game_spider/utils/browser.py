"""浏览器配置工具"""
import json
from pathlib import Path
from playwright.async_api import async_playwright

# 浏览器状态存储路径
STATE_DIR = Path(__file__).parent.parent / "browser_state"
STATE_FILE = STATE_DIR / "auth_state.json"


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
        
        # 尝试加载已保存的浏览器状态
        if STATE_FILE.exists():
            try:
                self.context = await self.browser.new_context(
                    storage_state=str(STATE_FILE),
                    viewport={"width": 1920, "height": 1080}
                )
                print("已加载保存的浏览器状态")
            except Exception as e:
                print(f"加载浏览器状态失败: {e}，使用新上下文")
                self.context = await self.browser.new_context(
                    viewport={"width": 1920, "height": 1080}
                )
        else:
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
        
        return self.context
    
    async def save_state(self):
        """保存浏览器状态（cookies、localStorage等）"""
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            await self.context.storage_state(path=str(STATE_FILE))
            print(f"浏览器状态已保存到: {STATE_FILE}")
        except Exception as e:
            print(f"保存浏览器状态失败: {e}")
    
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
