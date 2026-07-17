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
            
        Returns:
            str: 选择的日期字符串（YYYY-MM-DD格式），失败返回None
        """
        if target_date is None:
            target_date = datetime.now() - timedelta(days=2)
        
        target_day = target_date.day
        date_str = f"{target_date.year}-{target_date.month:02d}-{target_day:02d}"
        
        print(f"  选择日期: {date_str}")
        
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
            return date_str
            
        except Exception as e:
            print(f"  日期选择失败: {e}")
            return None
    
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
    async def get_monetization_data(self, frame: Frame):
        """从变现页面获取特定字段"""
        target_fields = [
            "Ad requests",
            "Ad impressions", 
            "Ad clicks",
            "Ad click-through rate",
            "eCPM",
            "Ad revenue"
        ]
        
        data = {}
        
        try:
            # 等待页面内容加载
            await frame.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # 获取页面文本
            body_text = await frame.locator("body").inner_text()
            
            # 从文本中解析数据（格式：字段名\n数值）
            # 只使用第一个匹配，避免匹配到描述文本
            lines = body_text.split("\n")
            for i, line in enumerate(lines):
                line = line.strip()
                for field in target_fields:
                    if field not in data and line.lower() == field.lower():
                        # 下一行是数值
                        if i + 1 < len(lines):
                            value = lines[i + 1].strip()
                            data[field] = value
                        break
            
            # 填充未找到的字段
            for field in target_fields:
                if field not in data:
                    data[field] = "N/A"
                    
        except Exception as e:
            data["error"] = str(e)
        
        return data
    
    async def get_dashboard_data(self, frame: Frame):
        """从仪表板页面获取特定字段"""
        target_fields = [
            "Total users",
            "New users",
            "Active users",
            "Repeat users",
            "Launched sessions",
            "Average launched sessions",
            "Average duration per user",
            "Average duration per session"
        ]
        
        data = {}
        
        try:
            # 等待页面内容加载
            await frame.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # 获取页面文本
            body_text = await frame.locator("body").inner_text()
            
            # 从文本中解析数据（格式：字段名\n数值）
            # 只使用第一个匹配，避免匹配到描述文本
            lines = body_text.split("\n")
            for i, line in enumerate(lines):
                line = line.strip()
                for field in target_fields:
                    if field not in data and line.lower() == field.lower():
                        # 下一行是数值
                        if i + 1 < len(lines):
                            value = lines[i + 1].strip()
                            data[field] = value
                        break
            
            # 填充未找到的字段
            for field in target_fields:
                if field not in data:
                    data[field] = "N/A"
                    
        except Exception as e:
            data["error"] = str(e)
        
        return data
    async def select_region_us(self, frame: Frame):
        """在iframe中选择United States区域"""
        try:
            # 点击Region下拉菜单（显示为"All"的combobox）
            region_select = frame.locator('span.semi-tt4d-select-selection-text:has-text("All")')
            await region_select.click()
            await asyncio.sleep(1)
            
            # 选择United States选项
            us_option = frame.locator('div.semi-tt4d-select-option-text:has-text("United States")')
            await us_option.click()
            await asyncio.sleep(2)
            
            print(f"  已切换到United States区域")
            return True
            
        except Exception as e:
            print(f"  切换区域失败: {e}")
            return False
    
    async def get_us_monetization_data(self, frame: Frame):
        """获取US区域的变现数据（eCPM和Ad revenue）"""
        target_fields = [
            "eCPM",
            "Ad revenue"
        ]
        
        data = {}
        
        try:
            # 等待页面内容加载
            await frame.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # 获取页面文本
            body_text = await frame.locator("body").inner_text()
            
            # 从文本中解析数据
            lines = body_text.split("\n")
            for i, line in enumerate(lines):
                line = line.strip()
                for field in target_fields:
                    if field not in data and line.lower() == field.lower():
                        if i + 1 < len(lines):
                            value = lines[i + 1].strip()
                            data[field] = value
                        break
            
            # 填充未找到的字段
            for field in target_fields:
                if field not in data:
                    data[field] = "N/A"
                    
        except Exception as e:
            data["error"] = str(e)
        
        return data
    
    async def click_performance_tab(self, frame: Frame):
        """点击Performance标签"""
        try:
            # 点击Performance按钮
            perf_btn = frame.locator('button[aria-label="Performance"]')
            await perf_btn.click()
            await asyncio.sleep(2)
            
            print(f"  已切换到Performance标签")
            return True
            
        except Exception as e:
            print(f"  切换Performance标签失败: {e}")
            return False
    
    async def get_performance_data(self, frame: Frame):
        """获取Performance标签的数据"""
        target_fields = [
            "Launch success rate",
            "Average first-time launch speed",
            "Average launch speed"
        ]
        
        data = {}
        
        try:
            # 等待页面内容加载
            await frame.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # 获取页面文本
            body_text = await frame.locator("body").inner_text()
            
            # 从文本中解析数据
            lines = body_text.split("\n")
            for i, line in enumerate(lines):
                line = line.strip()
                for field in target_fields:
                    if field not in data and line.lower() == field.lower():
                        if i + 1 < len(lines):
                            value = lines[i + 1].strip()
                            data[field] = value
                        break
            
            # 填充未找到的字段
            for field in target_fields:
                if field not in data:
                    data[field] = "N/A"
                    
        except Exception as e:
            data["error"] = str(e)
        
        return data
