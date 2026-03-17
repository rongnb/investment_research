"""
可视化工具函数
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Dict, List, Optional
from pathlib import Path
import numpy as np

def plot_assets(assets: pd.DataFrame, 
               output_file: Optional[str] = None) -> None:
    """
    绘制资产分布
    
    Args:
        assets: 资产数据
        output_file: 输出文件名
    """
    plt.figure(figsize=(12, 8))
    
    # 资产权重分布
    ax1 = plt.subplot(2, 2, 1)
    weights = list(assets['weight'] if 'weight' in assets.columns else 
                   np.ones(len(assets)) / len(assets))
    plt.pie(weights, labels=assets['asset'], autopct='%1.1f%%', 
            startangle=90, shadow=True)
    plt.title('资产权重分布')
    
    # 预期收益率
    ax2 = plt.subplot(2, 2, 2)
    plt.bar(assets['asset'], assets['expected_return'], 
            color=sns.color_palette('Set2'))
    plt.ylabel('预期收益率')
    plt.title('资产预期收益率')
    plt.xticks(rotation=45)
    
    # 波动率
    ax3 = plt.subplot(2, 2, 3)
    plt.bar(assets['asset'], assets['volatility'], 
            color=sns.color_palette('Set3'))
    plt.ylabel('波动率')
    plt.title('资产波动率')
    plt.xticks(rotation=45)
    
    # 相关性矩阵（如果有相关性数据）
    if 'correlation' in assets.columns:
        ax4 = plt.subplot(2, 2, 4)
        correlation = assets['correlation'].values
        plt.imshow(correlation, cmap='coolwarm', vmin=-1, vmax=1)
        plt.colorbar()
        plt.title('资产相关性矩阵')
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {output_file}")
    else:
        plt.show()

def plot_economic_cycle(cycle_data: Dict, 
                       output_file: Optional[str] = None) -> None:
    """
    绘制经济周期图表
    
    Args:
        cycle_data: 周期数据
        output_file: 输出文件名
    """
    plt.figure(figsize=(10, 6))
    
    # 指标时间序列
    if 'time_series' in cycle_data:
        plt.plot(cycle_data['time_series']['dates'], 
                cycle_data['time_series']['values'],
                linewidth=2, color='#2E8B57', marker='o')
        
        # 标记周期阶段
        if 'cycle_stages' in cycle_data:
            for stage in cycle_data['cycle_stages']:
                plt.axvspan(stage['start_date'], stage['end_date'],
                          alpha=0.3, color=stage['color'], 
                          label=stage['stage'])
    
    plt.xlabel('时间')
    plt.ylabel('经济指标值')
    plt.title('经济周期波动')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    else:
        plt.show()

def plot_correlation_matrix(corr_matrix: pd.DataFrame, 
                          output_file: Optional[str] = None) -> None:
    """
    绘制相关性矩阵热力图
    
    Args:
        corr_matrix: 相关性矩阵
        output_file: 输出文件名
    """
    plt.figure(figsize=(10, 8))
    
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm',
               mask=mask, fmt='.2f', cbar_kws={'shrink': .8})
    
    plt.title('资产相关性矩阵')
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    else:
        plt.show()

def plot_portfolio_performance(returns: pd.DataFrame, 
                             portfolio_name: str = '投资组合',
                             benchmark: Optional[pd.Series] = None,
                             output_file: Optional[str] = None) -> None:
    """
    绘制投资组合绩效图表
    
    Args:
        returns: 收益率数据
        portfolio_name: 组合名称
        benchmark: 基准收益率
        output_file: 输出文件名
    """
    plt.figure(figsize=(12, 6))
    
    # 累积收益率
    cumulative_returns = (1 + returns).cumprod()
    
    plt.plot(cumulative_returns, 
             linewidth=2, color='#0066CC', 
             label=portfolio_name)
    
    if benchmark is not None:
        cumulative_benchmark = (1 + benchmark).cumprod()
        plt.plot(cumulative_benchmark, 
                 linewidth=2, color='#FF6600', 
                 label='基准')
    
    plt.xlabel('时间')
    plt.ylabel('累积收益率')
    plt.title(f'{portfolio_name} 绩效表现')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    else:
        plt.show()

def plot_risk_return_scatter(assets: pd.DataFrame, 
                           output_file: Optional[str] = None) -> None:
    """
    绘制风险收益散点图
    
    Args:
        assets: 资产数据
        output_file: 输出文件名
    """
    plt.figure(figsize=(10, 6))
    
    plt.scatter(assets['volatility'], assets['expected_return'], 
                s=assets.get('weight', np.ones(len(assets)))*1000,
                c=assets['expected_return']/assets['volatility'],
                cmap='viridis', alpha=0.7)
    
    plt.xlabel('波动率 (风险)')
    plt.ylabel('预期收益率')
    plt.title('风险-收益散点图')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.colorbar(label='夏普比率')
    
    # 标注资产名称
    for i, asset in enumerate(assets['asset']):
        plt.annotate(asset, 
                    (assets['volatility'].iloc[i], 
                     assets['expected_return'].iloc[i]),
                    fontsize=8)
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    else:
        plt.show()
