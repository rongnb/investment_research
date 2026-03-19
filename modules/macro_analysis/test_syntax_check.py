#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Top-Down分析和分型技术分析的基础语法测试脚本

专注于检查代码语法和基本导入，避免依赖外部模块
"""

import sys
import traceback
from pathlib import Path

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """测试基础模块导入"""
    print("=" * 60)
    print("测试 1: 基础模块导入")
    print("=" * 60)

    test_modules = [
        ("fractal", "from modules.macro_analysis.technical import fractal"),
        ("trend", "from modules.macro_analysis.technical import trend"),
        ("top_down", "from modules.macro_analysis.framework import top_down"),
        ("china_market", "from modules.macro_analysis.framework import china_market"),
    ]

    all_imported = True

    for module_name, import_statement in test_modules:
        try:
            exec(import_statement)
            print(f"✅ {module_name} 导入成功")
        except Exception as e:
            print(f"❌ {module_name} 导入失败: {e}")
            all_imported = False

    return all_imported


def test_file_existence():
    """测试关键文件是否存在"""
    print("\n" + "=" * 60)
    print("测试 2: 关键文件存在性")
    print("=" * 60)

    required_files = [
        "modules/macro_analysis/technical/fractal.py",
        "modules/macro_analysis/technical/trend.py",
        "modules/macro_analysis/framework/top_down.py",
        "modules/macro_analysis/framework/china_market.py",
        "modules/macro_analysis/README.md",
        "modules/macro_analysis/test_top_down_fractal.py",
    ]

    all_exist = True

    for file_path in required_files:
        full_path = Path(project_root) / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"✅ {file_path} ({size:,} bytes)")
        else:
            print(f"❌ {file_path}")
            all_exist = False

    return all_exist


def test_syntax_check():
    """测试代码语法"""
    print("\n" + "=" * 60)
    print("测试 3: Python 语法检查")
    print("=" * 60)

    # 需要检查的Python文件列表
    python_files = [
        "modules/macro_analysis/technical/fractal.py",
        "modules/macro_analysis/technical/trend.py",
        "modules/macro_analysis/framework/top_down.py",
        "modules/macro_analysis/framework/china_market.py",
    ]

    all_syntactically_correct = True

    for file_path in python_files:
        full_path = Path(project_root) / file_path
        try:
            # 使用 compile() 函数检查语法
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                compile(content, str(full_path), 'exec')
            print(f"✅ {file_path} 语法检查通过")
        except SyntaxError as e:
            print(f"❌ {file_path} 语法错误")
            print(f"   行: {e.lineno}, 列: {e.offset}")
            print(f"   错误: {e.msg}")
            all_syntactically_correct = False
        except Exception as e:
            print(f"❌ {file_path} 读取失败: {e}")
            all_syntactically_correct = False

    return all_syntactically_correct


def analyze_code_quality():
    """分析代码质量指标"""
    print("\n" + "=" * 60)
    print("代码质量分析")
    print("=" * 60)

    # 分析每个模块的代码质量
    modules_analysis = []

    for module_name in ["fractal", "trend", "top_down", "china_market"]:
        file_path = f"modules/macro_analysis/technical/{module_name}.py" if module_name in ["fractal", "trend"] else \
                   f"modules/macro_analysis/framework/{module_name}.py"

        full_path = Path(project_root) / file_path

        if full_path.exists():
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                line_count = content.count('\n') + 1
                word_count = len(content.split())
                class_count = content.count('class ')
                function_count = content.count('def ')
                comment_count = content.count('#')

                modules_analysis.append({
                    "name": module_name,
                    "lines": line_count,
                    "words": word_count,
                    "classes": class_count,
                    "functions": function_count,
                    "comments": comment_count
                })

    if modules_analysis:
        print(f"{'模块':<10} | {'行数':<5} | {'单词数':<6} | {'类':<2} | {'函数':<3} | {'注释':<3}")
        print("-" * 70)
        for analysis in modules_analysis:
            print(f"{analysis['name']:<10} | {analysis['lines']:<5} | {analysis['words']:<6} | "
                  f"{analysis['classes']:<2} | {analysis['functions']:<3} | {analysis['comments']:<3}")

        # 计算平均值
        total_lines = sum(analysis['lines'] for analysis in modules_analysis)
        total_words = sum(analysis['words'] for analysis in modules_analysis)
        avg_lines_per_module = total_lines / len(modules_analysis)
        avg_words_per_module = total_words / len(modules_analysis)

        print("-" * 70)
        print(f"{'平均值':<10} | {avg_lines_per_module:<5.1f} | {avg_words_per_module:<6.0f} | "
              f"{'':<2} | {'':<3} | {'':<3}")

    return True


def main():
    """主测试函数"""
    print("=" * 60)
    print("Top-Down分析和分型技术分析基础语法测试")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"路径: {sys.path[0]}")
    print()

    results = []

    # 运行各项测试
    print("🎯 开始测试...")

    # 测试模块导入
    results.append(("模块导入", test_imports()))
    print()

    # 测试文件存在性
    results.append(("文件存在性", test_file_existence()))
    print()

    # 测试语法
    results.append(("语法检查", test_syntax_check()))
    print()

    # 分析代码质量
    results.append(("代码质量分析", analyze_code_quality()))
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
        print(f"{name:10s} {status}")

    print()
    print(f"总结: {passed}/{len(results)} 通过 ({success_rate:.1f}%)")

    if failed == 0:
        print("\n🎉 所有基础测试通过！代码结构良好")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")

    return failed


if __name__ == "__main__":
    print()
    exit_code = main()
    sys.exit(exit_code)
