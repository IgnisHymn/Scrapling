"""页面解析模块 - 直接在主页面上操作"""
from datetime import datetime, timedelta
from playwright.async_api import Page


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
    
    def __init__(self, page: Page):
        self.page = page
    
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
    
    async def select_date(self, target_date=None):
        """选择日期范围"""
        if target_date is None:
            target_date = datetime.now() - timedelta(days=2)
        
        target_day = target_date.day
        date_str = f"{target_date.year}-{target_date.month:02d}-{target_day:02d}"
        
        print(f"  选择日期: {date_str}")
        
        try:
            # 1. 找到Date range下拉菜单并点击
            date_select = self.page.locator('div[role="combobox"]:has(span:has-text("Date range"))')
            await date_select.click()
            
            # 2. 等待并选择 Custom 选项
            custom_opt = self.page.locator('[role="option"]:has-text("Custom")')
            await custom_opt.wait_for(state="visible", timeout=10000)
            await custom_opt.click()
            
            # 3. 等待并点击日期按钮打开日历
            date_picker = self.page.locator('.TUXDatePicker-button')
            await date_picker.wait_for(state="visible", timeout=10000)
            await date_picker.click()
            
            # 4. 等待日期按钮可用，找到目标日期
            await self.page.locator('.TUXCalendar-dateButton:not([disabled])').first.wait_for(state="visible", timeout=10000)
            available_dates = await self.page.locator(
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
            confirm_btn = self.page.locator('.TUXCalendar-confirm-button')
            await confirm_btn.wait_for(state="visible", timeout=10000)
            await confirm_btn.click()
            await self.page.wait_for_load_state("networkidle")
            
            print(f"  日期选择完成")
            return date_str
            
        except Exception as e:
            print(f"  日期选择失败: {e}")
            return None
    
    async def get_fields(self, target_fields: list[str]) -> dict:
        """通用方法：从页面中提取指定字段的数据"""
        data = {}
        
        try:
            # 等待页面完全加载
            await self.page.wait_for_load_state("networkidle")
            # 额外等待，确保 JavaScript 渲染的数据加载完成
            import asyncio
            await asyncio.sleep(4)
            
            # 尝试多次读取数据，直到获取到有效数据
            max_retries = 3
            for retry in range(max_retries):
                body_text = await self.page.locator("body").inner_text()
                
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
                
                # 检查是否所有字段都有数据
                all_fields_found = all(field in data for field in target_fields)
                if all_fields_found:
                    break
                
                # 如果还有字段没找到，等待后重试
                if retry < max_retries - 1:
                    print(f"    数据加载中，等待重试 ({retry + 1}/{max_retries})...")
                    await asyncio.sleep(2)
            
            for field in target_fields:
                if field not in data:
                    data[field] = "N/A"
                    
        except Exception as e:
            data["error"] = str(e)
        
        return data

    async def get_monetization_data(self):
        """从变现页面获取特定字段"""
        return await self.get_fields([
            "Ad requests", "Ad impressions", "Ad clicks",
            "Ad click-through rate", "eCPM", "Ad revenue"
        ])
    
    async def get_dashboard_data(self):
        """从仪表板页面获取特定字段"""
        return await self.get_fields([
            "Total users", "New users", "Active users", "Repeat users",
            "Launched sessions", "Average launched sessions",
            "Average duration per user", "Average duration per session"
        ])

    async def get_performance_data(self):
        """获取Performance标签的数据"""
        return await self.get_fields([
            "Launch success rate", "Average first-time launch speed",
            "Average launch speed"
        ])

    async def select_region_us(self):
        """选择United States区域"""
        try:
            region_select = self.page.locator('div[role="combobox"][aria-haspopup="dialog"]:has(span:has-text("Rest of the world"))')
            await region_select.click()
            
            us_option = self.page.locator('li[role="menuitem"]:has(span:has-text("United States"))')
            await us_option.wait_for(state="visible", timeout=10000)
            await us_option.click()
            await self.page.wait_for_load_state("networkidle")
            
            print(f"  已切换到United States区域")
            return True
            
        except Exception as e:
            print(f"  切换区域失败: {e}")
            return False
    
    async def click_performance_tab(self):
        """点击Performance标签"""
        try:
            perf_btn = self.page.locator('button[aria-label="Performance"]')
            await perf_btn.wait_for(state="visible", timeout=10000)
            await perf_btn.click()
            await self.page.wait_for_load_state("networkidle")
            
            print(f"  已切换到Performance标签")
            return True
            
        except Exception as e:
            print(f"  切换Performance标签失败: {e}")
            return False
