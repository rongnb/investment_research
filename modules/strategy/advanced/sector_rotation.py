"""
行业轮动策略 (Sector Rotation Strategy)

策略原理:
- 在不同行业之间轮动
- 基于动量、估值或经济周期进行行业选择

方法:
- 动量轮动: 选取近期表现最好的行业
- 估值轮动: 选取估值最低的行业
- 周期轮动: 根据经济周期配置行业

参数:
- sectors: 行业列表
- rotation_method: 轮动方法 (momentum/value/cycle)
- top_n: 选取行业数量
- rebalance_period: 调仓周期
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime

from ..base import (
    MultiAssetStrategy, StrategyConfig, Signal, 
    SignalType, create_signal
)


class SectorRotationStrategy(MultiAssetStrategy):
    """行业轮动策略"""
    
    DEFAULT_SECTORS = ['technology', 'finance', 'consumer', 'healthcare', 'energy', 'industrial']
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.sectors = config.get_param('sectors', self.DEFAULT_SECTORS)
        self.rotation_method = config.get_param('rotation_method', 'momentum')
        self.top_n = config.get_param('top_n', 3)
        self.rebalance_period = config.get_param('rebalance_period', 20)
        
    def initialize(self) -> None:
        self._is_initialized = True
        self._current_sectors = []
    
    def _calculate_sector_scores(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """计算各行业得分"""
        scores = {}
        
        for sector, df in data.items():
            if 'close' not in df.columns:
                continue
            
            prices = df['close']
            
            if self.rotation_method == 'momentum':
                # 动量得分
                ret = prices.pct_change(periods=20).iloc[-1]
                scores[sector] = ret if not np.isnan(ret) else 0
                
            elif self.rotation_method == 'value':
                # 估值得分 (简化: 使用波动率作为逆向指标)
                volatility = prices.pct_change().std()
                scores[sector] = -volatility if not np.isnan(volatility) else 0
                
            elif self.rotation_method == 'cycle':
                # 周期得分
                ret_20d = prices.pct_change(periods=20).iloc[-1]
                ret_60d = prices.pct_change(periods=60).iloc[-1]
                scores[sector] = ret_20d * 0.3 + ret_60d * 0.7 if not (np.isnan(ret_20d) or np.isnan(ret_60d)) else 0
        
        return scores
    
    def _select_top_sectors(self, scores: Dict[str, float]) -> List[str]:
        """选取Top N行业"""
        if not scores:
            return []
        
        sorted_sectors = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [s[0] for s in sorted_sectors[:self.top_n]]
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        if not data:
            return []
        
        scores = self._calculate_sector_scores(data)
        top_sectors = self._select_top_sectors(scores)
        
        signals = []
        timestamp = datetime.now()
        
        # 卖出不再持有的行业
        for sector in self._current_sectors:
            if sector not in top_sectors and sector in data and 'close' in data[sector].columns:
                price = data[sector]['close'].iloc[-1]
                signals.append(create_signal(
                    symbol=sector,
                    signal_type=SignalType.SELL,
                    price=price,
                    strength=0.8,
                    timestamp=timestamp,
                    reason='sector_rotation'
                ))
        
        # 买入新行业
        for sector in top_sectors:
            if sector in data and 'close' in data[sector].columns:
                price = data[sector]['close'].iloc[-1]
                score = scores.get(sector, 0)
                rank = top_sectors.index(sector) + 1
                
                signals.append(create_signal(
                    symbol=sector,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=1.0 - (rank - 1) * 0.2,  # 排名越前强度越高
                    timestamp=timestamp,
                    sector_score=score,
                    rank=rank,
                    method=self.rotation_method
                ))
        
        self._current_sectors = top_sectors
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals


class CyclicalDefensiveRotation(SectorRotationStrategy):
    """周期-防御轮动策略"""
    
    CYCLICAL_SECTORS = ['technology', 'industrial', 'materials', 'energy']
    DEFENSIVE_SECTORS = ['consumer', 'healthcare', 'utilities', 'telecom']
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.rotation_method = 'cycle'
        
    def _calculate_cycle_position(self, data: Dict[str, pd.DataFrame]) -> str:
        """判断经济周期位置"""
        # 简化: 使用市场整体动量
        if not data:
            return 'neutral'
        
        # 周期行业平均收益
        cyclical_returns = []
        for sector in self.CYCLICAL_SECTORS:
            if sector in data and 'close' in data[sector].columns:
                ret = data[sector]['close'].pct_change(periods=20).iloc[-1]
                if not np.isnan(ret):
                    cyclical_returns.append(ret)
        
        # 防御行业平均收益
        defensive_returns = []
        for sector in self.DEFENSIVE_SECTORS:
            if sector in data and 'close' in data[sector].columns:
                ret = data[sector]['close'].pct_change(periods=20).iloc[-1]
                if not np.isnan(ret):
                    defensive_returns.append(ret)
        
        if not cyclical_returns or not defensive_returns:
            return 'neutral'
        
        cyclical_avg = np.mean(cyclical_returns)
        defensive_avg = np.mean(defensive_returns)
        
        if cyclical_avg > defensive_avg + 0.02:
            return 'cyclical'
        elif defensive_avg > cyclical_avg + 0.02:
            return 'defensive'
        else:
            return 'neutral'
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        cycle_position = self._calculate_cycle_position(data)
        
        signals = []
        timestamp = datetime.now()
        
        if cycle_position == 'cyclical':
            target_sectors = self.CYCLICAL_SECTORS[:self.top_n]
        elif cycle_position == 'defensive':
            target_sectors = self.DEFENSIVE_SECTORS[:self.top_n]
        else:
            # 中性: 混合配置
            target_sectors = self.CYCLICAL_SECTORS[:2] + self.DEFENSIVE_SECTORS[:1]
        
        for sector in target_sectors:
            if sector in data and 'close' in data[sector].columns:
                price = data[sector]['close'].iloc[-1]
                signals.append(create_signal(
                    symbol=sector,
                    signal_type=SignalType.BUY,
                    price=price,
                    strength=0.8,
                    timestamp=timestamp,
                    cycle_position=cycle_position
                ))
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals