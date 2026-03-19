"""
智能贝塔策略 (Smart Beta Strategy)

策略原理:
- 基于因子暴露的增强型指数策略
- 在被动投资基础上获取因子溢价

常见因子:
- 价值因子: 低PE,低PB
- 动量因子: 过去收益
- 质量因子: 高ROE,低杠杆
- 低波动因子: 低波动率
- 规模因子: 小市值

参数:
- factors: 因子列表
- factor_exposure: 目标因子暴露
- rebalance_period: 调仓周期
- min_weight/max_weight: 权重约束
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime

from ..base import (
    PortfolioStrategy, StrategyConfig, Signal, 
    SignalType, create_signal
)


class SmartBetaStrategy(PortfolioStrategy):
    """智能贝塔策略"""
    
    DEFAULT_FACTORS = ['value', 'momentum', 'quality', 'low_vol', 'size']
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.factors = config.get_param('factors', self.DEFAULT_FACTORS)
        self.factor_exposure = config.get_param('factor_exposure', {
            'value': 0.25,
            'momentum': 0.25,
            'quality': 0.25,
            'low_vol': 0.25
        })
        self.rebalance_period = config.get_param('rebalance_period', 20)
        self.min_weight = config.get_param('min_weight', 0.02)
        self.max_weight = config.get_param('max_weight', 0.15)
        
    def initialize(self) -> None:
        self._is_initialized = True
        self._factor_scores: Dict[str, Dict[str, float]] = {}
    
    def _calculate_factor_scores(self, 
                                  data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, float]]:
        """计算各资产的因子得分"""
        factor_scores = {}
        
        for symbol, df in data.items():
            if 'close' not in df.columns:
                continue
            
            prices = df['close']
            scores = {}
            
            # 价值因子 (使用收益率作为代理)
            if 'value' in self.factors:
                ret = prices.pct_change(periods=20).iloc[-1]
                scores['value'] = ret if not np.isnan(ret) else 0
            
            # 动量因子
            if 'momentum' in self.factors:
                ret = prices.pct_change(periods=60).iloc[-1]
                scores['momentum'] = ret if not np.isnan(ret) else 0
            
            # 质量因子 (负波动率 = 高质量)
            if 'quality' in self.factors:
                vol = prices.pct_change().std()
                scores['quality'] = -vol if not np.isnan(vol) else 0
            
            # 低波动因子
            if 'low_vol' in self.factors:
                vol = prices.pct_change().std() * np.sqrt(252)
                scores['low_vol'] = -vol if not np.isnan(vol) else 0
            
            # 规模因子 (简化: 使用价格作为市值代理)
            if 'size' in self.factors:
                scores['size'] = -prices.iloc[-1]  # 价格越低,规模越小
        
            factor_scores[symbol] = scores
        
        return factor_scores
    
    def _normalize_scores(self, 
                         factor_scores: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """标准化因子得分"""
        normalized = {}
        
        for factor in self.factors:
            values = [scores.get(factor, 0) for scores in factor_scores.values()]
            
            if not values:
                continue
            
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            if std_val > 0:
                for symbol in factor_scores:
                    if factor in factor_scores[symbol]:
                        factor_scores[symbol][f'{factor}_norm'] = (
                            (factor_scores[symbol][factor] - mean_val) / std_val
                        )
        
        return factor_scores
    
    def _calculate_composite_score(self, 
                                   factor_scores: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """计算综合因子得分"""
        composite = {}
        
        for symbol, scores in factor_scores.items():
            total_score = 0
            
            for factor, exposure in self.factor_exposure.items():
                norm_key = f'{factor}_norm'
                if norm_key in scores:
                    total_score += exposure * scores[norm_key]
            
            composite[symbol] = total_score
        
        return composite
    
    def calculate_weights(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """计算智能贝塔权重"""
        # 计算因子得分
        factor_scores = self._calculate_factor_scores(data)
        factor_scores = self._normalize_scores(factor_scores)
        composite = self._calculate_composite_score(factor_scores)
        
        if not composite:
            return {}
        
        # 排序并选取
        sorted_assets = sorted(composite.items(), key=lambda x: x[1], reverse=True)
        
        # 简化: 基于排名分配权重
        n = len(sorted_assets)
        weights = {}
        
        # 头部倾斜: 前N只获得更高权重
        top_n = max(5, n // 4)
        
        for i, (symbol, score) in enumerate(sorted_assets):
            if i < top_n:
                # 头部: 较高权重
                base_weight = 2.0 * (top_n - i) / (top_n * (top_n + 1) / 2)
            else:
                # 尾部: 较低权重
                base_weight = 0.5 / (n - top_n)
            
            weights[symbol] = base_weight
        
        # 归一化
        total = sum(weights.values())
        weights = {s: w / total for s, w in weights.items()}
        
        # 应用约束
        for symbol in weights:
            weights[symbol] = max(self.min_weight, 
                                 min(self.max_weight, 
                                     weights[symbol]))
        
        # 重新归一化
        total = sum(weights.values())
        weights = {s: w / total for s, w in weights.items()}
        
        self._current_weights = weights
        self._factor_scores = factor_scores
        
        return weights
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        """生成再平衡信号"""
        target_weights = self.calculate_weights(data)
        
        signals = []
        timestamp = datetime.now()
        
        for symbol, weight in target_weights.items():
            if symbol in data and 'close' in data[symbol].columns:
                price = data[symbol]['close'].iloc[-1]
                current_weight = self._current_weights.get(symbol, 0)
                weight_change = abs(weight - current_weight)
                
                if weight_change > 0.02:
                    signal_type = (SignalType.BUY if weight > current_weight 
                                  else SignalType.SELL)
                    
                    scores = self._factor_scores.get(symbol, {})
                    
                    signals.append(create_signal(
                        symbol=symbol,
                        signal_type=signal_type,
                        price=price,
                        strength=min(1.0, weight_change * 10),
                        timestamp=timestamp,
                        target_weight=weight,
                        composite_score=scores.get('composite', 0),
                        factor_scores=scores
                    ))
        
        if signals:
            self._last_signal = signals[-1]
        
        return signals


class FactorTiltingStrategy(SmartBetaStrategy):
    """因子倾斜策略 - 智能贝塔的变体"""
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.base_weights = config.get_param('base_weights', {})  # 基准权重
    
    def calculate_weights(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """计算因子倾斜后的权重"""
        # 获取因子得分
        factor_scores = self._calculate_factor_scores(data)
        factor_scores = self._normalize_scores(factor_scores)
        composite = self._calculate_composite_score(factor_scores)
        
        if not composite:
            return {}
        
        # 基准权重 (等权或市值加权)
        symbols = list(data.keys())
        n = len(symbols)
        
        if not self.base_weights:
            base = 1.0 / n
            self.base_weights = {s: base for s in symbols}
        
        # 倾斜
        tilted_weights = {}
        for symbol in symbols:
            base = self.base_weights.get(symbol, 1.0 / n)
            factor_score = composite.get(symbol, 0)
            
            # 因子暴露倾斜
            tilt = 1 + factor_score * 0.5  # 最大1.5倍
            tilted_weights[symbol] = base * tilt
        
        # 归一化
        total = sum(tilted_weights.values())
        tilted_weights = {s: w / total for s, w in tilted_weights.items()}
        
        # 应用约束
        for symbol in tilted_weights:
            tilted_weights[symbol] = max(self.min_weight, 
                                         min(self.max_weight, 
                                             tilted_weights[symbol]))
        
        total = sum(tilted_weights.values())
        tilted_weights = {s: w / total for s, w in tilted_weights.items()}
        
        self._current_weights = tilted_weights
        return tilted_weights


class QualityFactorStrategy(SmartBetaStrategy):
    """质量因子策略 - 专注质量因子"""
    
    def __init__(self, config: StrategyConfig):
        config.params['factors'] = ['quality']
        config.params['factor_exposure'] = {'quality': 1.0}
        super().__init__(config)
    
    def _calculate_factor_scores(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, float]]:
        """计算质量得分"""
        factor_scores = {}
        
        for symbol, df in data.items():
            if 'close' not in df.columns:
                continue
            
            prices = df['close']
            scores = {}
            
            # 质量: 使用收益率稳定性作为ROE的代理
            returns = prices.pct_change().dropna()
            
            # 稳定性: 低波动
            vol = returns.std()
            scores['quality'] = -vol if not np.isnan(vol) else 0
            
            # 动量确认: 上涨趋势
            ma20 = prices.rolling(20).mean()
            ma50 = prices.rolling(50).mean()
            
            if not ma20.empty and not ma50.empty:
                trend = (ma20.iloc[-1] - ma50.iloc[-1]) / ma50.iloc[-1] if ma50.iloc[-1] != 0 else 0
                scores['quality'] += trend * 0.5
            
            factor_scores[symbol] = scores
        
        return factor_scores