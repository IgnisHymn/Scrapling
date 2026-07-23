"""爬虫配置文件"""
import os
from pathlib import Path


class SpiderConfig:
    # Excel文件路径 (UNC网络路径)
    EXCEL_PATH = r"\\192.168.110.40\胜加\自动化生产\TikTok运营端数据报表\minisInfo.xlsx"
    
    # TikTok开发者平台登录凭据
    LOGIN_EMAIL = "tlciber37@gmail.com"
    LOGIN_PASSWORD = "122334Xbt!"
    
    # 浏览器运行模式：环境变量 TIKTOK_HEADLESS=true 时使用无头模式
    HEADLESS = os.environ.get("TIKTOK_HEADLESS", "false").lower() == "true"
    SLOW_MO = 100     # 操作间隔(ms)
    
    # 输出配置
    OUTPUT_DIR = Path(__file__).parent / "output"
    REPORT_DIR = Path(__file__).parent / "reports"
    DAYS_REPORT_PATH = str(Path(__file__).parent / "output" / "DaysReports.xlsx")
    DAYS_REPORT_NETWORK_PATH = Path(r"\\192.168.110.40\胜加\自动化生产\TikTok运营端数据报表\DaysReports.xlsx")
    
    # iframe 定位器
    IFRAME_TITLE = "TikTok for Developers embedded view"
    
    # 基础URL
    BASE_URL = "https://developers.tiktok.com/portal/game"
    
    # 登录URL
    LOGIN_URL = "https://developers.tiktok.com/login"
