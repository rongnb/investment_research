# 投资研究系统架构文档

## 系统概述

投资研究系统是一个综合性的量化投资研究平台，提供数据采集、宏观分析、技术分析、策略回测等功能。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Web UI     │  │  移动APP     │  │  Jupyter    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      API接口层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  REST API   │  │  WebSocket  │  │  GraphQL    │        │
│  │  (FastAPI)  │  │             │  │  (可选)      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      业务逻辑层                             │
│  ┌──────────────┬──────────────┬──────────────┐          │
│  │  信息收集模块  │  宏观分析模块  │  技术分析模块  │          │
│  │  Data        │  Macro       │  Technical   │          │
│  │  Collection  │  Analysis    │  Indicators  │          │
│  ├──────────────┼──────────────┼──────────────┤          │
│  │  研报分析模块  │  决策优化模块  │  回测引擎模块  │          │
│  │  Research    │  Decision    │  Backtest    │          │
│  │  Analysis    │  Optimization│  Engine      │          │
│  ├──────────────┴──────────────┴──────────────┤          │
│  │           筛选器和估值模块                    │          │
│  │           Screener & Estimation             │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  PostgreSQL │  │    Redis    │  │ Elasticsearch│        │
│  │  (主要DB)    │  │   (缓存)     │  │  (日志/搜索)  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      外部数据源                             │
│  ┌──────────┬──────────┬──────────┬──────────┐              │
│  │ Tushare  │ AKShare  │东方财富  │  本地CSV  │              │
│  └──────────┴──────────┴──────────┴──────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## 模块详解

### 1. 信息收集模块 (modules/common/data_collector.py)

**功能**: 统一的数据采集接口

**核心类**:
- `DataCollector` - 统一入口，自动缓存
- `BaseDataFetcher` - 数据采集器基类
- `MockDataFetcher` - 模拟数据采集器
- `DataCache` - 缓存管理器

**支持数据源**:
- Mock (模拟数据)
- Tushare (待实现)
- AKShare (待实现)
- 东方财富 (待实现)

**API**:
```python
collector = DataCollector.create_data_collector("mock")
df = collector.get_stock_daily("000001", "2024-01-01", "2024-12-31")
```

### 2. 宏观分析模块 (modules/macro/)

**文件**:
- `analyzer.py` - 原有宏观经济分析器
- `cycle.py` - 经济周期分析器 [新增]
- `scenario.py` - 情景分析器 [新增]
- `policy.py` - 政策评估器 [新增]
- `indicators.py` - 经济指标管理

**核心功能**:

**周期分析器** (`EconomicCycleAnalyzer`):
- 基于多指标（PMI、GDP、失业率、CPI等）综合评分
- 判断周期阶段（复苏/扩张/顶峰/收缩/低谷）
- 计算置信度
- 生成投资建议

**情景分析器** (`ScenarioAnalyzer`):
- 生成基准/乐观/悲观三种情景
- 计算概率加权收益
- 推荐资产配置比例
- 风险评分

**政策评估器** (`PolicyAnalyzer`):
- 货币政策分析（利率、货币供应量）
- 财政政策分析（基建、投资）
- 产业政策分析
- 行业影响评分
- 资产配置建议

**使用示例**:
```python
from modules.macro import EconomicCycleAnalyzer, create_default_indicators

# 周期分析
analyzer = EconomicCycleAnalyzer()
indicators = create_default_indicators()
analysis = analyzer.analyze(indicators)

print(f"当前周期: {analysis.current_cycle.value}")
print(f"置信度: {analysis.confidence:.2%}")
print(f"建议: {analysis.recommendations}")
```

### 3. 技术分析模块 (modules/technical/)

**已有模块**:
- `moving_average.py` - 移动平均线
- `macd.py` - MACD指标
- `rsi.py` - RSI指标
- `kdj.py` - KDJ指标
- `bollinger.py` - 布林带
- `pattern.py` - 形态识别
- `fractal.py` - 分型指标 [新增]

**分型指标** (`FractalIndicator`):
- 顶分型识别（Bearish Fractal）
- 底分型识别（Bullish Fractal）
- 交易信号生成
- 灵活的分型周期设置

**使用示例**:
```python
from modules.technical import calculate_fractal, fractal_top_signal

# 计算分型指标
result = calculate_fractal(df, period=5)

# 获取顶分型信号
top_signals = fractal_top_signal(df)
```

### 4. 数据库模块 (database/)

**文件**:
- `models.py` - 数据模型定义
- `session.py` - 会话管理

**数据表**:
- `stocks` - 股票基本信息
- `stock_prices` - 股票价格数据
- `macro_indicators` - 宏观经济指标
- `strategies` - 策略定义
- `backtest_results` - 回测结果

**使用示例**:
```python
from database import get_db_session, get_stock_by_symbol

# 使用上下文管理器
with get_db_session() as db:
    stock = get_stock_by_symbol(db, "000001")
    print(stock.name)
```

### 5. API接口层 (api/)

**文件**:
- `models.py` - API数据模型
- `routes.py` - API路由定义

**端点**:

**系统状态**:
- `GET /` - API根路径
- `GET /health` - 健康检查
- `GET /api/v1/system/status` - 系统状态

**股票数据**:
- `GET /api/v1/stocks/{symbol}/price` - 股票价格

**宏观数据**:
- `GET /api/v1/macro/indicators` - 宏观指标
- `POST /api/v1/macro/cycle/analysis` - 周期分析

**技术分析**:
- `POST /api/v1/technical/indicators` - 技术指标

**回测**:
- `POST /api/v1/backtest` - 运行回测

**筛选器**:
- `POST /api/v1/screener` - 股票筛选

**启动API服务**:
```bash
cd investment_research
python -m api.routes
```

## 目录结构总览

```
investment_research/
├── api/                          # API接口层
│   ├── __init__.py
│   ├── models.py                 # API数据模型
│   └── routes.py                 # API路由
├── database/                     # 数据库模块
│   ├── __init__.py
│   ├── models.py                 # 数据模型定义
│   └── session.py                # 会话管理
├── modules/                      # 业务逻辑模块
│   ├── __init__.py
│   ├── common/                   # 通用模块
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── data_collector.py     # 数据采集器 [新增]
│   │   ├── exceptions.py
│   │   ├── models.py
│   │   └── utils.py
│   ├── macro/                    # 宏观分析模块
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   ├── cycle.py              # 周期分析 [新增]
│   │   ├── indicators.py
│   │   ├── policy.py             # 政策评估 [新增]
│   │   └── scenario.py           # 情景分析 [新增]
│   ├── technical/                # 技术分析模块
│   │   ├── __init__.py
│   │   ├── bollinger.py
│   │   ├── fractal.py            # 分型指标 [新增]
│   │   ├── kdj.py
│   │   ├── macd.py
│   │   ├── moving_average.py
│   │   ├── pattern.py
│   │   └── rsi.py
│   ├── backtest/                 # 回测模块
│   ├── decision/                 # 决策模块
│   ├── estimation/               # 估值模块
│   ├── research/                 # 研报分析模块
│   └── screener/                 # 筛选器模块
├── docs/                         # 文档
│   └── ARCHITECTURE.md           # 架构文档
├── main.py                       # 主入口
└── requirements.txt              # 依赖包
```

## 下一步工作

### 1. 完善现有功能
- [ ] 连接真实数据源（Tushare/AKShare）
- [ ] 完善技术指标计算
- [ ] 完善回测引擎
- [ ] 添加更多策略模板

### 2. 前端界面
- [ ] Web UI 设计
- [ ] 数据可视化
- [ ] 策略编辑器
- [ ] 回测结果展示

### 3. 部署运维
- [ ] Docker 容器化
- [ ] CI/CD 流程
- [ ] 监控告警
- [ ] 日志管理

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库
cd investment_research
python -c "from database import init_db; init_db()"

# 3. 启动API服务
python -m api.routes

# 4. 访问文档
# 打开浏览器访问: http://localhost:8000/docs
```

---

**当前状态**: Phase 1 (信息收集与宏观分析) 已完成核心功能开发

**已完成模块**:
- ✅ 数据采集模块 (data_collector.py)
- ✅ 经济周期分析 (cycle.py)
- ✅ 宏观情景分析 (scenario.py)
- ✅ 政策影响评估 (policy.py)
- ✅ 分型指标 (fractal.py)
- ✅ 数据库模型 (models.py)
- ✅ API接口层 (routes.py)
