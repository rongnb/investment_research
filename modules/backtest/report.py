"""
回测报告生成器
生成HTML回测报告，包含图表和统计数据
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os

from ..common.models import BacktestResult, Trade


class ReportGenerator:
    """
    回测报告生成器
    
    生成包含图表和统计数据的HTML回测报告
    """
    
    def __init__(self, result: BacktestResult, metrics: Optional[Dict] = None):
        """
        初始化报告生成器
        
        Args:
            result: 回测结果
            metrics: 额外的指标字典
        """
        self.result = result
        self.metrics = metrics if metrics else {}
        
        if hasattr(result, 'metrics'):
            self.metrics.update(result.metrics)
    
    def generate_html(self, output_path: str, 
                     include_trades: bool = True,
                     title: str = "回测报告") -> str:
        """
        生成HTML报告
        
        Args:
            output_path: 输出路径
            include_trades: 是否包含交易明细
            title: 报告标题
            
        Returns:
            生成的HTML文件路径
        """
        # 获取图表数据
        equity_data = self._get_equity_data()
        drawdown_data = self._get_drawdown_data()
        monthly_returns = self._get_monthly_returns()
        trade_summary = self._get_trade_summary() if include_trades else None
        
        # 格式化指标
        formatted_metrics = self._format_metrics()
        
        # 生成HTML
        html = self._render_html(
            title=title,
            formatted_metrics=formatted_metrics,
            equity_data=equity_data,
            drawdown_data=drawdown_data,
            monthly_returns=monthly_returns,
            trade_summary=trade_summary
        )
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path
    
    def generate_json(self, output_path: str) -> str:
        """
        生成JSON格式报告
        
        Args:
            output_path: 输出路径
            
        Returns:
            JSON文件路径
        """
        data = {
            'strategy_name': self.result.strategy_name,
            'start_date': self.result.start_date.isoformat() if self.result.start_date else None,
            'end_date': self.result.end_date.isoformat() if self.result.end_date else None,
            'initial_capital': self.result.initial_capital,
            'final_value': self.result.final_value,
            'metrics': self.metrics,
            'equity_curve': self.result.equity_curve.to_dict() if hasattr(self.result, 'equity_curve') else None,
            'total_trades': len(self.result.trades),
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def _format_metrics(self) -> Dict[str, str]:
        """格式化指标显示"""
        formatted = {}
        
        # 定义显示名称和格式化方式
        display_names = {
            'total_return': '总收益率',
            'annualized_return': '年化收益率',
            'volatility': '年化波动率',
            'max_drawdown': '最大回撤',
            'max_drawdown_duration': '最大回撤持续天数',
            'sharpe_ratio': '夏普比率',
            'sortino_ratio': '索提诺比率',
            'calmar_ratio': '卡尔马比率',
            'omega_ratio': 'Omega比率',
            'win_rate': '日胜率',
            'profit_loss_ratio': '盈亏比',
            'beta': 'Beta',
            'alpha': 'Alpha',
            'information_ratio': '信息比率',
            'treynor_ratio': '特雷诺比率',
            'skewness': '偏度',
            'kurtosis': '峰度',
            'var_95': 'VaR(95%)',
            'cvar_95': 'CVaR(95%)',
            'total_trades': '总交易次数',
            'trade_win_rate': '交易胜率',
            'total_commission': '总佣金',
            'total_slippage': '总滑点',
            'total_trading_cost': '总交易成本',
        }
        
        for key, value in self.metrics.items():
            name = display_names.get(key, key)
            
            if key in ['total_return', 'annualized_return', 'volatility', 
                      'max_drawdown', 'win_rate', 'alpha', 'excess_return',
                      'var_95', 'cvar_95']:
                formatted[name] = f"{value * 100:.2f}%"
            elif key in ['sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 
                        'omega_ratio', 'profit_loss_ratio', 'beta', 
                        'information_ratio', 'treynor_ratio', 'skewness', 
                        'kurtosis']:
                formatted[name] = f"{value:.4f}"
            elif key in ['total_trades', 'max_drawdown_duration', 
                       'up_days', 'down_days']:
                formatted[name] = f"{int(value)}"
            elif key in ['total_commission', 'total_slippage', 'total_trading_cost']:
                formatted[name] = f"{value:.2f}"
            else:
                formatted[name] = f"{value:.4f}"
        
        return formatted
    
    def _get_equity_data(self) -> List[Dict]:
        """获取权益曲线数据"""
        equity = self.result.equity_curve
        if equity is None or len(equity) == 0:
            return []
        
        data = []
        for date, value in equity.items():
            if isinstance(date, datetime):
                date_str = date.strftime('%Y-%m-%d')
            else:
                date_str = str(date)
            data.append({
                'date': date_str,
                'value': float(value)
            })
        
        return data
    
    def _get_drawdown_data(self) -> List[Dict]:
        """获取回撤曲线数据"""
        if hasattr(self.result, 'daily_returns'):
            daily_returns = self.result.daily_returns
            cumulative = (1 + daily_returns).cumprod()
            running_max = cumulative.cummax()
            drawdown = (cumulative - running_max) / running_max
            
            data = []
            for date, dd in drawdown.items():
                if isinstance(date, datetime):
                    date_str = date.strftime('%Y-%m-%d')
                else:
                    date_str = str(date)
                data.append({
                    'date': date_str,
                    'drawdown': float(dd * 100)
                })
            return data
        return []
    
    def _get_monthly_returns(self) -> Dict[str, Dict]:
        """获取月度收益汇总"""
        if hasattr(self.result, 'daily_returns'):
            daily_returns = self.result.daily_returns
            daily_returns.index = pd.to_datetime(daily_returns.index)
            monthly = daily_returns.resample('M').sum()
            
            # 按年组织
            result: Dict[str, Dict] = {}
            for date, ret in monthly.items():
                year = str(date.year)
                month = date.month
                if year not in result:
                    result[year] = {}
                result[year][f"{month}"] = float(ret * 100)
            
            # 添加年度汇总
            for year in result:
                if result[year]:
                    total = sum(result[year].values()) / 100
                    result[year]['YTD'] = total * 100
            
            return result
        return {}
    
    def _get_trade_summary(self) -> List[Dict]:
        """获取交易明细"""
        trades = self.result.trades
        if not trades:
            return []
        
        data = []
        for trade in trades:
            data.append({
                'id': trade.id,
                'code': trade.code,
                'direction': trade.direction.value,
                'price': f"{trade.price:.4f}",
                'volume': trade.volume,
                'amount': f"{trade.amount:.2f}",
                'timestamp': trade.timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(trade.timestamp, 'strftime') else str(trade.timestamp),
                'commission': f"{trade.commission:.2f}",
                'slippage': f"{trade.slippage:.4f}"
            })
        
        return data[:100]  # 限制显示最近100笔
    
    def _render_html(self, title: str, formatted_metrics: Dict,
                    equity_data: List, drawdown_data: List,
                    monthly_returns: Dict, trade_summary: Optional[List]) -> str:
        """渲染HTML"""
        equity_json = json.dumps(equity_data, ensure_ascii=False)
        drawdown_json = json.dumps(drawdown_data, ensure_ascii=False)
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .card h2 {{
            font-size: 20px;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }}
        .metric-item {{
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .metric-name {{ font-size: 14px; color: #666; margin-bottom: 5px; }}
        .metric-value {{ font-size: 20px; font-weight: bold; color: #333; }}
        .chart-container {{ position: relative; height: 400px; margin-bottom: 20px; }}
        .monthly-returns {{
            width: 100%;
            border-collapse: collapse;
        }}
        .monthly-returns td, .monthly-returns th {{
            border: 1px solid #eee;
            padding: 8px 12px;
            text-align: right;
        }}
        .monthly-returns th {{ background: #f8f9fa; font-weight: 600; }}
        .positive {{ color: #28a745; font-weight: bold; }}
        .negative {{ color: #dc3545; font-weight: bold; }}
        .trade-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        .trade-table th, .trade-table td {{
            border-bottom: 1px solid #eee;
            padding: 10px;
            text-align: left;
        }}
        .trade-table th {{ background: #f8f9fa; font-weight: 600; }}
        .buy {{ color: #28a745; font-weight: bold; }}
        .sell {{ color: #dc3545; font-weight: bold; }}
        @media (max-width: 768px) {{
            .metrics-grid {{ grid-template-columns: 1fr 1fr; }}
            .trade-table {{ font-size: 12px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>策略: {self.result.strategy_name} | {self.result.start_date.strftime('%Y-%m-%d')} ~ {self.result.end_date.strftime('%Y-%m-%d')}</p>
            <p>初始资金: {self.result.initial_capital:.2f} | 最终权益: {self.result.final_value:.2f}</p>
        </div>

        <div class="card">
            <h2>📊 核心绩效指标</h2>
            <div class="metrics-grid">
"""

        for name, value in formatted_metrics.items():
            html += f'                <div class="metric-item">\n'
            html += f'                    <div class="metric-name">{name}</div>\n'
            html += f'                    <div class="metric-value">{value}</div>\n'
            html += f'                </div>\n'

        html += """            </div>
        </div>

        <div class="card">
            <h2>📈 权益曲线</h2>
            <div class="chart-container">
                <canvas id="equityChart"></canvas>
            </div>
        </div>

        <div class="card">
            <h2>📉 回撤曲线</h2>
            <div class="chart-container">
                <canvas id="drawdownChart"></canvas>
            </div>
        </div>
"""

        if monthly_returns:
            html += """
        <div class="card">
            <h2>📅 月度收益 (%)</h2>
            <table class="monthly-returns">
                <thead>
                    <tr>
                        <th>Year</th>
                        <th>Jan</th><th>Feb</th><th>Mar</th><th>Apr</th><th>May</th><th>Jun</th>
                        <th>Jul</th><th>Aug</th><th>Sep</th><th>Oct</th><th>Nov</th><th>Dec</th>
                        <th>YTD</th>
                    </tr>
                </thead>
                <tbody>
"""

            for year in sorted(monthly_returns.keys(), reverse=True):
                months = monthly_returns[year]
                html += f'                    <tr><td>{year}</td>'
                for month in range(1, 13):
                    ret = months.get(str(month), None)
                    if ret is not None:
                        cls = 'positive' if ret > 0 else 'negative'
                        html += f'<td class="{cls}">{ret:.2f}</td>'
                    else:
                        html += '<td>-</td>'
                ytd = months.get('YTD', None)
                if ytd is not None:
                    cls = 'positive' if ytd > 0 else 'negative'
                    html += f'<td class="{cls}"><strong>{ytd:.2f}</strong></td>'
                else:
                    html += '<td>-</td>'
                html += '</tr>\n'

            html += """                </tbody>
            </table>
        </div>
"""

        if trade_summary and len(trade_summary) > 0:
            html += f"""
        <div class="card">
            <h2>💼 交易明细 (显示最近 {min(len(trade_summary), 100)} 笔)</h2>
            <table class="trade-table">
                <thead>
                    <tr>
                        <th>时间</th>
                        <th>代码</th>
                        <th>方向</th>
                        <th>价格</th>
                        <th>数量</th>
                        <th>金额</th>
                        <th>佣金</th>
                    </tr>
                </thead>
                <tbody>
"""
            for trade in trade_summary:
                direction_cls = 'buy' if trade['direction'] == 'buy' else 'sell'
                direction_text = '买入' if trade['direction'] == 'buy' else '卖出'
                html += f"""                    <tr>
                        <td>{trade['timestamp']}</td>
                        <td><strong>{trade['code']}</strong></td>
                        <td class="{direction_cls}">{direction_text}</td>
                        <td>{trade['price']}</td>
                        <td>{trade['volume']}</td>
                        <td>{trade['amount']}</td>
                        <td>{trade['commission']}</td>
                    </tr>
"""

            html += """                </tbody>
            </table>
        </div>
"""

        # 添加Chart.js代码
        html += f"""
        <script>
            // 权益曲线数据
            const equityData = {equity_json};
            const drawdownData = {drawdown_json};
            
            // 权益曲线
            const equityCtx = document.getElementById('equityChart').getContext('2d');
            new Chart(equityCtx, {{
                type: 'line',
                data: {{
                    labels: equityData.map(d => d.date),
                    datasets: [{{
                        label: '组合净值',
                        data: equityData.map(d => d.value),
                        borderColor: 'rgb(102, 126, 234)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        intersect: false,
                        mode: 'index'
                    }},
                    plugins: {{
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return `净值: ${{context.parsed.y.toFixed(2)}}`;
                                }}
                            }}
                        }}
                    },
                    scales: {{
                        x: {{
                            ticks: {{
                                maxTicksLimit: 20
                            }}
                        }}
                    }}
                }}
            }});
            
            // 回撤曲线
            const drawdownCtx = document.getElementById('drawdownChart').getContext('2d');
            new Chart(drawdownCtx, {{
                type: 'line',
                data: {{
                    labels: drawdownData.map(d => d.date),
                    datasets: [{{
                        label: '回撤 (%)',
                        data: drawdownData.map(d => d.drawdown),
                        borderColor: 'rgb(220, 53, 69)',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        intersect: false,
                        mode: 'index'
                    }},
                    plugins: {{
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return `回撤: ${{context.parsed.y.toFixed(2)}}%`;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            ticks: {{
                                maxTicksLimit: 20
                            }}
                        }},
                        y: {{
                            reverse: true
                        }}
                    }}
                }}
            }});
        </script>
    </div>
</body>
</html>
"""
        
        return html