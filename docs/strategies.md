# 策略库文档

## 概述

本策略库提供多种经典和高级交易策略的实现,适用于量化投资研究系统。

## 架构

```
modules/strategy/
├── base.py          # 策略基类和接口定义
├── manager.py       # 策略管理器和工厂
├── classic/         # 经典策略
│   ├── moving_average_crossover.py
│   ├── macd_strategy.py
│   ├── rsi_strategy.py
│   ├── bollinger_strategy.py
│   ├── breakout_strategy.py
│   ├── mean_reversion.py
│   └── momentum.py
├── advanced/        # 高级策略
│   ├── multi_factor.py
│   ├── style_rotation.py
│   ├── sector_rotation.py
│   └── market_neutral.py
└── portfolio/       # 组合策略
    ├── risk_parity.py
    ├── maximum_diversification.py
    ├── target_risk.py
    └── smart_beta.py
```

## 基类

### Strategy (抽象基类)

所有策略的基类,定义以下接口:

- `initialize()`: 初始化策略
- `generate_signals(data)`: 生成交易信号
- `calculate_indicators(data)`: 计算技术指标
- `validate_data(data)`: 验证数据有效性

### SingleAssetStrategy

适用于单一交易标的的策略

### MultiAssetStrategy

适用于需要处理多个交易标的的策略

### PortfolioStrategy

适用于管理多个仓位的组合策略

## 信号类型

```python
from modules.strategy.base import SignalType

SignalType.BUY       # 买入信号
SignalType.SELL      # 卖出信号
SignalType.HOLD      # 持有/观望
SignalType.CLOSE_LONG   # 平多仓
SignalType.CLOSE_SHORT  # 平空仓
```

## 经典策略

### 1. 双均线策略 (MovingAverageCrossoverStrategy)

**原理**: 短期均线上穿长期均线时买入,下穿时卖出

**参数**:
- `short_period`: 短期均线周期 (默认20)
- `long_period`: 长期均线周期 (默认50)
- `ma_type`: 均线类型 (sma/ema/wma)

**示例**:
```python
config = StrategyConfig(
    name='MA_Crossover',
    symbol='000001.SZ',
    params={'short_period': 10, 'long_period': 30, 'ma_type': 'sma'}
)
strategy = MovingAverageCrossoverStrategy(config)
signals = strategy.generate_signals(data)
```

### 2. MACD策略 (MACDStrategy)

**原理**: MACD线与信号线交叉产生信号

**参数**:
- `fast_period`: 快速EMA周期 (默认12)
- `slow_period`: 慢速EMA周期 (默认26)
- `signal_period`: 信号线周期 (默认9)

### 3. RSI策略 (RSIStrategy)

**原理**: RSI超卖时买入,超买时卖出

**参数**:
- `period`: RSI计算周期 (默认14)
- `overbought`: 超买阈值 (默认70)
- `oversold`: 超卖阈值 (默认30)

### 4. 布林带策略 (BollingerBandsStrategy)

**原理**: 价格触及布林带上下轨时产生信号

**参数**:
- `period`: 均线周期 (默认20)
- `std_dev`: 标准差倍数 (默认2)

### 5. 突破策略 (BreakoutStrategy)

**原理**: 价格突破N日高点买入,跌破N日低点卖出

**参数**:
- `lookback_period`: 回溯周期 (默认20)
- `use_closing`: 是否使用收盘价突破 (默认True)

### 6. 均值回归策略 (MeanReversionStrategy)

**原理**: 价格偏离均值超过阈值后回归时产生信号

**参数**:
- `period`: 均值计算周期 (默认20)
- `std_threshold`: 标准差阈值 (默认2)
- `exit_threshold`: 退出阈值 (默认0.5)

### 7. 动量策略 (ClassicMomentumStrategy)

**原理**: 趋势延续性,过去表现好的资产未来继续表现好

**参数**:
- `lookback_period`: 回溯周期 (默认60)
- `holding_period`: 持仓周期 (默认20)

## 高级策略

### 1. 多因子策略 (MultiFactorStrategy)

**原理**: 结合多个因子(价值、动量、质量)进行选股

**参数**:
- `factors`: 因子列表
- `factor_weights`: 因子权重
- `rebalance_period`: 调仓周期
- `top_n`: 选取股票数量

### 2. 风格轮动策略 (StyleRotationStrategy)

**原理**: 在不同市场风格(成长/价值/大小盘)之间轮动

**参数**:
- `styles`: 轮动的风格列表
- `momentum_period`: 动量计算周期
- `lookback_period`: 回溯周期

### 3. 行业轮动策略 (SectorRotationStrategy)

**原理**: 基于动量或估值在不同行业之间轮动

**参数**:
- `sectors`: 行业列表
- `rotation_method`: 轮动方法 (momentum/value/cycle)
- `top_n`: 选取行业数量

### 4. 市场中性策略 (MarketNeutralStrategy)

**原理**: 同时持有多头和空头,对冲市场风险

**参数**:
- `long_short_ratio`: 多空比例
- `hedge_ratio`: 对冲比率

## 组合策略

### 1. 风险平价策略 (RiskParityStrategy)

**原理**: 每个资产对组合风险的贡献相等

**参数**:
- `target_volatility`: 目标波动率
- `lookback_period`: 回溯周期
- `min_weight/max_weight`: 权重约束

### 2. 最大分散化策略 (MaximumDiversificationStrategy)

**原理**: 最大化组合的分散化比率

**参数**:
- `min_weight/max_weight`: 权重约束
- `target_volatility`: 目标波动率

### 3. 目标风险策略 (TargetRiskStrategy)

**原理**: 动态调整资产权重以维持目标风险水平

**参数**:
- `target_volatility`: 目标年化波动率
- `lookback_period`: 回溯周期
- `volatility_adjustment`: 波动率调整系数

### 4. 智能贝塔策略 (SmartBetaStrategy)

**原理**: 基于因子暴露的增强型指数策略

**参数**:
- `factors`: 因子列表
- `factor_exposure`: 目标因子暴露
- `min_weight/max_weight`: 权重约束

## 策略管理器

### StrategyManager

```python
from modules.strategy.manager import StrategyManager
from modules.strategy.base import StrategyConfig

# 创建管理器
manager = StrategyManager(initial_capital=1000000)

# 添加策略
config = StrategyConfig(
    name='MA_Crossover',
    symbol='000001.SZ',
    params={'short_period': 10, 'long_period': 30}
)
manager.add_strategy('MA_Crossover', config)

# 运行策略
signals = manager.run_strategy('MA_Crossover', data)

# 运行所有策略
all_signals = manager.run_all(data)
```

### 参数优化

```python
# 参数优化
param_grid = {
    'short_period': [10, 20, 30],
    'long_period': [40, 50, 60]
}

result = manager.optimize_strategy('MA_Crossover', param_grid, data)
print(f"Best params: {result.best_params}")
print(f"Best score: {result.best_score}")
```

## 使用示例

```python
import pandas as pd
from modules.strategy.base import StrategyConfig, SignalType
from modules.strategy.classic.moving_average_crossover import MovingAverageCrossoverStrategy

# 准备数据
data = pd.read_csv('stock_data.csv', index_col='date', parse_dates=True)

# 创建策略
config = StrategyConfig(
    name='双均线策略',
    symbol='600519.SH',
    params={
        'short_period': 10,
        'long_period': 30,
        'ma_type': 'sma'
    }
)
strategy = MovingAverageCrossoverStrategy(config)

# 生成信号
signals = strategy.generate_signals(data)

# 打印信号
for sig in signals:
    print(f"{sig.timestamp} - {sig.symbol} - {sig.signal_type.name} - 价格: {sig.price}")
```

## 测试

```bash
cd /home/lam/.openclaw/workspace/investment_research
python -m pytest tests/test_strategies.py -v
```

## 扩展策略

可以继承现有策略类创建自定义策略:

```python
from modules.strategy.base import Strategy, StrategyConfig, SignalType

class MyCustomStrategy(Strategy):
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.my_param = config.get_param('my_param', 10)
    
    def initialize(self) -> None:
        self._is_initialized = True
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        # 实现自定义逻辑
        signals = []
        # ...
        return signals
```