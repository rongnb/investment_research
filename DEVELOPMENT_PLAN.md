# 投资研究系统核心模块开发计划

## 开发目标
深度开发投资研究系统的三个核心模块：
1. 个股筛选模块 (Stock Screener) - 最高优先级
2. 回测系统 (Backtesting) - 高优先级
3. 实时数据接入 (Real-time Data) - 高优先级

## 目录结构

```
investment_research/
├── modules/
│   ├── screener/              # 个股筛选模块
│   │   ├── __init__.py
│   │   ├── factors.py         # 多因子模型
│   │   ├── technical.py       # 技术面筛选
│   │   ├── fundamental.py     # 基本面筛选
│   │   ├── strategy.py        # 自定义策略
│   │   └── ranking.py         # 评分排名
│   │
│   ├── backtest/              # 回测系统
│   │   ├── __init__.py
│   │   ├── engine.py          # 回测引擎
│   │   ├── metrics.py         # 绩效指标
│   │   ├── risk.py            # 风险分析
│   │   ├── trade.py           # 交易记录
│   │   └── report.py          # 报告生成
│   │
│   ├── data/                  # 实时数据接入
│   │   ├── __init__.py
│   │   ├── source.py          # 数据源管理
│   │   ├── realtime.py        # 实时行情
│   │   ├── fundamental.py     # 财务数据
│   │   ├── macro.py           # 宏观数据
│   │   ├── cleaning.py        # 数据清洗
│   │   └── websocket.py       # WebSocket推送
│   │
│   ├── technical/             # 技术指标库
│   │   ├── __init__.py
│   │   ├── moving_average.py  # 移动平均线
│   │   ├── macd.py            # MACD指标
│   │   ├── rsi.py             # RSI指标
│   │   ├── kdj.py             # KDJ指标
│   │   ├── bollinger.py       # 布林带
│   │   └── pattern.py         # 形态识别
│   │
│   └── common/                # 公共模块
│       ├── __init__.py
│       ├── constants.py       # 常量定义
│       ├── models.py          # 数据模型
│       ├── utils.py           # 工具函数
│       └── exceptions.py      # 异常定义
│
├── tests/                     # 测试用例
│   ├── test_screener.py
│   ├── test_backtest.py
│   ├── test_data.py
│   └── test_technical.py
│
└── notebooks/                 # 分析笔记本
    ├── screener_demo.ipynb
    ├── backtest_demo.ipynb
    └── data_analysis.ipynb

## 开发进度

### Phase 1: 基础设施 (1-2天)
- [ ] 创建完整的目录结构
- [ ] 定义数据模型和常量
- [ ] 实现基础工具函数
- [ ] 配置数据接口

### Phase 2: 个股筛选模块 (3-5天)
- [ ] 多因子选股模型
- [ ] 技术面筛选实现
- [ ] 基本面筛选实现
- [ ] 自定义策略框架
- [ ] 实时排名算法

### Phase 3: 回测系统 (3-4天)
- [ ] 回测引擎核心
- [ ] 绩效指标计算
- [ ] 风险分析模块
- [ ] 交易记录管理
- [ ] 可视化报告

### Phase 4: 实时数据接入 (2-3天)
- [ ] 多数据源管理
- [ ] 实时行情接入
- [ ] 财务数据抓取
- [ ] 数据清洗管道
- [ ] WebSocket推送

### Phase 5: 技术指标库 (2-3天)
- [ ] 移动平均线系列
- [ ] MACD指标
- [ ] RSI指标
- [ ] KDJ指标
- [ ] 布林带
- [ ] 形态识别

### Phase 6: 测试与优化 (2-3天)
- [ ] 单元测试覆盖
- [ ] 集成测试
- [ ] 性能优化
- [ ] 文档完善

## 技术依赖

```
# 核心依赖
pandas>=1.5.0
numpy>=1.23.0
scipy>=1.9.0

# 金融数据
tushare>=1.2.0
akshare>=1.9.0

# 技术分析
ta-lib>=0.4.0
pandas-ta>=0.3.0

# 数据可视化
matplotlib>=3.5.0
seaborn>=0.12.0
plotly>=5.0.0

# 机器学习
scikit-learn>=1.1.0
statsmodels>=0.13.0

# 实时数据
websocket-client>=1.4.0
aiohttp>=3.8.0

# 数据库
sqlalchemy>=1.4.0
redis>=4.3.0

# 工具
python-dotenv>=0.20.0
pydantic>=1.10.0
cachetools>=5.2.0
```

## 设计原则

1. **模块化设计**: 每个功能模块独立，低耦合高内聚
2. **配置驱动**: 通过配置文件管理参数，无需修改代码
3. **可扩展性**: 易于添加新的因子、策略、数据源
4. **高性能**: 使用pandas/numpy向量化运算，避免循环
5. **数据验证**: 严格的数据校验和清洗流程
6. **容错机制**: 完善的错误处理和日志记录

## 使用示例

```python
# 个股筛选示例
from modules.screener import StockScreener
from modules.screener.factors import FactorBuilder

screener = StockScreener()

# 构建多因子策略
factors = FactorBuilder()\
    .add_pe_ratio(max_val=30)\
    .add_pb_ratio(max_val=3)\
    .add_roe(min_val=15)\
    .add_revenue_growth(min_val=20)\
    .build()

# 执行筛选
results = screener.screen(factors)
ranked = screener.rank(results, weights={'pe': 0.2, 'pb': 0.2, 'roe': 0.3, 'growth': 0.3})

# 回测示例
from modules.backtest import BacktestEngine
from modules.backtest.strategy import StrategyBase

class MyStrategy(StrategyBase):
    def on_data(self, data):
        if self.position == 0 and data['signal'] == 1:
            self.buy(data['close'])
        elif self.position > 0 and data['signal'] == -1:
            self.sell(data['close'])

engine = BacktestEngine(initial_capital=100000)
engine.set_strategy(MyStrategy())
engine.run(data)
report = engine.generate_report()

# 实时数据示例
from modules.data import RealtimeData

data = RealtimeData()
data.subscribe(['000001.SZ', '600000.SH'])

@data.on_tick
async def handle_tick(tick):
    print(f"{tick['code']}: {tick['price']}")
```
