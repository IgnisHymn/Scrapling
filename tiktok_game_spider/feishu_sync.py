"""飞书电子表格同步模块"""
import os
import urllib.request
import json
from datetime import datetime
from pathlib import Path


class FeishuSync:
    """飞书电子表格同步"""
    
    # 飞书表格 Token（固定值）
    SPREADSHEET_TOKEN = 'GeELsuE0ohaFyitSZjMcOU4bnQc'
    
    def __init__(self):
        self.token = None
        self.sheets = None
        self._styled_sheets = set()  # 已设置日期格式的 sheet
        self.FEISHU_APP_ID = ''
        self.FEISHU_APP_SECRET = ''
        self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """从配置文件读取飞书凭证"""
        config_path = Path(__file__).parent.parent / "config" / "feishu_credentials.json"
        try:
            with open(config_path, "r", encoding="utf-8-sig") as f:
                config = json.load(f)
            self.FEISHU_APP_ID = config.get("app_id", "")
            self.FEISHU_APP_SECRET = config.get("app_secret", "")
            self.SPREADSHEET_TOKEN = config.get("spreadsheet_token", self.SPREADSHEET_TOKEN)
        except Exception as e:
            print(f"无法读取飞书凭证配置: {e}")
    
    def _validate_config(self):
        """验证飞书配置是否完整"""
        if not self.FEISHU_APP_ID or not self.FEISHU_APP_SECRET:
            print("警告: 飞书配置不完整，请检查 config/feishu_credentials.json")
    
    def _get_token(self):
        """获取飞书 Token"""
        if self.token:
            return self.token
        
        token_data = json.dumps({
            'app_id': self.FEISHU_APP_ID,
            'app_secret': self.FEISHU_APP_SECRET
        }).encode()
        
        req = urllib.request.Request(
            'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
            data=token_data,
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        
        if result.get('code') == 0:
            self.token = result['tenant_access_token']
            return self.token
        else:
            raise Exception(f'获取飞书 Token 失败: {result}')
    
    def _get_sheets(self):
        """获取 Sheet 列表"""
        if self.sheets:
            return self.sheets
        
        token = self._get_token()
        req = urllib.request.Request(
            f'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.SPREADSHEET_TOKEN}/metainfo',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        
        if result.get('code') == 0:
            self.sheets = result['data']['sheets']
            return self.sheets
        else:
            raise Exception(f'获取 Sheet 列表失败: {result}')
    
    def _get_sheet_id_by_name(self, game_name: str) -> str | None:
        """根据游戏名称动态查找对应的 Sheet ID
        
        Args:
            game_name: 游戏名称
            
        Returns:
            str: Sheet ID，未找到返回 None
        """
        sheets = self._get_sheets()
        for sheet in sheets:
            if sheet.get("title") == game_name:
                return sheet.get("sheetId")
        return None
    
    def _get_sheet_data(self, sheet_id):
        """获取 Sheet 数据"""
        token = self._get_token()
        req = urllib.request.Request(
            f'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.SPREADSHEET_TOKEN}/values/{sheet_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        
        if result.get('code') == 0:
            return result['data']['valueRange']['values']
        else:
            raise Exception(f'获取 Sheet 数据失败: {result}')
    
    def _write_sheet_data(self, sheet_id, range_str, values):
        """写入 Sheet 数据"""
        token = self._get_token()
        
        data = {
            'valueRange': {
                'range': f'{sheet_id}!{range_str}',
                'values': values
            }
        }
        
        req = urllib.request.Request(
            f'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.SPREADSHEET_TOKEN}/values',
            data=json.dumps(data).encode(),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            method='PUT'
        )
        
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        
        if result.get('code') == 0:
            return True
        else:
            raise Exception(f'写入 Sheet 数据失败: {result}')
    
    def _col_letter(self, idx):
        """将 0-based 列索引转为 Excel 列字母
        
        Args:
            idx: 列索引（0=A, 24=Y）
            
        Returns:
            str: 列字母
        """
        return chr(ord('A') + idx)
    
    def _write_sparse_row(self, sheet_id, row_num, row_data):
        """稀疏写入一行数据：只写非 None 的连续列段，跳过 None 列
        
        Args:
            sheet_id: Sheet ID
            row_num: 行号（飞书 API 从 1 开始）
            row_data: 数据列表，None 表示不写入
        """
        # 找出连续非 None 值的段
        segments = []
        seg_start = None
        
        for i, val in enumerate(row_data):
            if val is not None:
                if seg_start is None:
                    seg_start = i
            else:
                if seg_start is not None:
                    segments.append((seg_start, i - 1))
                    seg_start = None
        
        if seg_start is not None:
            segments.append((seg_start, len(row_data) - 1))
        
        if not segments:
            print(f'  跳过写入：所有列均为空')
            return
        
        # 按段写入
        for start_idx, end_idx in segments:
            start_col = self._col_letter(start_idx)
            end_col = self._col_letter(end_idx)
            range_str = f'{start_col}{row_num}:{end_col}{row_num}'
            values = [row_data[start_idx:end_idx + 1]]
            self._write_sheet_data(sheet_id, range_str, values)
    
    def _date_to_serial(self, date_str):
        """将日期字符串转换为 Excel 序列号
        
        Args:
            date_str: 日期字符串，格式为 'YYYY-MM-DD'
            
        Returns:
            int: Excel 序列号
        """
        date = datetime.strptime(date_str, '%Y-%m-%d')
        # Excel 序列号：1900-01-01 = 1
        base = datetime(1899, 12, 30)
        delta = date - base
        return delta.days
    
    def _parse_number(self, value):
        """解析数值
        
        Args:
            value: 字符串格式的数值，如 '143,127' 或 '1.7%'
            
        Returns:
            float: 数值，解析失败返回 None
        """
        if value is None:
            return None
        
        value = str(value).strip()
        
        if not value or value == 'N/A' or value == '-':
            return None
        
        # 处理百分比
        if value.endswith('%'):
            try:
                return float(value.replace('%', '')) / 100
            except ValueError:
                print(f'  警告: 无法解析百分比数值 "{value}"')
                return None
        
        # 处理带逗号的数值
        value = value.replace(',', '')
        
        # 处理货币符号
        value = value.replace('$', '')
        
        try:
            return float(value)
        except ValueError:
            print(f'  警告: 无法解析数值 "{value}"')
            return None
    
    def _parse_duration(self, value):
        """解析时长
        
        Args:
            value: 字符串格式的时长，如 '7m' 或 '2s'
            
        Returns:
            str: 时长字符串
        """
        if value is None:
            return '/'
        
        value = str(value).strip()
        
        # 如果已经是格式化的时长，直接返回
        if value.endswith('m') or value.endswith('s'):
            return value
        
        return '/'
    
    def _calculate_ipu(self, ad_impressions, active_users):
        """计算 IPU
        
        Args:
            ad_impressions: 广告曝光量
            active_users: 活跃用户 DAU
            
        Returns:
            float: IPU 值，无法计算返回 None
        """
        if active_users is None or active_users == 0 or ad_impressions is None:
            return None
        
        return ad_impressions / active_users
    
    def _find_date_row(self, sheet_data, date_str):
        """查找日期所在的行
        
        Args:
            sheet_data: Sheet 数据
            date_str: 日期字符串（YYYY-MM-DD 格式）
            
        Returns:
            int: 行号（从 0 开始），如果未找到返回 None
        """
        if not sheet_data or len(sheet_data) < 3:
            return None
        
        date_serial = self._date_to_serial(date_str)
        
        # 从第 3 行开始查找（跳过表头）
        for i in range(2, len(sheet_data)):
            row = sheet_data[i]
            if not row or row[0] is None:
                continue
            # 兼容序列号和字符串格式
            cell_val = row[0]
            if cell_val == date_serial or str(cell_val).strip() == date_str:
                return i
        
        return None
    
    def _convert_excel_data(self, date_str, monetization_data, dashboard_data):
        """将爬取数据转换为飞书电子表格格式
        
        严格按飞书电子表格表头列顺序（23列 A-W）：
        A: Date, B: 广告请求, C: 广告曝光量, D: 广告点击量, E: 广告点击率,
        F: eCPM, G: 广告收入, H: 广告支出, I: ROAS, J: IPU,
        K: 总用户数, L: 新用户数, M: 活跃用户数DAU, N: 重复用户数,
        O: 启动次数, P: 人均启动次数, Q: 每位用户的首日平均时长, R: 次均时长,
        S: 次留, T: 性别比（女/男）, U: 启动成功率, V: 首次平均启动速度, W: 平均启动速度
        
        没有数据的列填 None，_write_sparse_row 会跳过，不碰飞书表格中对应单元格。
        
        Args:
            date_str: 日期字符串
            monetization_data: 变现数据
            dashboard_data: 仪表板数据
            
        Returns:
            list: 飞书格式的数据行（23列）
        """
        ad_requests = self._parse_number(monetization_data.get('Ad requests') or monetization_data.get('广告请求'))
        ad_impressions = self._parse_number(monetization_data.get('Ad impressions') or monetization_data.get('广告曝光量'))
        ad_clicks = self._parse_number(monetization_data.get('Ad clicks') or monetization_data.get('广告点击量'))
        ad_ctr = self._parse_number(monetization_data.get('Ad click-through rate') or monetization_data.get('广告点击率'))
        ecpm = self._parse_number(monetization_data.get('eCPM') or monetization_data.get('eCPM（总）'))
        ad_revenue = self._parse_number(monetization_data.get('Ad revenue') or monetization_data.get('广告收入（总）'))
        
        total_users = self._parse_number(dashboard_data.get('Total users') or dashboard_data.get('总用户数'))
        new_users = self._parse_number(dashboard_data.get('New users') or dashboard_data.get('新用户数'))
        active_users = self._parse_number(dashboard_data.get('Active users') or dashboard_data.get('活跃用户数DAU'))
        repeat_users = self._parse_number(dashboard_data.get('Repeat users') or dashboard_data.get('重复用户数'))
        launched_sessions = self._parse_number(dashboard_data.get('Launched sessions') or dashboard_data.get('启动次数'))
        avg_sessions = self._parse_number(dashboard_data.get('Average launched sessions') or dashboard_data.get('人均启动次数'))
        avg_duration_user = self._parse_duration(dashboard_data.get('Average duration per user') or dashboard_data.get('每位用户的首日平均时长'))
        avg_duration_session = self._parse_duration(dashboard_data.get('Average duration per session') or dashboard_data.get('次均时长'))
        
        date_serial = self._date_to_serial(date_str)
        
        row_data = [
            date_serial,           # A: Date
            ad_requests,           # B: 广告请求
            ad_impressions,        # C: 广告曝光量
            ad_clicks,             # D: 广告点击量
            ad_ctr,                # E: 广告点击率
            ecpm,                  # F: eCPM
            ad_revenue,            # G: 广告收入
            None,                  # H: 广告支出
            None,                  # I: ROAS
            self._calculate_ipu(ad_impressions, active_users),  # J: IPU
            total_users,           # K: 总用户数
            new_users,             # L: 新用户数
            active_users,          # M: 活跃用户数DAU
            repeat_users,          # N: 重复用户数
            launched_sessions,     # O: 启动次数
            avg_sessions,          # P: 人均启动次数
            avg_duration_user,     # Q: 每位用户的首日平均时长
            avg_duration_session,  # R: 次均时长
            None,                  # S: 次留
            None,                  # T: 性别比（女/男）
            dashboard_data.get('启动成功率'),    # U: 启动成功率
            dashboard_data.get('首次平均启动速度'),  # V: 首次平均启动速度
            dashboard_data.get('平均启动速度'),    # W: 平均启动速度
        ]
        
        return row_data
    
    def _set_date_style(self, sheet_id):
        """设置日期列格式
        
        调用飞书样式 API，将 A 列设置为 yyyy-MM-dd 日期格式。
        只对每个 sheet 设置一次。
        
        Args:
            sheet_id: Sheet ID
        """
        if sheet_id in self._styled_sheets:
            return
        
        token = self._get_token()
        
        data = {
            'appendStyle': {
                'range': f'{sheet_id}!A3:A',
                'style': {
                    'formatter': 'yyyy-MM-dd'
                }
            }
        }
        
        req = urllib.request.Request(
            f'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.SPREADSHEET_TOKEN}/style',
            data=json.dumps(data).encode(),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            method='PUT'
        )
        
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
            
            if result.get('code') == 0:
                self._styled_sheets.add(sheet_id)
            else:
                print(f'  设置日期格式失败: {result}')
        except Exception as e:
            print(f'  设置日期格式异常: {e}')
    
    def sync_game_data(self, app_name, date_str, monetization_data, dashboard_data):
        """同步游戏数据到飞书电子表格
        
        Args:
            app_name: 游戏名称
            date_str: 日期字符串
            monetization_data: 变现数据
            dashboard_data: 仪表板数据
            
        Returns:
            bool: 是否成功
        """
        # 动态查找对应的 Sheet ID
        sheet_id = self._get_sheet_id_by_name(app_name)
        if not sheet_id:
            print(f'  未找到 {app_name} 对应的 Sheet，跳过同步')
            return False
        
        try:
            # 获取现有数据
            sheet_data = self._get_sheet_data(sheet_id)
            
            # 查找日期所在的行
            existing_row = self._find_date_row(sheet_data, date_str)
            
            # 转换数据
            row_data = self._convert_excel_data(date_str, monetization_data, dashboard_data)
            
            # 计算行号（飞书 API 从 1 开始）
            if existing_row is not None:
                row_num = existing_row + 1
                print(f'  更新飞书电子表格 {app_name} 第 {row_num} 行（稀疏模式）')
                
                # 稀疏写入：只写有数据的列，跳过 None 列
                self._write_sparse_row(sheet_id, row_num, row_data)
            else:
                row_num = len(sheet_data) + 1 if sheet_data else 3
                print(f'  添加飞书电子表格 {app_name} 第 {row_num} 行')
                
                # 新行：整行写入（A-W 共23列，匹配飞书表头）
                range_str = f'A{row_num}:W{row_num}'
                self._write_sheet_data(sheet_id, range_str, [row_data])
            
            # 设置日期列格式
            self._set_date_style(sheet_id)
            
            print(f'  飞书电子表格同步成功')
            return True
            
        except Exception as e:
            print(f'  飞书电子表格同步失败: {e}')
            return False
