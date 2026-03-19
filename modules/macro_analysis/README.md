# 宏观分析模块

## 概述

宏观分析模块是投资研究系统的重要组成部分，采用 **Top-Down 分析框架**，旨在：
1. 爬虫技术获取官方媒体消息和政府文件公告
2. 宏观经济指标分析（GDP、CPI、PPI、利率等）
3. 政策解读与影响评估
4. 行业配置与风险评估
5. 趋势分析与交易信号生成
6. 分型技术分析（入市信号识别）

## 核心分析框架

### Top-Down 分析方法
```
宏观经济 → 行业配置 → 个股选择
```

### 入市信号识别
- 基于 **分型分析** 判断趋势转折
- 顶分型确认卖出信号
- 底分型确认买入信号

### 主要市场
- **中国大陆**：A股市场（上证、深证、科创、创业板）
- **可投资标的**：股票、债券、ETF、商品等


## 功能特点

### 📊 数据采集
- **政府网站爬虫**：爬取中国政府网、国务院政策文件库、各部委官网
- **监管机构爬虫**：爬取证监会、央行、银保监会等监管机构信息
- **官方媒体爬虫**：爬取新华社、人民网、央视新闻等媒体内容
- **定时调度**：支持使用 APScheduler 进行定时任务调度

### 📈 数据分析
- **情感分析**：分析文本情感倾向（积极/消极/中性）
- **政策分析**：识别政策重点、影响行业和实施时间表
- **影响评估**：评估政策对各行业和市场的影响程度
- **自动分类**：自动识别内容类型和来源类型

### 🏗️ 架构设计

```
macro_analysis/
├── __init__.py          # 模块入口
├── __main__.py         # 命令行接口
├── config.py           # 配置文件
├── database.py         # 数据库模型
├── api/                # API 接口
│   ├── __init__.py
│   └── routes.py       # 路由定义
├── crawler/            # 爬虫模块
│   ├── __init__.py
│   ├── base.py         # 爬虫基类
│   ├── government.py   # 政府网站爬虫
│   ├── media.py        # 官方媒体爬虫
│   └── scheduler.py    # 定时调度器
└── analyzer/           # 分析模块
    ├── __init__.py
    ├── policy.py       # 政策分析器
    └── sentiment.py    # 情感分析器
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行爬虫任务

#### 立即运行所有爬虫

```bash
python -m modules.macro_analysis crawler
```

#### 指定任务运行

```bash
python -m modules.macro_analysis crawler -t "中国政府网爬虫"
```

#### 详细输出

```bash
python -m modules.macro_analysis crawler -v
```

### 3. 运行文本分析

#### 分析指定文本

```bash
python -m modules.macro_analysis analyze -t "中国人民银行决定下调存款准备金率0.5个百分点"
```

### 4. 查看系统状态

```bash
python -m modules.macro_analysis status
```

## API 接口

### 基础接口

#### 健康检查

```
GET /macro-analysis/health
```

#### 获取爬虫统计信息

```
GET /macro-analysis/crawler/stats
```

#### 运行爬虫任务

```
POST /macro-analysis/crawler/tasks/中国政府网爬虫/run
```

### 数据分析接口

#### 分析文本情感

```
POST /macro-analysis/analyze/text/sentiment
Content-Type: application/json

{
  "text": "这是要分析的文本"
}
```

#### 分析文本政策

```
POST /macro-analysis/analyze/text/policy
Content-Type: application/json

{
  "title": "文章标题",
  "content": "文章内容"
}
```

### 数据查询接口

#### 获取文章列表

```
GET /macro-analysis/articles?page=1&page_size=20&source_type=government&category=政策
```

#### 获取文章详情

```
GET /macro-analysis/articles/1
```

#### 分析文章情感

```
POST /macro-analysis/articles/1/analyze-sentiment
```

## 使用示例

### 示例 1：爬取并分析政策文件

```python
from modules.macro_analysis import CrawlerManager
from modules.macro_analysis import PolicyAnalyzer, SentimentAnalyzer

# 1. 初始化管理器
manager = CrawlerManager()

# 2. 立即运行政府网站爬虫
manager.run_immediate_crawl(["中国政府网爬虫"])

# 3. 从数据库中获取文章
db = get_db_session()
articles = db.query(NewsArticle).limit(10).all()

# 4. 分析文章
policy_analyzer = PolicyAnalyzer()
sentiment_analyzer = SentimentAnalyzer()

for article in articles:
    print(f"分析: {article.title}")
    
    policy_result = policy_analyzer.analyze(article.title, article.content)
    sentiment_result = sentiment_analyzer.analyze(article.content)
    
    print(f"政策类型: {policy_result.policy_type}")
    print(f"情感倾向: {sentiment_result.sentiment_to_text(sentiment_result.overall)}")
    print("-" * 50)
```

### 示例 2：实时监听政策更新

```python
import time
from modules.macro_analysis import CrawlerManager

def monitor_policies():
    manager = CrawlerManager()
    
    while True:
        print("监控政策更新...")
        
        # 运行爬虫任务
        manager.run_immediate_crawl(["国务院政策文件库"])
        
        # 检查是否有新的重要政策
        db = get_db_session()
        recent_articles = db.query(NewsArticle)\
            .filter(NewsArticle.published_at > datetime.now() - timedelta(days=1))\
            .filter(NewsArticle.content_type == "政策")\
            .all()
        
        if recent_articles:
            print(f"发现 {len(recent_articles)} 篇新政策")
            for article in recent_articles:
                print(f"• {article.title}")
        
        time.sleep(3600)  # 每小时检查一次

if __name__ == "__main__":
    monitor_policies()
```

## 配置说明

### 爬虫配置

```python
from modules.macro_analysis.config import CrawlerConfig

# 修改默认请求超时
CrawlerConfig.DEFAULT_TIMEOUT = 60

# 添加新的用户代理
CrawlerConfig.USER_AGENTS.append('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

# 修改请求间隔
CrawlerConfig.MIN_DELAY = 2
CrawlerConfig.MAX_DELAY = 5
```

### 分析器配置

```python
from modules.macro_analysis.config import AnalyzerConfig

# 修改情感分析阈值
AnalyzerConfig.SENTIMENT_THRESHOLDS['positive'] = 0.25
AnalyzerConfig.SENTIMENT_THRESHOLDS['negative'] = -0.25

# 修改政策分析权重
AnalyzerConfig.POLICY_SCORE_WEIGHTS['sentiment'] = 0.4
AnalyzerConfig.POLICY_SCORE_WEIGHTS['context'] = 0.3
```

## 性能优化

### 1. 并行处理

```python
from concurrent.futures import ThreadPoolExecutor
from modules.macro_analysis import CrawlerManager

def parallel_crawl():
    manager = CrawlerManager()
    tasks = manager.scheduler.get_all_tasks()
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        for task in tasks:
            executor.submit(manager.run_immediate_crawl, [task.name])
```

### 2. 增量爬取

```python
from datetime import datetime, timedelta
from modules.macro_analysis import get_db_session

def incremental_crawl():
    db = get_db_session()
    
    # 获取最近一次爬取时间
    last_crawl = db.query(CrawlerLog)\
        .filter(CrawlerLog.status == 'success')\
        .order_by(CrawlerLog.started_at.desc())\
        .first()
    
    if last_crawl:
        # 只爬取更新的内容
        print(f"上次爬取时间: {last_crawl.started_at}")
    else:
        # 初始爬取
        print("首次爬取，获取所有内容")
```

## 扩展开发

### 添加新爬虫

```python
from modules.macro_analysis.crawler.base import BaseCrawler

class MyCustomCrawler(BaseCrawler):
    name = "my_custom"
    source_name = "我的自定义来源"
    source_type = "news"
    
    def get_list_urls(self, page_count: int = 1, **kwargs):
        return ["https://example.com/news"]
    
    def parse_list(self, html: str, list_url: str):
        return []
    
    def parse_detail(self, html: str, detail_url: str):
        return None
```

### 添加新分析器

```python
from modules.macro_analysis.analyzer.sentiment import SentimentAnalyzer

class MySentimentAnalyzer(SentimentAnalyzer):
    def __init__(self, config=None):
        super().__init__(config)
        
    def analyze(self, text: str):
        # 自定义分析逻辑
        return super().analyze(text)
```

## 故障排查

### 常见问题

1. **爬虫运行失败**
   - 检查网络连接
   - 检查网站是否已更新结构
   - 查看 `logs/crawler.log` 文件

2. **解析错误**
   - 检查目标网站的 HTML 结构
   - 更新对应的解析函数
   - 调试定位具体问题

3. **数据库连接错误**
   - 检查数据库配置
   - 确认数据库服务运行正常
   - 检查文件权限

## 系统架构

### 架构图

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  数据源      │────►│  爬虫模块     │────►│  数据库存储   │
└─────────────┘     └──────────────┘     └──────────────┘
                          │                     ▲
                          │                     │
                          ▼                     │
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ 用户/API     │────►│ 调度器        │────►│ 任务队列      │
└─────────────┘     └──────────────┘     └──────────────┘
                          │                     ▲
                          │                     │
                          ▼                     │
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  分析器      │────►│  数据分析引擎   │────►│  结果存储     │
└─────────────┘     └──────────────┘     └──────────────┘
```

### 核心分析流程

### 1. 宏观经济分析
```python
from modules.macro_analysis.framework.top_down import TopDownAnalyzer
from modules.macro_analysis import CrawlerManager

# 初始化分析器和爬虫
analyzer = TopDownAnalyzer()
manager = CrawlerManager()

# 运行爬虫任务
manager.run_immediate_crawl(["中国政府网爬虫", "证监会爬虫"])

# 获取宏观经济指标
indicators = analyzer.get_macro_indicators(
    start_date="2025-01-01",
    end_date="2025-03-31"
)

# 分析经济周期
cycle = analyzer.analyze_economic_cycle(indicators)
print(f"当前经济周期阶段：{cycle.value}")
```

### 2. 行业配置分析
```python
from modules.macro_analysis.framework.china_market import ChinaMarketAnalyzer

# 初始化分析器
analyzer = ChinaMarketAnalyzer()

# 获取行业数据
industry_data = analyzer.fetch_industry_data()

# 分析估值和趋势
processed_industries = analyzer.analyze_sector_valuations(industry_data)

# 生成配置建议
for sector in processed_industries[:3]:
    print(f"{sector['name']}: {sector['综合分数']:.2f}分")
```

### 3. 分型技术分析与交易信号
```python
from modules.macro_analysis.technical.fractal import FractalAnalyzer, KLine

# 模拟K线数据
test_data = [
    KLine(open=100, high=105, low=98, close=102),  # 1
    KLine(open=102, high=108, low=101, close=106), # 2
    KLine(open=106, high=110, low=104, close=105), # 3 - 顶分型中心
    KLine(open=105, high=107, low=102, close=103), # 4
    KLine(open=103, high=104, low=99, close=100),  # 5
    KLine(open=100, high=101, low=95, close=96),  # 6 - 底分型中心
    KLine(open=96, high=98, low=94, close=97),    # 7
    KLine(open=97, high=100, low=96, close=99),   # 8
]

# 初始化分析器
fractal_analyzer = FractalAnalyzer()

# 识别分型
fractals = fractal_analyzer.identify_fractals(test_data)

# 分析趋势
trend = fractal_analyzer.get_trend_direction(fractals)
print(f"趋势方向: {trend.value}")

# 生成分型交易信号
signals = fractal_analyzer.generate_trading_signals(test_data)
for signal in signals:
    print(f"{signal['type']}信号: {signal['price']:.2f} (强度: {signal['strength']:.2f})")
```

### 4. 综合策略
```python
from modules.macro_analysis.framework.top_down import TopDownStrategy
from modules.macro_analysis.framework.china_market import ChinaMarketAnalyzer
from modules.macro_analysis.technical.trend import TrendAnalysis

def create_top_down_strategy():
    """创建Top-Down投资策略"""
    strategy = TopDownStrategy(
        name="中国市场Top-Down投资策略",
        description="基于宏观分析和分型技术的完整策略",
        config={
            "cycle_analysis": True,
            "fractal_analysis": True,
            "risk_management": True,
            "asset_allocation": True
        }
    )
    
    return strategy

def run_complete_analysis():
    """运行完整的投资分析流程"""
    # 1. 宏观经济分析
    strategy = create_top_down_strategy()
    
    # 2. 获取并分析市场数据
    analyzer = ChinaMarketAnalyzer()
    market_data = analyzer.fetch_market_data()
    
    # 3. 行业配置建议
    industry_suggestions = analyzer.analyze_sector_rotation()
    
    # 4. 交易信号生成
    signals = analyzer.generate_trading_signals()
    
    # 5. 风险管理
    risk_analysis = analyzer.calculate_risk_profile()
    
    return strategy.generate_report(market_data, signals, risk_analysis)
```

## 技术架构

### 数据采集层
```
┌─────────────────────────────────────────────────────────┐
│                    数据源                                │
│  中国政府网  证监会   央行     新华社  人民网  央视新闻   │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                   爬虫框架                               │
│  政府网站爬虫  监管机构爬虫  官方媒体爬虫  定时调度器      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                   存储层                                │
│  新闻表     情感分析   政策分析   影响评估   爬虫日志    │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                   分析层                                │
│  情感分析器   政策分析器   市场影响  趋势分析  风险评估   │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                   应用层                                │
│  API接口  策略引擎  可视化  风险管理  智能推荐            │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                   用户层                                │
│  Web界面  移动端  数据分析  回测系统                     │
└─────────────────────────────────────────────────────────┘
```

### 核心分析模块
```
modules/macro_analysis/
├── framework/
│   ├── __init__.py         # 框架入口
│   ├── top_down.py         # Top-Down分析
│   └── china_market.py     # 中国市场特定
├── technical/
│   ├── __init__.py         # 技术分析入口
│   ├── fractal.py          # 分型分析
│   └── trend.py            # 趋势分析
├── crawler/
│   ├── __init__.py         # 爬虫入口
│   ├── government.py       # 政府网站爬虫
│   ├── regulator.py        # 监管机构爬虫
│   ├── media.py            # 官方媒体爬虫
│   └── scheduler.py        # 定时调度器
├── analyzer/
│   ├── __init__.py         # 分析入口
│   ├── emotion.py          # 情感分析
│   ├── policy.py           # 政策分析
│   └── impact.py           # 影响评估
└── api/
    ├── __init__.py         # API入口
    └── v1/                 # 版本控制
```

## 配置与部署

### 数据库配置
```yaml
database:
  host: "localhost"
  port: 3306
  database: "macro_analysis"
  username: "admin"
  password: "password"

  # 连接池配置
  pool_size: 5
  max_overflow: 10
  pool_recycle: 3600
```

### 爬虫配置
```yaml
crawler:
  # 并发设置
  concurrency: 5
  timeout: 30

  # 调度设置
  interval: 10  # 秒
  max_retries: 3

  # 用户代理设置
  ua_pool: [
    "Mozilla/5.0...Chrome/120.0",
    "Mozilla/5.0...Firefox/120.0",
    "Mozilla/5.0...Safari/605.1"
  ]

  # 爬虫列表
  crawlers:
    - name: "中国政府网爬虫"
      enabled: true
      interval: 3600
    - name: "证监会爬虫"
      enabled: true
      interval: 1800
    - name: "央行爬虫"
      enabled: true
      interval: 2400
```

### API服务器配置
```yaml
api:
  # 服务器设置
  host: "0.0.0.0"
  port: 5000

  # CORS设置
  cors:
    origins: ["http://localhost:3000"]
    headers: ["Content-Type", "Authorization"]

  # 缓存设置
  cache:
    enabled: true
    timeout: 300  # 秒

  # 限流设置
  rate_limit:
    enabled: true
    per_minute: 100
```

## 运行与测试

### 简单语法检查（推荐）
如果您无法安装依赖，可以先运行简单的语法检查：

```bash
python3 modules/macro_analysis/test_simple_syntax.py
```

### 安装依赖（需要pip）
```bash
pip3 install -r requirements.txt
```

### 综合测试（需要所有依赖）
```bash
python3 modules/macro_analysis/test_top_down_fractal.py
```

### 数据库初始化
```bash
python -m modules.macro_analysis.database.initialize
```

### 运行爬虫任务
```bash
python -m modules.macro_analysis.crawler.scheduler
```

### 启动API服务器
```bash
python -m modules.macro_analysis.api.server
```

### 测试分析流程
```bash
python -m modules.macro_analysis.test
```

## 性能优化

### 1. 数据库优化
- 为查询频繁的字段添加索引
- 实现分页查询
- 使用连接池管理数据库连接

### 2. 爬虫优化
- 实现增量爬虫
- 优化请求频率和重试逻辑
- 使用分布式爬虫架构

### 3. 分析优化
- 并行处理大量数据
- 使用缓存存储计算结果
- 优化NLP分析算法

## 安全与监控

### 错误处理
- 完善的异常捕获和日志记录
- 自动重试机制
- 数据验证和清洗

### 监控系统
- 运行状态监控
- 性能指标采集
- 异常预警机制

### 安全措施
- API接口认证和授权
- 数据加密传输
- 请求限制和防火墙

## 未来规划

### 短期目标（1-3个月）
1. 完善Top-Down分析框架
2. 优化分型分析算法
3. 增强情感分析准确率
4. 添加更多数据源支持

### 中期目标（3-6个月）
1. 引入机器学习预测模型
2. 实现实时数据流处理
3. 完善风险管理功能
4. 支持多语言和多市场

### 长期目标（6-12个月）
1. 构建完整的量化交易系统
2. 增强可视化和交互功能
3. 实现智能推荐系统
4. 支持高频交易和算法策略

## 许可证

本项目遵循与主项目相同的开源许可证。
