"""页面解析模块 - 处理iframe和动态id

关键发现：iframe是跨域的
- 主页面域名: developers.tiktok.com
- iframe域名: developers.us.tiktok.com

解决方案：在iframe中直接操作
"""
import asyncio
from datetime import datetime, timedelta
from playwright.async_api import Page, Frame


class PageParser:
    """解析TikTok开发者平台页面"""
    
    def __init__(self, page: Page, iframe_title: str):
        self.page = page
        self.iframe_title = iframe_title
    
    async def get_target_frame(self):
        """获取目标iframe（developers.us.tiktok.com）"""
        frames = self.page.frames
        for frame in frames:
            if "developers.us.tiktok.com" in frame.url:
                return frame
        return None
    
    async def select_date_in_iframe(self, frame: Frame, target_date=None):
        """在iframe中选择日期范围
        
        Args:
            frame: 目标iframe
            target_date: 目标日期，默认为前天
        """
        if target_date is None:
            target_date = datetime.now() - timedelta(days=2)
        
        target_day = target_date.day
        
        print(f"  选择日期: {target_date.year}-{target_date.month:02d}-{target_day}")
        
        try:
            # 1. 找到Date range下拉菜单
            date_select = frame.locator('[role="combobox"]').first
            await date_select.click()
            await asyncio.sleep(1)
            
            # 2. 选择 Custom 选项
            custom_opt = frame.locator('[role="option"]:has-text("Custom")')
            await custom_opt.click()
            await asyncio.sleep(2)
            
            # 3. 点击日期按钮打开日历
            date_picker = frame.locator('.TUXDatePicker-button')
            await date_picker.click()
            await asyncio.sleep(1)
            
            # 4. 找到目标日期按钮
            available_dates = await frame.locator(
                '.TUXCalendar-dateButton:not([disabled])'
            ).all()
            
            target_btn = None
            for date_btn in available_dates:
                date_text = await date_btn.locator('.TUXCalendar-dateCircle').inner_text()
                if date_text == str(target_day):
                    target_btn = date_btn
                    break
            
            if target_btn:
                # 5. 点击开始日期
                await target_btn.click()
                await asyncio.sleep(1)
                
                # 6. 点击结束日期（同一个日期）
                await target_btn.click()
                await asyncio.sleep(1)
            
            # 7. 点击 Confirm
            confirm_btn = frame.locator('.TUXCalendar-confirm-button')
            await confirm_btn.click()
            await asyncio.sleep(2)
            
            print(f"  日期选择完成")
            return True
            
        except Exception as e:
            print(f"  日期选择失败: {e}")
            return False
    
    async def get_data_from_iframe(self, frame: Frame):
        """从iframe中获取数据"""
        data = {}
        
        try:
            # 等待页面内容加载
            await frame.wait_for_load_state("networkidle")
            
            # 获取所有文本内容
            body_text = await frame.locator("body").inner_text()
            
            # 尝试提取关键数据
            tables = await frame.locator("table").all()
            for table in tables:
                rows = await table.locator("tr").all()
                for row in rows:
                    cells = await row.locator("td, th").all()
                    if len(cells) >= 2:
                        key = await cells[0].inner_text()
                        value = await cells[1].inner_text()
                        data[key.strip()] = value.strip()
            
            # 如果没有提取到结构化数据，保存原始文本
            if not data:
                data["raw_text"] = body_text[:5000]
                
        except Exception as e:
            data["error"] = str(e)
        
        return data
