# 数据源接入文档

## 概述

投资研究系统支持通过 **Tushare** 和 **AKShare** 两个数据源获取真实市场数据和宏观经济数据。

- **Tushare**: 需要API Token，主要提供股票、指数等金融市场数据
- **AKShare**: 开源免费，不需要API Key，宏观数据更加丰富

## 安装依赖

```bash
# 安装Tushare
pip install tushare

# 安装AKShare
pip install akshare

# 安装测试依赖
pip install pytest
```

## 配置

### 1. 配置文件

配置文件位于 `config/data_sources.yaml`：

```yaml
global:
  enable_quality_check: true    # 启用数据质量检查
  auto_clean: true              # 自动清洗数据
  cache_dir: ./data/cache       # 缓存目录
  cache_expire_hours: 24        # 缓存过期时间
  retry_times: 3                 # 重试次数
  max_requests_per_minute: 60    # 每分钟最大请求数

tushare:
  token: ""  # 留空自动读取环境变量 TUSHARE_TOKEN
  max_requests_per_minute: 60    # 免费版限制每分钟60次

akshare:
  # 不需要API Key
  max_requests_per_minute: 120

# 数据源优先级（用于FallbackDataCollector）
priority_order:
  - tushare
  - akshare
  - mock
```

### 2. 环境变量配置（推荐）

在你的 `.bashrc`、`.zshrc` 或者 `.env` 文件中添加：

```bash
export TUSHARE_TOKEN=你的TushareToken在这里
```

获取Tushare Token：访问 https://tushare.pro/ 注册后即可获取。

## 使用方法

### 基本用法

```python
from modules.common.data_collector import create_data_collector

# 创建Tushare采集器
collector = create_data_collector('tushare')

# 创建AKShare采集器
# collector = create_data_collector('akshare')

# 获取股票日线数据
result = collector.get_stock_daily(
    symbol='000001',
    start_date='2024-01-01',
    end_date='2024-03-01',
    adjust='qfq'  # qfq前复权, hfq后复权, none不复权
)

if result.success:
    print(result.data.head())
else:
    print(f"获取失败: {result.error}")

# 获取宏观经济指标
result = collector.get_macro_indicator(
    indicator_code='cpi',
    start_date='2020-01-01',
    end_date='2024-01-01'
)

# 获取指数日线数据
result = collector.get_index_daily(
    index_code='000300',  # 沪深300
    start_date='2024-01-01',
    end_date='2024-03-01'
)

# 获取财务报表
result = collector.get_financial_report(
    symbol='000001',
    year=2023,
    report_type='annual'
)
```

### 多数据源自动回退

```python
from modules.common.data_collector import FallbackDataCollector

# 配置多个数据源，按优先级尝试
collector = FallbackDataCollector([
    {
        'source': 'tushare',
        'api_key': 'your-token',
    },
    {
        'source': 'akshare',
    }
])

# 使用方式和单个采集器完全一样
result = collector.get_stock_daily(
    '000001',
    '2024-01-01',
    '2024-03-01'
)
```

### 直接使用DataFetcher

```python
from modules.common.data_fetcher import TushareDataFetcher, AkshareDataFetcher, FetchConfig

# Tushare
config = FetchConfig(api_key='your-token')
fetcher = TushareDataFetcher(config)
df = fetcher.fetch_stock_daily('000001', '2024-01-01', '2024-03-01')

# AKShare
config = FetchConfig()
fetcher = AkshareDataFetcher(config)
df = fetcher.fetch_macro_indicator('cpi', '2020-01-01', '2024-01-01')
```

## API 参考

### DataCollector 方法

| 方法 | 说明 | 参数 |
|------|------|------|
| `get_stock_daily(symbol, start_date, end_date, adjust, use_cache)` | 获取股票日线 | symbol: 股票代码<br>start_date: 开始日期<br>end_date: 结束日期<br>adjust: 复权类型<br>use_cache: 是否使用缓存 |
| `get_stock_minute(symbol, period, use_cache)` | 获取分钟数据 | symbol: 股票代码<br>period: 周期 (1min/5min/15min/30min/60min) |
| `get_index_daily(index_code, start_date, end_date, use_cache)` | 获取指数日线 | index_code: 指数代码 |
| `get_macro_indicator(indicator_code, start_date, end_date, use_cache)` | 获取宏观指标 | indicator_code: 指标代码 |
| `get_financial_report(symbol, year, report_type, use_cache)` | 获取财务报表 | symbol: 股票代码<br>year: 年份<br>report_type: annual/quarterly |
| `batch_get_stocks(symbols, start_date, end_date)` | 批量获取股票 | symbols: 股票代码列表 |

### 支持的宏观指标

| 代码 | 指标名称 |
|------|----------|
| `gdp` | 国内生产总值 |
| `gdp_yoy` | GDP同比增长率 |
| `cpi` | 居民消费价格指数 |
| `cpi_yoy` | CPI同比 |
| `ppi` | 工业生产者出厂价格指数 |
| `ppi_yoy` | PPI同比 |
| `pmi` | 制造业采购经理指数 |
| `manufacturing_pmi` | 制造业PMI |
| `non_manufacturing_pmi` | 非制造业PMI |
| `interest_rate` | 贷款市场报价利率 (LPR) |
| `rrr` | 存款准备金率 |
| `m2` | 货币供应量M2 |
| `m2_yoy` | M2同比 |
| `social_financing` | 社会融资规模 |
| `unemployment` | 失业率 |
| `consumer_confidence` | 消费者信心指数 |
| `industrial_output` | 工业增加值 |
| `fixed_asset_investment` | 固定资产投资 |
| `retail_sales` | 社会消费品零售总额 |

### 常用指数代码

| 代码 | 指数名称 |
|------|----------|
| `000001` | 上证指数 |
| `000300` | 沪深300 |
| `399001` | 深证成指 |
| `399006` | 创业板指 |
| `000016` | 上证50 |
| `399905` | 中证500 |
| `000688` | 科创50 |

## 数据质量检查

系统内置了数据质量检查功能：

1. **完整性检查**：检查是否有空DataFrame、缺失列、缺失值
2. **异常值检测**：使用Z-score方法检测数值异常
3. **数据清洗**：自动去除重复值、填充异常值

可以在配置中关闭：

```yaml
global:
  enable_quality_check: false
  auto_clean: false
```

## 限流机制

- 每个数据源独立统计每分钟请求数
- 超过限制会自动等待到下一分钟
- 配合重试机制提高成功率

## 缓存机制

- 自动缓存获取到的数据到 `./data/cache`
- 默认过期时间24小时
- 相同请求会直接返回缓存数据，减少API调用

## 错误处理

所有方法返回 `DataResult` 对象：

```python
@dataclass
class DataResult:
    success: bool           # 是否成功
    data: Optional[pd.DataFrame]  # 数据
    error: Optional[str]   # 错误信息
    source: DataSource     # 数据源
    quality_issues: List[str]  # 数据质量问题
    cached: bool           # 是否来自缓存
```

始终检查 `result.success` 来确认是否获取成功。

## 运行测试

```bash
cd investment_research
python -m pytest tests/test_data_fetcher.py -v
```

## 对比

| 特性 | Tushare | AKShare |
|------|---------|---------|
| 需要API Key | ✓ | ✗ |
| 免费额度 | 有限 | 无限 |
| 股票数据 | 丰富 | 可用 |
| 宏观数据 | 有限 | 丰富 |
| 稳定性 | 好 | 较好 |
| 更新频率 | 高 | 高 |

**推荐用法**: 股票数据优先用Tushare，宏观数据优先用AKShare，配置FallbackDataCollector自动回退。

## 故障排除

### Q: 提示 "Tushare token not configured"
A: 在环境变量设置 `TUSHARE_TOKEN` 或者在配置文件填写 `tushare.token`

### Q: 获取数据返回空
A: 1. 检查网络连接；2. 检查代码格式是否正确；3. Tushare需要积分，检查积分是否足够

### Q: "Tushare not installed"
A: 运行 `pip install tushare`

### Q: "AKShare not installed"
A: 运行 `pip install akshare`

## 参见

- Tushare官网: https://tushare.pro/
- AKShare GitHub: https://github.com/akfamily/akshare
