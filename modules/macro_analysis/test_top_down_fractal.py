#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Top-Down分析和分型技术分析的综合测试脚本

测试从宏观分析到入市信号的完整流程
"""

import sys
import traceback
from pathlib import Path

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)

    try:
        from modules.macro_analysis import CrawlerManager
        print("✅ CrawlerManager导入成功")
    except Exception as e:
        print(f"❌ CrawlerManager导入失败: {e}")
        return False

    try:
        from modules.macro_analysis.framework.top_down import (
            TopDownAnalyzer,
            EconomicPhase,
            SectorAllocation,
            StockSelection
        )
        print("✅ TopDown分析框架导入成功")
    except Exception as e:
        print(f"❌ TopDown分析框架导入失败: {e}")
        return False

    try:
        from modules.macro_analysis.framework.china_market import ChinaMarketAnalyzer
        print("✅ 中国市场分析器导入成功")
    except Exception as e:
        print(f"❌ 中国市场分析器导入失败: {e}")
        return False

    try:
        from modules.macro_analysis.technical.fractal import (
            FractalAnalyzer,
            FractalType,
            KLine
        )
        print("✅ 分型分析器导入成功")
    except Exception as e:
        print(f"❌ 分型分析器导入失败: {e}")
        return False

    try:
        from modules.macro_analysis.technical.trend import TrendAnalysis, TrendAnalyzer
        print("✅ 趋势分析器导入成功")
    except Exception as e:
        print(f"❌ 趋势分析器导入失败: {e}")
        return False

    return True


def test_top_down_framework():
    """测试Top-Down分析框架"""
    print("\n" + "=" * 60)
    print("测试 2: Top-Down分析框架")
    print("=" * 60)

    try:
        from modules.macro_analysis.framework.top_down import (
            TopDownAnalyzer,
            EconomicPhase,
            MacroIndicator
        )
        from datetime import datetime

        analyzer = TopDownAnalyzer()

        # 测试经济指标
        indicators = [
            MacroIndicator("GDP_GROWTH", 5.2, 0.3, 0.1, datetime(2025, 1, 1), "percent"),
            MacroIndicator("CPI", 2.1, -0.5, 0.2, datetime(2025, 1, 1), "percent"),
            MacroIndicator("UNEMPLOYMENT", 4.8, -0.2, -0.1, datetime(2025, 1, 1), "percent")
        ]

        # 测试经济周期判断
        cycle = analyzer.analyze_economic_cycle(indicators)
        print(f"✅ 经济周期分析成功: {cycle.value}")

        # 测试资产配置
        allocation = analyzer.generate_asset_allocation(cycle)
        print("✅ 资产配置建议成功")
        for asset, weight in allocation.items():
            print(f"   {asset.value}: {weight:.1%}")

        # 测试行业轮动
        sectors = analyzer.analyze_sector_rotation(cycle)
        print(f"✅ 行业轮动分析成功: {len(sectors)}个推荐行业")
        for sector in sectors:
            print(f"   - {sector}")

        return True
    except Exception as e:
        print(f"❌ Top-Down分析失败: {e}")
        print(traceback.format_exc())
        return False


def test_china_market_analysis():
    """测试中国市场分析"""
    print("\n" + "=" * 60)
    print("测试 3: 中国市场分析")
    print("=" * 60)

    try:
        from modules.macro_analysis.framework.china_market import ChinaMarketAnalyzer

        analyzer = ChinaMarketAnalyzer()

        # 生成策略
        strategy = analyzer.generate_china_specific_strategy()

        print(f"✅ 策略生成成功: {strategy['name']}")
        print(f"   目标收益率: {strategy['target_returns']:.1%}")
        print(f"   风险承受能力: {strategy['risk_tolerance']}")
        print(f"   最低投资: {strategy['minimum_investment']:,}元")

        # 测试资产配置
        allocation = strategy['asset_allocation']
        print(f"✅ 资产配置: {len(allocation)}个类别")
        for asset, weight in allocation.items():
            print(f"   {asset}: {weight:.0%}")

        # 测试行业权重
        sectors = strategy['sector_weights']
        print(f"✅ 行业权重: {len(sectors)}个行业")
        for sector, weight in sectors:
            print(f"   {sector}: {weight:.0%}")

        return True
    except Exception as e:
        print(f"❌ 中国市场分析失败: {e}")
        print(traceback.format_exc())
        return False


def test_fractal_analysis():
    """测试分型分析"""
    print("\n" + "=" * 60)
    print("测试 4: 分型分析器")
    print("=" * 60)

    try:
        from modules.macro_analysis.technical.fractal import (
            FractalAnalyzer,
            FractalType,
            KLine
        )

        # 模拟K线数据
        test_data = [
            KLine(open=100, high=105, low=98, close=102),   # 1
            KLine(open=102, high=108, low=101, close=106),  # 2
            KLine(open=106, high=110, low=104, close=105),  # 3 - 顶分型中心
            KLine(open=105, high=107, low=102, close=103),  # 4
            KLine(open=103, high=104, low=99, close=100),   # 5
            KLine(open=100, high=101, low=95, close=96),    # 6 - 底分型中心
            KLine(open=96, high=98, low=94, close=97),      # 7
            KLine(open=97, high=100, low=96, close=99),     # 8
        ]

        analyzer = FractalAnalyzer()
        fractals = analyzer.identify_fractals(test_data)

        print(f"✅ 识别到 {len(fractals)} 个分型")
        for i, fractal in enumerate(fractals, 1):
            print(f"   分型 {i}: {fractal.fractal_type.value}")

        # 测试趋势分析
        trend = analyzer.get_trend_direction(fractals)
        print(f"✅ 趋势分析成功: {trend.value}")

        # 测试交易信号
        signals = analyzer.generate_trading_signals(test_data)
        print(f"✅ 交易信号生成成功: {len(signals)}个信号")
        for signal in signals:
            print(f"   {signal['type']}: 价格={signal['price']:.2f}")

        return True
    except Exception as e:
        print(f"❌ 分型分析失败: {e}")
        print(traceback.format_exc())
        return False


def test_combined_analysis():
    """测试综合分析流程"""
    print("\n" + "=" * 60)
    print("测试 5: 综合分析流程")
    print("=" * 60)

    try:
        from modules.macro_analysis.framework.top_down import TopDownAnalyzer
        from modules.macro_analysis.framework.china_market import ChinaMarketAnalyzer
        from modules.macro_analysis.technical.fractal import FractalAnalyzer, KLine
        from datetime import datetime

        print("🔄 初始化分析器...")
        top_down_analyzer = TopDownAnalyzer()
        china_analyzer = ChinaMarketAnalyzer()
        fractal_analyzer = FractalAnalyzer()

        print("✅ 所有分析器初始化成功")

        # 创建模拟数据
        test_klines = [
            KLine(open=100, high=105, low=98, close=102),
            KLine(open=102, high=108, low=101, close=106),
            KLine(open=106, high=110, low=104, close=105),
            KLine(open=105, high=107, low=102, close=103),
            KLine(open=103, high=104, low=99, close=100)
        ]

        # 分析市场数据
        fractals = fractal_analyzer.identify_fractals(test_klines)
        trend = fractal_analyzer.get_trend_direction(fractals)

        # 执行Top-Down分析
        china_strategy = china_analyzer.generate_china_specific_strategy()

        print(f"✅ 综合分析流程成功")
        print(f"   策略名称: {china_strategy['name']}")
        print(f"   趋势方向: {trend.value}")
        print(f"   策略收益率: {china_strategy['target_returns']:.1%}")

        return True
    except Exception as e:
        print(f"❌ 综合分析流程失败: {e}")
        print(traceback.format_exc())
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("Top-Down分析与分型技术分析综合测试")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"路径: {sys.path[0]}")
    print()

    results = []

    # 运行各项测试
    print("🎯 开始测试...")

    # 模块导入测试
    results.append(("模块导入", test_imports()))
    print()

    # Top-Down分析框架测试
    results.append(("Top-Down分析", test_top_down_framework()))
    print()

    # 中国市场分析测试
    results.append(("中国市场分析", test_china_market_analysis()))
    print()

    # 分型分析测试
    results.append(("分型分析", test_fractal_analysis()))
    print()

    # 综合分析流程测试
    results.append(("综合分析", test_combined_analysis()))
    print()

    # 生成测试报告
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    success_rate = (passed / len(results)) * 100

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s} {status}")

    print()
    print(f"总结: {passed}/{len(results)} 通过 ({success_rate:.1f}%)")

    if failed == 0:
        print("\n🎉 所有测试通过! Top-Down分析系统运行正常")
    elif failed <= 2:
        print("\n⚠️  有少量测试失败，建议检查相关模块")
    else:
        print("\n❌ 有多个测试失败，系统需要修复")

    return failed


if __name__ == "__main__":
    print()
    exit_code = main()
    sys.exit(exit_code)
