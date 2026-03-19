#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宏观分析模块主程序

提供命令行接口用于运行爬虫和分析任务
"""

import argparse
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.macro_analysis.crawler.scheduler import CrawlerManager
from modules.macro_analysis.analyzer.policy import PolicyAnalyzer
from modules.macro_analysis.analyzer.sentiment import SentimentAnalyzer


# 配置日志
def setup_logging(log_level=logging.INFO):
    """配置日志"""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/macro_analysis.log')
        ]
    )
    return logging.getLogger('macro_analysis')


def run_crawler(args):
    """运行爬虫任务"""
    logger = setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    manager = CrawlerManager()
    
    logger.info("启动爬虫管理系统...")
    
    if args.task:
        logger.info(f"立即运行任务: {args.task}")
        manager.run_immediate_crawl([args.task])
    else:
        logger.info("立即运行所有爬虫任务")
        manager.run_immediate_crawl()
    
    # 打印状态报告
    logger.info("运行完成")
    print("\n=== 运行结果 ===")
    print(manager.get_status_report())


def run_analysis(args):
    """运行分析任务"""
    logger = setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    
    if args.text:
        # 分析指定文本
        policy_analyzer = PolicyAnalyzer()
        sentiment_analyzer = SentimentAnalyzer()
        
        logger.info("分析文本内容...")
        
        policy_result = policy_analyzer.analyze("文本分析", args.text)
        sentiment_result = sentiment_analyzer.analyze(args.text)
        
        # 输出结果
        print("\n=== 政策分析结果 ===")
        print(f"标题: {policy_result.title}")
        print(f"政策类型: {policy_result.policy_type}")
        print(f"政策级别: {policy_result.policy_level}")
        print(f"紧急程度: {policy_result.urgency_level}/10")
        print(f"置信度: {policy_result.confidence:.1%}")
        
        print("\n=== 关键要点 ===")
        for point in policy_result.key_points:
            print(f"• {point.content} (重要性: {point.importance}/10)")
        
        print("\n=== 受影响行业 ===")
        for impact in policy_result.affected_sectors:
            print(f"• {impact.sector}: {impact.impact_score:.1f} 分 ({impact.duration})")
        
        print("\n=== 情感分析结果 ===")
        print(f"总体情感: {sentiment_result.overall} ({sentiment_result.overall_score:.2f})")
        print(f"市场情感: {sentiment_result.market_sentiment:.2f}")
        print(f"政策情感: {sentiment_result.policy_sentiment:.2f}")
        print(f"行业情感: {sentiment_result.sector_sentiment:.2f}")
        print(f"置信度: {sentiment_result.confidence:.1%}")
        
        if sentiment_result.positive_keywords:
            print("\n正向关键词:")
            for kw in sentiment_result.positive_keywords:
                print(f"• {kw}")
        
        if sentiment_result.negative_keywords:
            print("\n负向关键词:")
            for kw in sentiment_result.negative_keywords:
                print(f"• {kw}")
    else:
        logger.error("请提供要分析的文本内容")


def show_status(args):
    """显示系统状态"""
    logger = setup_logging(logging.INFO)
    manager = CrawlerManager()
    
    print("=== 爬虫系统状态 ===")
    print(manager.get_status_report())


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description="宏观分析模块 - 官方媒体和政府文件爬虫与分析工具"
    )
    
    parser.add_argument(
        '-v', '--verbose', 
        action='store_true', 
        help='显示详细输出'
    )
    
    subparsers = parser.add_subparsers(title='子命令')
    
    # 爬虫子命令
    parser_crawler = subparsers.add_parser('crawler', help='爬虫管理')
    parser_crawler.add_argument(
        '-t', '--task', 
        help='指定要运行的爬虫任务名称'
    )
    parser_crawler.set_defaults(func=run_crawler)
    
    # 分析子命令
    parser_analysis = subparsers.add_parser('analyze', help='文本分析')
    parser_analysis.add_argument(
        '-t', '--text', 
        help='要分析的文本内容'
    )
    parser_analysis.set_defaults(func=run_analysis)
    
    # 状态子命令
    parser_status = subparsers.add_parser('status', help='显示状态')
    parser_status.set_defaults(func=show_status)
    
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        try:
            args.func(args)
        except KeyboardInterrupt:
            print("\n程序已终止")
        except Exception as e:
            print(f"错误: {e}")
            if args.verbose:
                import traceback
                print(traceback.format_exc())
            return 1
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    main()
