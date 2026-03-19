#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础功能测试脚本

测试宏观分析模块的基础功能，不依赖外部库
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_module_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)
    
    try:
        from modules.macro_analysis import __init__
        print("✅ 模块 __init__.py 导入成功")
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    
    try:
        from modules.macro_analysis.config import config, CrawlerConfig
        print("✅ 配置模块导入成功")
        print(f"   - 默认超时: {CrawlerConfig.DEFAULT_TIMEOUT}")
        print(f"   - 最小延迟: {CrawlerConfig.MIN_DELAY}")
    except Exception as e:
        print(f"❌ 配置模块导入失败: {e}")
        return False
    
    return True


def test_database_module():
    """测试数据库模型"""
    print("\n" + "=" * 60)
    print("测试 2: 数据库模型")
    print("=" * 60)
    
    try:
        from modules.macro_analysis.database import (
            NewsArticle, SentimentAnalysis, PolicyAnalysis,
            MarketImpact, CrawlerTask, CrawlerLog, Base
        )
        print("✅ 数据库模型导入成功")
        
        # 检查表名
        print(f"   - NewsArticle: {NewsArticle.__tablename__}")
        print(f"   - SentimentAnalysis: {SentimentAnalysis.__tablename__}")
        print(f"   - PolicyAnalysis: {PolicyAnalysis.__tablename__}")
        print(f"   - MarketImpact: {MarketImpact.__tablename__}")
        print(f"   - CrawlerTask: {CrawlerTask.__tablename__}")
        print(f"   - CrawlerLog: {CrawlerLog.__tablename__}")
        
        return True
    except Exception as e:
        print(f"❌ 数据库模块导入失败: {e}")
        return False


def test_crawler_classes():
    """测试爬虫类定义"""
    print("\n" + "=" * 60)
    print("测试 3: 爬虫类定义")
    print("=" * 60)
    
    try:
        from modules.macro_analysis.crawler.base import BaseCrawler, CrawlerResult
        print("✅ 基础爬虫类导入成功")
        
        from modules.macro_analysis.crawler.government import (
            ChinaGovernmentCrawler, CSRCrawler, 
            StateCouncilPolicyCrawler, CNMCrawler
        )
        print("✅ 政府网站爬虫类导入成功")
        print(f"   - ChinaGovernmentCrawler: {ChinaGovernmentCrawler.name}")
        print(f"   - CSRCrawler: {CSRCrawler.name}")
        print(f"   - StateCouncilPolicyCrawler: {StateCouncilPolicyCrawler.name}")
        print(f"   - CNMCrawler: {CNMCrawler.name}")
        
        from modules.macro_analysis.crawler.media import (
            XinhuaNewsCrawler, PeopleDailyCrawler,
            CCTVNewsCrawler, ChinaEconomicNetCrawler
        )
        print("✅ 官方媒体爬虫类导入成功")
        print(f"   - XinhuaNewsCrawler: {XinhuaNewsCrawler.name}")
        print(f"   - PeopleDailyCrawler: {PeopleDailyCrawler.name}")
        print(f"   - CCTVNewsCrawler: {CCTVNewsCrawler.name}")
        print(f"   - ChinaEconomicNetCrawler: {ChinaEconomicNetCrawler.name}")
        
        return True
    except Exception as e:
        print(f"❌ 爬虫类导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analyzer_classes():
    """测试分析器类定义"""
    print("\n" + "=" * 60)
    print("测试 4: 分析器类定义")
    print("=" * 60)
    
    try:
        from modules.macro_analysis.analyzer.policy import PolicyAnalyzer, PolicyKeyPoint, PolicyImpact
        print("✅ 政策分析器导入成功")
        
        from modules.macro_analysis.analyzer.sentiment import SentimentAnalyzer, SentimentResult, SentimentType
        print("✅ 情感分析器导入成功")
        
        # 测试情感类型枚举
        print(f"   - SentimentType.VERY_POSITIVE: {SentimentType.VERY_POSITIVE.value}")
        print(f"   - SentimentType.POSITIVE: {SentimentType.POSITIVE.value}")
        print(f"   - SentimentType.NEUTRAL: {SentimentType.NEUTRAL.value}")
        print(f"   - SentimentType.NEGATIVE: {SentimentType.NEGATIVE.value}")
        print(f"   - SentimentType.VERY_NEGATIVE: {SentimentType.VERY_NEGATIVE.value}")
        
        return True
    except Exception as e:
        print(f"❌ 分析器类导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """测试文件结构"""
    print("\n" + "=" * 60)
    print("测试 5: 文件结构")
    print("=" * 60)
    
    module_path = project_root / "modules" / "macro_analysis"
    
    required_files = [
        "__init__.py",
        "__main__.py",
        "config.py",
        "database.py",
        "README.md",
        "IMPLEMENTATION_SUMMARY.md",
        "crawler/__init__.py",
        "crawler/base.py",
        "crawler/government.py",
        "crawler/media.py",
        "crawler/scheduler.py",
        "analyzer/__init__.py",
        "analyzer/policy.py",
        "analyzer/sentiment.py",
        "api/__init__.py",
        "api/routes.py",
    ]
    
    missing_files = []
    for file in required_files:
        file_path = module_path / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {file} ({size:,} bytes)")
        else:
            missing_files.append(file)
            print(f"❌ {file} (缺失)")
    
    if missing_files:
        print(f"\n缺失的文件: {len(missing_files)}")
        return False
    else:
        print(f"\n✅ 所有必需文件都存在")
        return True


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "宏观分析模块基础测试" + " " * 21 + "║")
    print("╚" + "═" * 58 + "╝")
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_module_imports()))
    results.append(("数据库模型", test_database_module()))
    results.append(("爬虫类", test_crawler_classes()))
    results.append(("分析器类", test_analyzer_classes()))
    results.append(("文件结构", test_file_structure()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s} {status}")
    
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 通过 ({passed/total:.1%})")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 所有测试通过！宏观分析模块结构完整！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
