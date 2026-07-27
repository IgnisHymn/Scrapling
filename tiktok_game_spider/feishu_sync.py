"""飞书电子表格同步模块 - 支持双表格动态列匹配"""
import os
import urllib.request
import json
from datetime import datetime
from pathlib import Path


class FeishuSync:
    """飞书电子表格同步"""
    
    def __init__(self, spreadsheet_token=None):
        """初始化
        
        Args:
            spreadsheet_token: 飞书表格 token，如果不传则从配置文件读取
        """
        self.token = None
        self.sheets = None
        self.column_cache = {}  # 缓存每个 sheet 的列映射 {sheet_id: {col_name: col_index}}
        self.FEISHU_APP_ID = ''
        self.FEISHU_APP_SECRET = ''
        self.SPREADSHEET_TOKEN = spreadsheet_token
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
            # 如果没有传入 token，使用配置文件中的 other token
            if not self.SPREADSHEET_TOKEN:
                self.SPREADSHEET_TOKEN = config.get("spreadsheet_other_token", "")
        except Exception as e:
            print(f"无法读取飞书凭证配置: {e}")
    
    def _validate_config(self):
        """验证飞书配置是否完整"""
        if not self.FEISHU_APP_ID or not self.FEISHU_APP_SECRET:
            print("警告: 飞书配置不完整，请检查 config/feishu_credentials.json")
        if not self.SPREADSHEET_TOKEN:
            print("警告: 未设置 spreadsheet_token")
    
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
    
    def _get_sheet_id_by_name(self, app_name: str) -> str | None:
        """根据游戏名称动态查找对应的 Sheet ID"""
        sheets = self._get_sheets()
        for sheet in sheets:
            if sheet.get("title") == app_name:
                return sheet.get("sheetId")
        return None
    
    def _get_sheet_data(self, sheet_id, range_str=None):
        """获取 Sheet 数据"""
        token = self._get_token()
        
        if range_str:
            url = f'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.SPREADSHEET_TOKEN}/values/{sheet_id}!{range_str}'
        else:
            url = f'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{self.SPREADSHEET_TOKEN}/values/{sheet_id}'
        
        req = urllib.request.Request(
            url,
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
        """将 0-based 列索引转为 Excel 列字母"""
        result = ''
        while idx >= 0:
            result = chr(ord('A') + idx % 26) + result
            idx = idx // 26 - 1
        return result
    
    def _get_column_mapping(self, sheet_id):
        """获取飞书表格的列名到列索引的映射
        
        读取第 1 行获取列名，建立映射关系。
        
        Args:
            sheet_id: Sheet ID
            
        Returns:
            dict: {列名: 列索引(0-based)}
        """
        if sheet_id in self.column_cache:
            return self.column_cache[sheet_id]
        
        try:
            # 读取第 1 行获取列名
            header_data = self._get_sheet_data(sheet_id, 'A1:Z1')
            if not header_data or not header_data[0]:
                print(f'  警告: 无法读取 {sheet_id} 的表头')
                return {}
            
            column_map = {}
            for col_idx, col_name in enumerate(header_data[0]):
                if col_name and isinstance(col_name, str):
                    col_name = col_name.strip()
                    if col_name:
                        column_map[col_name] = col_idx
            
            self.column_cache[sheet_id] = column_map
            return column_map
            
        except Exception as e:
            print(f'  获取列映射失败: {e}')
            return {}
    
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
        
        # 从第 3 行开始查找（跳过表头）
        for i in range(2, len(sheet_data)):
            row = sheet_data[i]
            if not row or len(row) == 0 or row[0] is None:
                continue
            cell_val = str(row[0]).strip()
            if cell_val == date_str:
                return i
        
        return None
    
    def _parse_number(self, value):
        """解析数值"""
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
                return None
        
        # 处理带逗号的数值
        value = value.replace(',', '')
        
        # 处理货币符号
        value = value.replace('$', '')
        
        try:
            return float(value)
        except ValueError:
            return None
    
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
        # 查找对应的 Sheet ID
        sheet_id = self._get_sheet_id_by_name(app_name)
        if not sheet_id:
            print(f'  未找到 {app_name} 对应的 Sheet，跳过同步')
            return False
        
        try:
            # 获取列映射
            column_map = self._get_column_mapping(sheet_id)
            if not column_map:
                print(f'  无法获取 {app_name} 的列映射，跳过同步')
                return False
            
            # 合并所有数据
            all_data = {}
            all_data.update(monetization_data)
            all_data.update(dashboard_data)
            all_data['Date'] = date_str
            
            # 构建行数据（按飞书表格列顺序）
            max_col = max(column_map.values()) + 1
            row_data = [None] * max_col
            
            for field_name, value in all_data.items():
                if field_name in column_map:
                    col_idx = column_map[field_name]
                    # 数值类型转换
                    if field_name != 'Date':
                        parsed = self._parse_number(value)
                        row_data[col_idx] = parsed if parsed is not None else value
                    else:
                        row_data[col_idx] = value
            
            # 获取现有数据
            sheet_data = self._get_sheet_data(sheet_id)
            
            # 查找日期所在的行
            existing_row = self._find_date_row(sheet_data, date_str)
            
            # 计算行号（飞书 API 从 1 开始）
            if existing_row is not None:
                row_num = existing_row + 1
                print(f'  更新飞书电子表格 {app_name} 第 {row_num} 行')
                
                # 稀疏写入：只写有数据的列
                self._write_sparse_row(sheet_id, row_num, row_data)
            else:
                row_num = len(sheet_data) + 1 if sheet_data else 3
                print(f'  添加飞书电子表格 {app_name} 第 {row_num} 行')
                
                # 整行写入
                end_col = self._col_letter(max_col - 1)
                range_str = f'A{row_num}:{end_col}{row_num}'
                self._write_sheet_data(sheet_id, range_str, [row_data])
            
            print(f'  飞书电子表格同步成功')
            return True
            
        except Exception as e:
            print(f'  飞书电子表格同步失败: {e}')
            return False
    
    def _write_sparse_row(self, sheet_id, row_num, row_data):
        """稀疏写入一行数据：只写非 None 的连续列段"""
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
        
        for start_idx, end_idx in segments:
            start_col = self._col_letter(start_idx)
            end_col = self._col_letter(end_idx)
            range_str = f'{start_col}{row_num}:{end_col}{row_num}'
            values = [row_data[start_idx:end_idx + 1]]
            self._write_sheet_data(sheet_id, range_str, values)
