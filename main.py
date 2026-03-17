#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Investment Research System - Main Entry Point

This script serves as the primary interface for the Investment Research System,
providing a comprehensive command-line interface for investment analysis and portfolio management.
"""

import argparse
import sys
import logging
from pathlib import Path

# 添加项目路径到sys.path
PROJECT_PATH = Path(__file__).parent
sys.path.append(str(PROJECT_PATH))

from utils.logger import setup_logger, Logger
from modules.macro.analyzer import MacroAnalyzer, EconomicCycle
from modules.research.analyzer import ResearchAnalyzer
from modules.estimation.estimator import ParameterEstimator
from modules.decision.optimizer import PortfolioOptimizer, RiskTolerance

def main():
    """Main entry point"""
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='Investment Research System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
        Example Usage:
            python main.py macro --start-date "2020-01-01" --end-date "2024-12-31"
            python main.py optimize --budget 100000 --risk-tolerance moderate
            python main.py research --file-path "/path/to/report.pdf"
            python main.py estimate --parameter GDP_GROWTH
        '''
    )
    
    # 配置参数
    parser.add_argument('-v', '--version', action='version', 
                       version='Investment Research System v0.1.0')
    
    subparsers = parser.add_subparsers(title='Subcommands', dest='subcommand')
    
    # 宏观分析子命令
    macro_parser = subparsers.add_parser('macro', 
                                       help='宏观经济分析')
    macro_parser.add_argument('--start-date', type=str, 
                            help='开始日期 (YYYY-MM-DD)')
    macro_parser.add_argument('--end-date', type=str, 
                            help='结束日期 (YYYY-MM-DD)')
    
    # 优化子命令
    optimize_parser = subparsers.add_parser('optimize', 
                                           help='投资组合优化')
    optimize_parser.add_argument('--budget', type=float, default=100000, 
                               help='投资预算')
    optimize_parser.add_argument('--risk-tolerance', type=str, 
                               choices=['low', 'moderate', 'high'],
                               default='moderate', 
                               help='风险容忍度')
    
    # 研报分析子命令
    research_parser = subparsers.add_parser('research', 
                                           help='研报分析')
    research_parser.add_argument('--file-path', type=str, 
                               help='研报文件路径')
    
    # 参数估计子命令
    estimate_parser = subparsers.add_parser('estimate', 
                                           help='经济参数估计')
    estimate_parser.add_argument('--parameter', type=str, required=True,
                               choices=['GDP_GROWTH', 'CPI', 'PPI', 'INTEREST_RATE',
                                        'UNEMPLOYMENT', 'MONEY_SUPPLY'],
                               help='参数类型')
    
    # 可视化子命令
    visualize_parser = subparsers.add_parser('visualize', 
                                           help='数据可视化')
    visualize_parser.add_argument('--type', type=str, required=True,
                               choices=['assets', 'cycle', 'performance'],
                               help='可视化类型')
    
    args = parser.parse_args()
    
    # 设置日志
    logger = Logger.get_logger()
    logger.setLevel(logging.INFO)
    
    try:
        if args.subcommand == 'macro':
            # 宏观经济分析
            analyze_macro(args)
        elif args.subcommand == 'optimize':
            # 投资组合优化
            optimize_portfolio(args)
        elif args.subcommand == 'research':
            # 研报分析
            analyze_research(args)
        elif args.subcommand == 'estimate':
            # 参数估计
            estimate_parameter(args)
        elif args.subcommand == 'visualize':
            # 可视化
            visualize_data(args)
        else:
            # 没有指定子命令，显示帮助信息
            parser.print_help()
            
        return 0
            
    except KeyboardInterrupt:
        logger.info("操作被用户中断")
        return 1
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
        return 2

def analyze_macro(args):
    """宏观经济分析"""
    logger = Logger.get_logger()
    logger.info("开始宏观经济分析")
    
    analyzer = MacroAnalyzer()
    
    if args.start_date and args.end_date:
        indicators = analyzer.fetch_economic_indicators(
            args.start_date, args.end_date
        )
    else:
        # 使用模拟数据
        indicators = analyzer.fetch_economic_indicators(
            "2020-01-01", "2024-12-31"
        )
    
    cycle = analyzer.analyze_economic_cycle(indicators)
    report = analyzer.generate_macro_report(indicators, cycle)
    
    logger.info("\n" + report)

def optimize_portfolio(args):
    """投资组合优化"""
    logger = Logger.get_logger()
    logger.info(f"开始投资组合优化，预算: {args.budget:.2f}")
    
    # 转换风险容忍度
    risk_tolerance = {
        'low': RiskTolerance.LOW,
        'moderate': RiskTolerance.MODERATE,
        'high': RiskTolerance.HIGH
    }[args.risk_tolerance.lower()]
    
    optimizer = PortfolioOptimizer(args.budget, risk_tolerance)
    
    # 使用合成数据进行优化
    portfolio = optimizer.optimize_risk_return()
    
    logger.info(f"优化结果:")
    logger.info(f"预期收益率: {portfolio.expected_return:.2%}")
    logger.info(f"波动率: {portfolio.volatility:.2%}")
    logger.info(f"夏普比率: {portfolio.sharpe_ratio:.2f}")
    
    # 输出详细分配
    logger.info("资产分配:")
    allocations = optimizer.get_weight_allocation(portfolio)
    
    for asset, info in allocations.items():
        logger.info(f"{asset}: 权重 {info['weight']:.1%}, 金额 {info['amount']:.2f}元")

def analyze_research(args):
    """研报分析"""
    logger = Logger.get_logger()
    logger.info("开始研报分析")
    
    if not args.file_path:
        logger.warning("未提供研报文件路径，使用示例数据")
        # 创建临时示例
        return
    
    try:
        analyzer = ResearchAnalyzer()
        
        report = analyzer.read_pdf_report(args.file_path)
        
        # 分析
        key_points = analyzer.extract_key_points(report)
        target_price = analyzer.extract_target_price(report)
        risk_assessment = analyzer.extract_risk_assessment(report)
        investment_rating = analyzer.extract_investment_rating(report)
        
        logger.info(f"关键信息: {key_points}")
        logger.info(f"目标价: {target_price}")
        logger.info(f"风险评估: {risk_assessment}")
        logger.info(f"投资评级: {investment_rating}")
        
    except Exception as e:
        logger.error(f"研报分析失败: {e}")

def estimate_parameter(args):
    """经济参数估计"""
    logger = Logger.get_logger()
    logger.info(f"开始参数估计: {args.parameter}")
    
    estimator = ParameterEstimator()
    
    # 生成数据
    import pandas as pd
    from modules.estimation.estimator import ParameterType
    
    param_type = {
        'GDP_GROWTH': ParameterType.GDP_GROWTH,
        'CPI': ParameterType.CPI,
        'PPI': ParameterType.PPI,
        'INTEREST_RATE': ParameterType.INTEREST_RATE,
        'UNEMPLOYMENT': ParameterType.UNEMPLOYMENT,
        'MONEY_SUPPLY': ParameterType.MONEY_SUPPLY
    }[args.parameter]
    
    data = estimator.generate_synthetic_data(param_type)
    
    # 参数估计
    result = estimator.estimate_parameter(param_type, data)
    
    logger.info(f"估计结果:")
    logger.info(f"参数: {result.parameter.value}")
    logger.info(f"估计值: {result.estimate:.2f}")
    logger.info(f"置信区间: [{result.lower_bound:.2f}, {result.upper_bound:.2f}]")
    logger.info(f"R-squared: {result.r_squared:.3f}")

def visualize_data(args):
    """可视化"""
    logger = Logger.get_logger()
    logger.info(f"开始可视化: {args.type}")
    
    # 可视化功能待完善
    from utils.visualization import plot_assets, plot_economic_cycle
    
    if args.type == 'assets':
        from modules.decision.optimizer import PortfolioOptimizer
        optimizer = PortfolioOptimizer()
        assets, _ = optimizer.generate_synthetic_assets()
        assets['weight'] = [0.1, 0.15, 0.2, 0.1, 0.15, 0.1, 0.1, 0.1]
        plot_assets(assets)
        
    elif args.type == 'cycle':
        cycle_data = {
            'time_series': {
                'dates': ["2020-01", "2020-02", "2020-03", "2020-04"],
                'values': [100, 102, 105, 110]
            }
        }
        plot_economic_cycle(cycle_data)
        
    logger.info("可视化完成")

if __name__ == "__main__":
    sys.exit(main())
