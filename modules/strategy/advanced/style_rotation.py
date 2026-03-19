"""
风格轮动策略 (Style Rotation Strategy)

策略原理:
- 在不同市场风格之间轮动(成长/价值/大小盘)
- 根据动量或估值指标判断风格切换时机

风格类型:
- 成长股: 高增长,高估值
- 价值股: 低估值,高股息
- 大盘股: 稳定性,低波动
- 小盘股: 高弹性,高波动

参数:
- styles: 轮动的风格列表
- momentum_period: 动量计算周期
- lookback_period: 回溯周期
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime

from ..base import (
    MultiAssetStrategy, StrategyConfig, Signal, 
    SignalType, create_signal
)


class StyleRotationStrategy(MultiAssetStrategy):
    """风格轮动策略"""
    
    STYLES = ['growth', 'value', 'large_cap', 'small_cap']
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.styles = config.get_param('styles', self.STYLES)
        self.momentum_period = config.get_param('momentum_period', 60)
        self.lookback_period = config.get_param('lookback_period', 20)
        
    def initialize(self) -> None:
        self._is_initialized = True
        self._current_style = None
    
    def _calculate_style_momentum(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """计算各风格的动量"""
        momentum = {}
        
        for style, df in data.items():
            if 'close' in df.columns:
                prices = df['close']
                ret = prices.pct_change(periods=self.momentum_period).iloc[-1]
                momentum[style] = ret if not np.isnan(ret) else 0
        
        return momentum
    
    def _select_best_style(self, momentum: Dict[str, float]) -> str:
        """选择最佳风格"""
        if not momentum:
            return self.styles[0]
        
        # 选择动量最强的风格
        return max(momentum.items(), key=lambda x: x[1])[0]
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        if not data:
            return []
        
        momentum = self._calculate_style_momentum(data)
        best_style = self._select_best_style(momentum)
        
        signals = []
        timestamp = datetime.now()
        
        # 风格切换信号
        if self._current_style and self._current_style != best_style:
            # 卖出旧风格
            if self._current_style in data and 'close' in data[self._current_style].columns:
                price = data[self._current_style]['close'].iloc[-1]
                signals.append(create_signal(
                    symbol=self._current_style,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=0.8,
                    timestamp=timestamp,
                    reason='style_rotation'
                ))
        
        # 买入新风格
        if best_style in data and 'close' in data[best_style].columns:
            price = data[best_style]['close'].iloc[-1]
            momentum_score = momentum.get(best_style, 0)
            
            signals.append(create_signal(
                symbol=best_style,
                signal_type=SignalType.BUY,
                price=price,
                strength=min(1.0, abs(momentum_score) * 10),
                timestamp=timestamp,
                momentum=momentum_score,
                style=best_style
            ))
        
        self._current_style = best_style
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals


class ValueGrowthRotationStrategy(StyleRotationStrategy):
    """价值-成长轮动策略"""
    
    def __init__(self, config: StrategyConfig):
        config.params['styles'] = ['value', 'growth']
        super().__init__(config)
        
    def _calculate_style_momentum(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """计算价值/成长动量"""
        momentum = {}
        
        # 价值股: 低估值策略
        if 'value' in data:
            prices = data['value']['close']
            # 使用短期动量
            ret = prices.pct_change(periods=20).iloc[-1]
            momentum['value'] = ret if not np.isnan(ret) else 0
        
        # 成长股: 长期动量
        if 'growth' in data:
            prices = data['growth']['close']
            ret = prices.pct_change(periods=60).iloc[-1]
            momentum['growth'] = ret if not np.isnan(ret) else 0
        
        return momentum


class SizeRotationStrategy(StyleRotationStrategy):
    """大小盘轮动策略"""
    
    def __init__(self, config: StrategyConfig):
        config.params['styles'] = ['large_cap', 'small_cap']
        super().__init__(config)
        self.relative_strength = []
        
    def _calculate_relative_strength(self, data: Dict[str, pd.DataFrame]) -> float:
        """计算小盘相对大盘的相对强弱"""
        if 'large_cap' not in data or 'small_cap' not in data:
            return 0
        
        large_ret = data['large_cap']['close'].pct_change(periods=20).iloc[-1]
        small_ret = data['small_cap']['close'].pct_change(periods=20).iloc[-1]
        
        return small_ret - large_ret
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        rs = self._calculate_relative_strength(data)
        self.relative_strength.append(rs)
        
        signals = []
        timestamp = datetime.now()
        
        # 基于相对强弱切换
        if rs > 0.05:  # 小盘领涨
            target = 'small_cap'
        elif rs < -0.05:  # 大盘领涨
            target = 'large_cap'
        else:
            target = self._current_style or 'large_cap'
        
        if target in data and 'close' in data[target].columns:
            price = data[target]['close'].iloc[-1]
            signals.append(create_signal(
                symbol=target,
                signal_type=SignalType.BUY,
                price=price,
                strength=min(1.0, abs(rs) * 5),
                timestamp=timestamp,
                relative_strength=rs
            ))
            
            self._current_style = target
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals