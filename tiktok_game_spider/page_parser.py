"""页面解析模块 - 处理iframe和动态id

关键发现：iframe是跨域的
- 主页面域名: developers.tiktok.com
- iframe域名: developers.us.tiktok.com

解决方案：在iframe中直接操作
"""
from datetime import datetime, timedelta
from playwright.async_api import Page, Frame


class PageParser:
    """解析TikTok开发者平台页面"""
    
    # 所有可能的字段名称（用于验证值是否是字段名称）
    ALL_FIELD_NAMES = [
        "total users", "new users", "active users", "repeat users",
        "launched sessions", "average launched sessions", 
        "average duration per user", "average duration per session",
        "ad requests", "ad impressions", "ad clicks", "ad click-through rate",
        "ecpm", "ad revenue", "launch success rate", 
        "average first-time launch speed", "average launch speed",
        "data is refreshed every day", "number of times"
    ]
    
    def __init__(self, page: Page, iframe_title: str):
        self.page = page
        self.iframe_title = iframe_title
    
    def _is_valid_value(self, value: str) -> bool:
        """验证值是否是有效的数值（不是字段名称或描述文本）"""
        if not value:
            return False
        if value.lower() in self.ALL_FIELD_NAMES:
            return False
        if "data is refreshed" in value.lower():
            return False
        if "number of times" in value.lower():
            return False
        return True
    
    async def get_target_frame(self):
        """获取目标iframe（developers.us.tiktok.com）"""
        frames = self.page.frames
        for frame in frames:
            if "developers.us.tiktok.com" in frame.url:
                return frame
        return None
    
    async def select_date_in_iframe(self, frame: Frame, target_date=None):
        """在iframe中选择日期范围"""
        if target_date is None:
            target_date = datetime.now() - timedelta(days=2)
        
        target_day = target_date.day
        date_str = f"{target_date.year}-{target_date.month:02d}-{target_day:02d}"
        
        print(f"  选择日期: {date_str}")
        
        try:
            # 1. 找到Date range下拉菜单并点击
            date_select = frame.locator('[role="combobox"]').first
            await date_select.click()
            
            # 2. 等待并选择 Custom 选项
            custom_opt = frame.locator('[role="option"]:has-text("Custom")')
            await custom_opt.wait_for(state="visible", timeout=10000)
            await custom_opt.click()
            
            # 3. 等待并点击日期按钮打开日历
            date_picker = frame.locator('.TUXDatePicker-button')
            await date_picker.wait_for(state="visible", timeout=10000)
            await date_picker.click()
            
            # 4. 等待日期按钮可用，找到目标日期
            await frame.locator('.TUXCalendar-dateButton:not([disabled])').first.wait_for(state="visible", timeout=10000)
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
                # 6. 点击结束日期（同一个日期）
                await target_btn.click()
            
            # 7. 等待并点击 Confirm
            confirm_btn = frame.locator('.TUXCalendar-confirm-button')
            await confirm_btn.wait_for(state="visible", timeout=10000)
            await confirm_btn.click()
            await frame.wait_for_load_state("networkidle")
            
            print(f"  日期选择完成")
            return date_str
            
        except Exception as e:
            print(f"  日期选择失败: {e}")
            return None
    
    async def get_data_from_iframe(self, frame: Frame):
        """从iframe中获取数据"""
        data = {}
        
        try:
            await frame.wait_for_load_state("networkidle")
            body_text = await frame.locator("body").inner_text()
            
            tables = await frame.locator("table").all()
            for table in tables:
                rows = await table.locator("tr").all()
                for row in rows:
                    cells = await row.locator("td, th").all()
                    if len(cells) >= 2:
                        key = await cells[0].inner_text()
                        value = await cells[1].inner_text()
                        data[key.strip()] = value.strip()
            
            if not data:
                data["raw_text"] = body_text[:5000]
                
        except Exception as e:
            data["error"] = str(e)
        
        return data

    async def get_fields_from_frame(self, frame: Frame, target_fields: list[str]) -> dict:
        """通用方法：从iframe中提取指定字段的数据"""
        data = {}
        
        try:
            await frame.wait_for_load_state("networkidle")
            body_text = await frame.locator("body").inner_text()
            
            lines = body_text.split("\n")
            for i, line in enumerate(lines):
                line = line.strip()
                for field in target_fields:
                    if field not in data and line.lower() == field.lower():
                        if i + 1 < len(lines):
                            value = lines[i + 1].strip()
                            if self._is_valid_value(value):
                                data[field] = value
                            else:
                                data[field] = "N/A"
                        break
            
            for field in target_fields:
                if field not in data:
                    data[field] = "N/A"
                    
        except Exception as e:
            data["error"] = str(e)
        
        return data

    async def get_monetization_data(self, frame: Frame):
        """从变现页面获取特定字段"""
        return await self.get_fields_from_frame(frame, [
            "Ad requests", "Ad impressions", "Ad clicks",
            "Ad click-through rate", "eCPM", "Ad revenue"
        ])
    
    async def get_dashboard_data(self, frame: Frame):
        """从仪表板页面获取特定字段"""
        return await self.get_fields_from_frame(frame, [
            "Total users", "New users", "Active users", "Repeat users",
            "Launched sessions", "Average launched sessions",
            "Average duration per user", "Average duration per session"
        ])

    async def get_performance_data(self, frame: Frame):
        """获取Performance标签的数据"""
        return await self.get_fields_from_frame(frame, [
            "Launch success rate", "Average first-time launch speed",
            "Average launch speed"
        ])

    async def get_us_monetization_data(self, frame: Frame):
        """获取US区域的变现数据（eCPM和Ad revenue）"""
        return await self.get_fields_from_frame(frame, [
            "eCPM", "Ad revenue"
        ])

    async def select_region_us(self, frame: Frame):
        """在iframe中选择United States区域"""
        try:
            region_select = frame.locator('span.semi-tt4d-select-selection-text:has-text("All")')
            await region_select.click()
            
            us_option = frame.locator('div.semi-tt4d-select-option-text:has-text("United States")')
            await us_option.wait_for(state="visible", timeout=10000)
            await us_option.click()
            await frame.wait_for_load_state("networkidle")
            
            print(f"  已切换到United States区域")
            return True
            
        except Exception as e:
            print(f"  切换区域失败: {e}")
            return False
    
    async def click_performance_tab(self, frame: Frame):
        """点击Performance标签"""
        try:
            perf_btn = frame.locator('button[aria-label="Performance"]')
            await perf_btn.wait_for(state="visible", timeout=10000)
            await perf_btn.click()
            await frame.wait_for_load_state("networkidle")
            
            print(f"  已切换到Performance标签")
            return True
            
        except Exception as e:
            print(f"  切换Performance标签失败: {e}")
            return False
