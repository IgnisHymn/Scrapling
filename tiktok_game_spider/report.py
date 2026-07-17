"""HTML报告生成器"""
from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """生成HTML分析报告"""
    
    def __init__(self, output_dir="./reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, all_data, filename=None):
        """生成HTML报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tiktok_games_report_{timestamp}.html"
        
        filepath = self.output_dir / filename
        html_content = self._build_html(all_data)
        filepath.write_text(html_content, encoding="utf-8")
        
        return filepath
    
    def _build_html(self, all_data):
        """构建HTML内容"""
        rows_html = ""
        for item in all_data:
            rows_html += f"""
            <div class="game-card">
                <h3>{self._escape(item.get('name', 'N/A'))} (ID: {self._escape(item.get('app_id', 'N/A'))})</h3>
                <div class="data-section">
                    <h4>变现数据</h4>
                    <table>
                        {self._build_dict_table(item.get('monetization', {}))}
                    </table>
                </div>
                <div class="data-section">
                    <h4>数据仪表板</h4>
                    <table>
                        {self._build_dict_table(item.get('dashboard', {}))}
                    </table>
                </div>
            </div>
            """
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok小游戏数据报告</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f0f2f5; 
            color: #333;
        }}
        .header {{ 
            background: linear-gradient(135deg, #fe2c55, #25f4ee); 
            color: white; 
            padding: 30px; 
            border-radius: 12px; 
            margin-bottom: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .header h1 {{ margin: 0 0 10px 0; font-size: 28px; }}
        .header p {{ margin: 5px 0; opacity: 0.9; }}
        .game-card {{ 
            background: white; 
            padding: 24px; 
            margin-bottom: 20px; 
            border-radius: 12px; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: transform 0.2s;
        }}
        .game-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.12); }}
        .game-card h3 {{ 
            color: #fe2c55; 
            border-bottom: 3px solid #fe2c55; 
            padding-bottom: 12px; 
            margin-top: 0;
            font-size: 20px;
        }}
        .data-section {{ margin-top: 20px; }}
        .data-section h4 {{ 
            color: #555; 
            font-size: 16px;
            margin-bottom: 12px;
            padding-left: 12px;
            border-left: 4px solid #25f4ee;
        }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            margin-top: 8px; 
        }}
        th, td {{ 
            border: 1px solid #e8e8e8; 
            padding: 12px 16px; 
            text-align: left; 
        }}
        th {{ 
            background-color: #fafafa; 
            font-weight: 600;
            color: #555;
        }}
        tr:hover {{ background-color: #f8f9fa; }}
        .raw-text {{ 
            background: #f5f5f5; 
            padding: 16px; 
            border-radius: 8px; 
            white-space: pre-wrap; 
            word-break: break-all;
            max-height: 300px;
            overflow-y: auto;
            font-size: 13px;
            line-height: 1.5;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>TikTok小游戏数据报告</h1>
        <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>数据条数: {len(all_data)} 个游戏</p>
    </div>
    {rows_html}
    <div class="footer">
        <p>报告由 TikTok Game Spider 自动生成</p>
    </div>
</body>
</html>"""
    
    def _build_dict_table(self, data_dict):
        """将字典转换为表格行"""
        if not data_dict:
            return "<tr><td>暂无数据</td></tr>"
        
        rows = ""
        for key, value in data_dict.items():
            if key == "raw_text":
                # 原始文本特殊处理
                rows += f'<tr><td colspan="2"><div class="raw-text">{self._escape(str(value))}</div></td></tr>'
            elif key == "error":
                rows += f'<tr><td><strong>错误</strong></td><td style="color: red;">{self._escape(str(value))}</td></tr>'
            else:
                rows += f'<tr><td><strong>{self._escape(str(key))}</strong></td><td>{self._escape(str(value))}</td></tr>'
        return rows
    
    def _escape(self, text):
        """HTML转义"""
        if not text:
            return ""
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
