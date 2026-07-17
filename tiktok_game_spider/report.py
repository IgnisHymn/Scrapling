"""Excel报告保存模块"""
import openpyxl
from openpyxl.styles import Alignment, PatternFill, Font
from pathlib import Path


class ExcelSaver:
    """将爬取数据保存到Excel文件"""
    
    # 字段映射：爬取字段 -> Excel列名
    MONETIZATION_FIELDS = {
        "Ad requests": "广告请求",
        "Ad impressions": "广告曝光量",
        "Ad clicks": "广告点击量",
        "Ad click-through rate": "广告点击率",
        "eCPM": "eCPM（总）",
        "Ad revenue": "广告收入（总）"
    }
    
    DASHBOARD_FIELDS = {
        "Total users": "总用户数",
        "New users": "新用户数",
        "Active users": "活跃用户数DAU",
        "Repeat users": "重复用户数",
        "Launched sessions": "启动次数",
        "Average launched sessions": "人均启动次数",
        "Average duration per user": "每位用户的首日平均时长",
        "Average duration per session": "次均时长"
    }
    
    # 表头定义
    HEADER_ROW1 = ['Date', '营收侧', '', '', '', '', '', '', '', '', '', '', '用户侧', '', '', '', '', '', '', '', '', '', '表现侧', '', '']
    HEADER_ROW2 = [
        '', '广告请求', '广告曝光量', '广告点击量', '广告点击率', 'eCPM（总）', 'eCPM（US）', 
        '广告收入（US）', '广告收入（总）', '广告支出', 'ROAS', 'IPU', '总用户数', '新用户数', 
        '活跃用户数DAU', '重复用户数', '启动次数', '人均启动次数', '每位用户的首日平均时长', 
        '次均时长', '次留', '受众分布（性别）', '启动成功率', '首次平均启动速度', '平均启动速度'
    ]
    
    # 列映射：Excel列名 -> 列索引 (0-based)
    COLUMN_MAP = {
        "Date": 0,
        "广告请求": 1,
        "广告曝光量": 2,
        "广告点击量": 3,
        "广告点击率": 4,
        "eCPM（总）": 5,
        "eCPM（US）": 6,
        "广告收入（US）": 7,
        "广告收入（总）": 8,
        "广告支出": 9,
        "ROAS": 10,
        "IPU": 11,
        "总用户数": 12,
        "新用户数": 13,
        "活跃用户数DAU": 14,
        "重复用户数": 15,
        "启动次数": 16,
        "人均启动次数": 17,
        "每位用户的首日平均时长": 18,
        "次均时长": 19,
        "次留": 20,
        "受众分布（性别）": 21,
        "启动成功率": 22,
        "首次平均启动速度": 23,
        "平均启动速度": 24
    }
    
    def __init__(self, excel_path):
        self.excel_path = Path(excel_path)
    
    def _sanitize_sheet_name(self, name):
        """清理sheet名称，移除非法字符"""
        # Excel不允许的字符: : \ / ? * [ ]
        illegal_chars = [':', '\\', '/', '?', '*', '[', ']']
        for char in illegal_chars:
            name = name.replace(char, '_')
        # Excel sheet名称最长31个字符
        return name[:31]
    
    def save_data(self, app_name, date_str, monetization_data, dashboard_data):
        """保存数据到Excel
        
        Args:
            app_name: 应用名称（sheet页名称）
            date_str: 日期字符串（YYYY-MM-DD格式）
            monetization_data: 变现数据字典
            dashboard_data: 仪表板数据字典
        """
        # 加载或创建工作簿
        if self.excel_path.exists():
            wb = openpyxl.load_workbook(self.excel_path)
        else:
            wb = openpyxl.Workbook()
            # 删除默认sheet
            if "Sheet" in wb.sheetnames:
                del wb["Sheet"]
        
        # 获取或创建sheet（清理非法字符）
        sheet_name = self._sanitize_sheet_name(app_name)
        if sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
        else:
            ws = wb.create_sheet(title=sheet_name)
            self._init_header(ws)
        
        # 找到最后一行
        last_row = ws.max_row + 1
        
        # 构建数据行
        row_data = [''] * 25  # 25列
        
        # Date
        row_data[0] = date_str
        
        # 变现数据
        for field, value in monetization_data.items():
            if field in self.MONETIZATION_FIELDS:
                col_name = self.MONETIZATION_FIELDS[field]
                col_idx = self.COLUMN_MAP[col_name]
                row_data[col_idx] = value
            elif field in self.COLUMN_MAP:
                # 直接使用中文字段名（如 eCPM（US）, 广告收入（US））
                col_idx = self.COLUMN_MAP[field]
                row_data[col_idx] = value
        
        # 仪表板数据
        for field, value in dashboard_data.items():
            if field in self.DASHBOARD_FIELDS:
                col_name = self.DASHBOARD_FIELDS[field]
                col_idx = self.COLUMN_MAP[col_name]
                row_data[col_idx] = value
            elif field in self.COLUMN_MAP:
                # 直接使用中文字段名（如 启动成功率, 首次平均启动速度, 平均启动速度）
                col_idx = self.COLUMN_MAP[field]
                row_data[col_idx] = value
        
        # 写入数据
        for col_idx, value in enumerate(row_data, start=1):
            ws.cell(row=last_row, column=col_idx, value=value)
        
        # 保存
        wb.save(self.excel_path)
        print(f"  数据已保存到 {sheet_name} sheet 第 {last_row} 行")
    
    def _init_header(self, ws):
        """初始化表头"""
        # 写入表头
        for col_idx, value in enumerate(self.HEADER_ROW1, start=1):
            ws.cell(row=1, column=col_idx, value=value)
        for col_idx, value in enumerate(self.HEADER_ROW2, start=1):
            ws.cell(row=2, column=col_idx, value=value)
        
        # 合并单元格
        ws.merge_cells('A1:A2')       # Date
        ws.merge_cells('B1:L1')       # 营收侧
        ws.merge_cells('M1:V1')       # 用户侧
        ws.merge_cells('W1:Y1')       # 表现侧
        
        # 定义背景颜色
        fill_ys = PatternFill(start_color="E1EAFF", end_color="E1EAFF", fill_type="solid")  # 营收侧-淡蓝
        fill_yh = PatternFill(start_color="FBBFBC", end_color="FBBFBC", fill_type="solid")  # 用户侧-淡粉红
        fill_bx = PatternFill(start_color="D9F5D6", end_color="D9F5D6", fill_type="solid")  # 表现侧-淡绿
        
        # 通用的文字对齐方式
        center_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # 填充背景色
        for row_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=2, min_col=1, max_col=25), start=1):
            for col_idx, cell in enumerate(row, start=1):
                cell.alignment = center_alignment
                
                if row_idx == 1:
                    if 2 <= col_idx <= 12:    # 营收侧
                        cell.fill = fill_ys
                    elif 13 <= col_idx <= 22: # 用户侧
                        cell.fill = fill_yh
                    elif 23 <= col_idx <= 25: # 表现侧
                        cell.fill = fill_bx
                
                # 设置字体
                cell_font = Font(name="Arial", size=10, bold=True, color="1F2329")
                if cell.value:
                    if "eCPM" in str(cell.value):
                        cell_font = Font(name="Arial", size=10, bold=True, color="3370FF")
                    elif cell.value == "ROAS":
                        cell_font = Font(name="Arial", size=10, bold=True, color="2EA121")
                    elif cell.value == "IPU":
                        cell_font = Font(name="Arial", size=10, bold=True, color="F54A45")
                cell.font = cell_font
