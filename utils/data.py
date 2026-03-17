"""
数据工具函数
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict
from pathlib import Path
import json
import pickle

def load_data(file_path: str, file_type: str = 'csv') -> Optional[pd.DataFrame]:
    """
    加载数据文件
    
    Args:
        file_path: 文件路径
        file_type: 文件类型 (csv, json, excel, pickle)
        
    Returns:
        DataFrame或None
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"文件不存在: {file_path}")
            return None
        
        if file_type == 'csv':
            return pd.read_csv(file_path)
        elif file_type == 'json':
            return pd.read_json(file_path)
        elif file_type == 'excel':
            return pd.read_excel(file_path)
        elif file_type == 'pickle':
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        else:
            print(f"不支持的文件格式: {file_type}")
            return None
            
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None

def save_data(data: pd.DataFrame, file_path: str, 
             file_type: str = 'csv', encoding: str = 'utf-8') -> bool:
    """
    保存数据到文件
    
    Args:
        data: DataFrame数据
        file_path: 文件路径
        file_type: 文件类型
        encoding: 编码格式
        
    Returns:
        保存成功返回True，否则False
    """
    try:
        file_path = Path(file_path)
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if file_type == 'csv':
            data.to_csv(file_path, index=False, encoding=encoding)
        elif file_type == 'json':
            data.to_json(file_path, force_ascii=False, indent=2)
        elif file_type == 'excel':
            data.to_excel(file_path, index=False)
        elif file_type == 'pickle':
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
        else:
            print(f"不支持的文件格式: {file_type}")
            return False
            
        print(f"数据已保存到: {file_path}")
        return True
        
    except Exception as e:
        print(f"保存数据失败: {e}")
        return False

def clean_data(data: pd.DataFrame, 
               remove_duplicates: bool = True,
               drop_missing: bool = True,
               fill_method: str = 'mean',
               numerical_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    数据清洗
    
    Args:
        data: 原始数据
        remove_duplicates: 是否删除重复值
        drop_missing: 是否删除缺失值
        fill_method: 缺失值填充方法 (mean, median, forward, backward)
        numerical_columns: 数值列列表
        
    Returns:
        清洗后的数据
    """
    cleaned_data = data.copy()
    
    # 删除重复值
    if remove_duplicates:
        original_size = len(cleaned_data)
        cleaned_data = cleaned_data.drop_duplicates()
        print(f"删除了 {original_size - len(cleaned_data)} 个重复值")
    
    # 处理缺失值
    if drop_missing:
        original_size = len(cleaned_data)
        cleaned_data = cleaned_data.dropna()
        print(f"删除了 {original_size - len(cleaned_data)} 个缺失值")
    else:
        # 填充缺失值
        if numerical_columns is None:
            numerical_columns = cleaned_data.select_dtypes(include=['int64', 'float64']).columns
            
        for col in numerical_columns:
            if fill_method == 'mean':
                value = cleaned_data[col].mean()
            elif fill_method == 'median':
                value = cleaned_data[col].median()
            elif fill_method == 'forward':
                cleaned_data[col] = cleaned_data[col].ffill()
                continue
            elif fill_method == 'backward':
                cleaned_data[col] = cleaned_data[col].bfill()
                continue
            else:
                continue
                
            cleaned_data[col].fillna(value, inplace=True)
            missing_count = data[col].isnull().sum()
            if missing_count > 0:
                print(f"列 {col} 填充了 {missing_count} 个缺失值")
    
    return cleaned_data

def validate_data(data: pd.DataFrame, 
                 column_specs: Optional[Dict[str, dict]] = None) -> Dict:
    """
    数据验证
    
    Args:
        data: 数据
        column_specs: 列验证规格
        
    Returns:
        验证结果
    """
    validation_results = {
        'data_shape': data.shape,
        'duplicate_count': data.duplicated().sum(),
        'missing_counts': data.isnull().sum().to_dict(),
        'data_types': data.dtypes.to_dict()
    }
    
    if column_specs:
        for column, specs in column_specs.items():
            if column in data.columns:
                valid_count = 0
                invalid_count = 0
                
                if 'range' in specs:
                    min_val, max_val = specs['range']
                    valid = data[column].between(min_val, max_val)
                    valid_count = valid.sum()
                    invalid_count = (~valid).sum()
                    
                validation_results[column] = {
                    'valid': valid_count,
                    'invalid': invalid_count
                }
                
    return validation_results
