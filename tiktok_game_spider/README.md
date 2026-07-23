# TikTok小游戏数据爬虫

基于 Playwright 实现的 TikTok 开发者平台小游戏数据爬虫。

## 功能特点

- 自动读取 Excel 配置文件获取小游戏列表
- 复用 Chrome 浏览器登录态，无需重复登录
- 处理 iframe 内嵌页面数据提取
- 生成 HTML 格式的分析报告
- 支持定时任务自动运行

## 目录结构

```
tiktok_game_spider/
├── main.py             # 主入口
├── config.py           # 配置文件
├── excel_reader.py     # Excel读取模块
├── page_parser.py      # 页面解析模块
├── report.py           # HTML报告生成器
├── debug.py            # 调试工具
├── run_spider.bat      # Windows定时任务批处理
├── requirements.txt    # 依赖列表
├── utils/
│   └── browser.py      # 浏览器配置工具
├── output/             # 原始数据输出目录
└── reports/            # HTML报告输出目录
```

## 使用方法

### 1. 配置

编辑 `config.py` 文件：

```python
# Excel文件路径
EXCEL_PATH = r"\\192.168.110.40\胜加\自动化生产\TikTok运营端数据报表\minisInfo.xlsx"

# Chrome浏览器配置文件路径
CHROME_USER_DATA_DIR = r"C:\Users\你的用户名\AppData\Local\Google\Chrome\User Data"

# 浏览器运行模式（定时任务时设为True）
HEADLESS = False
```

### 2. Excel文件格式

Excel文件需要包含两个Sheet：

| Sheet | 名称 | 内容 |
|-------|------|------|
| Sheet1 | AppInfos | A列: 游戏名称, B列: app_id |
| Sheet2 | Link | A1: 基础URL |

### 3. 运行

#### 调试模式（首次使用推荐）

```bash
python debug.py
```

输入 app_id 后，程序会打开浏览器并输出页面结构，帮助分析数据提取方式。

#### 正常运行

```bash
python main.py
```

#### 定时任务

1. 双击运行 `run_spider.bat`
2. 或在 Windows 任务计划程序中配置定时执行

## 技术说明

### 处理 iframe

页面内容在 `<iframe title="TikTok for Developers embedded view">` 中，使用以下方式获取：

```python
frame = page.frame(title="TikTok for Developers embedded view")
```

### 处理动态 id

不依赖元素 id，使用以下稳定的选择器：

- CSS class: `.class-name`
- 文本内容: `text='固定文本'`
- 相对路径: `//div[@class='parent']//span`
- 表格结构: `table tbody tr:first-child`

## 注意事项

1. 首次运行前，请确保已在 Chrome 中登录 TikTok 开发者平台
2. 运行时请关闭其他 Chrome 窗口，避免配置文件冲突
3. 如果遇到跨域问题，可能需要调整浏览器启动参数
