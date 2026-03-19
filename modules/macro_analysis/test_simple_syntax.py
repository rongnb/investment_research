#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的语法检查脚本，只检查Python语法，不导入外部依赖
"""

import sys
import traceback
from pathlib import Path


def check_syntax(file_path):
    """检查单个文件的语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试编译代码检查语法
        compile(content, file_path, 'exec')
        return True, None
    except Exception as e:
        return False, f"{e} (行: {e.lineno if hasattr(e, 'lineno') else '未知'})"


def main():
    project_root = Path(__file__).parent.parent.parent
    
    print("=" * 60)
    print("Top-Down分析和分型技术分析 - 简单语法检查")
    print("=" * 60)
    print()
    
    # 需要检查的关键Python文件
    files_to_check = [
        "modules/macro_analysis/technical/fractal.py",
        "modules/macro_analysis/technical/trend.py", 
        "modules/macro_analysis/framework/top_down.py",
        "modules/macro_analysis/framework/china_market.py",
        "modules/macro_analysis/test_top_down_fractal.py"
    ]
    
    results = []
    for file_path in files_to_check:
        full_path = project_root / file_path
        is_ok, error_msg = check_syntax(full_path)
        
        if is_ok:
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}: {error_msg}")
            results.append(file_path)
    
    print()
    print("=" * 60)
    if results:
        print(f"发现 {len(results)} 个语法错误")
        return 1
    else:
        print("所有检查的文件语法都正确")
        return 0


if __name__ == "__main__":
    sys.exit(main())
