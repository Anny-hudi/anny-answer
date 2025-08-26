"""
数据验证模块

提供A股数据的完整性、准确性和质量检查功能。
包括价格逻辑验证、异常值检测、数据连续性检查等。
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings

warnings.filterwarnings('ignore')


class DataValidator:
    """数据验证器"""
    
    def __init__(self, validation_config: Dict[str, Any] = None):
        """
        初始化数据验证器
        
        Args:
            validation_config: 验证配置
        """
        self.validation_config = validation_config or {}
        self.validation_rules = self._init_validation_rules()
        
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 验证结果
        self.validation_results = {}
    
    def _init_validation_rules(self) -> Dict[str, Any]:
        """
        初始化验证规则
        
        Returns:
            验证规则字典
        """
        default_rules = {
            'price_rules': {
                'min_price': 0.01,  # 最小股价
                'max_price': 10000,  # 最大股价
                'max_daily_change': 0.2,  # 最大日涨跌幅
                'price_precision': 2  # 价格精度
            },
            'volume_rules': {
                'min_volume': 0,  # 最小成交量
                'max_volume_spike': 10,  # 最大成交量异常倍数
                'volume_zero_tolerance': 0.05  # 成交量为0的容忍度
            },
            'logic_rules': {
                'require_high_low_order': True,  # 要求最高价>=最低价
                'require_ohlc_consistency': True,  # 要求OHLC逻辑一致
                'allow_missing_values': False  # 是否允许缺失值
            },
            'temporal_rules': {
                'check_trading_days': True,  # 检查交易日
                'max_gap_days': 5,  # 最大数据间隔天数
                'require_chronological': True  # 要求时间序列
            }
        }
        
        # 合并用户配置
        if self.validation_config:
            for category, rules in self.validation_config.items():
                if category in default_rules:
                    default_rules[category].update(rules)
                else:
                    default_rules[category] = rules
        
        return default_rules
    
    def validate_data_format(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        验证数据格式
        
        Args:
            data: 股票数据
            
        Returns:
            验证结果
        """
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'details': {}
        }
        
        try:
            # 检查必要列
            required_columns = ['stock_code', 'trade_date', 'open_price', 'high_price', 
                              'low_price', 'close_price', 'volume', 'amount']
            
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                results['is_valid'] = False
                results['errors'].append(f"缺少必要列: {missing_columns}")
            
            # 检查数据类型
            if 'trade_date' in data.columns:
                if not pd.api.types.is_datetime64_any_dtype(data['trade_date']):
                    try:
                        pd.to_datetime(data['trade_date'])
                    except:
                        results['warnings'].append("trade_date列可能不是有效的日期格式")
            
            # 检查数值列
            numeric_columns = ['open_price', 'high_price', 'low_price', 'close_price', 'volume', 'amount']
            for col in numeric_columns:
                if col in data.columns:
                    if not pd.api.types.is_numeric_dtype(data[col]):
                        results['warnings'].append(f"{col}列不是数值类型")
            
            # 检查数据行数
            if len(data) == 0:
                results['is_valid'] = False
                results['errors'].append("数据为空")
            
            results['details']['total_records'] = len(data)
            results['details']['columns'] = list(data.columns)
            
        except Exception as e:
            results['is_valid'] = False
            results['errors'].append(f"格式验证异常: {str(e)}")
        
        return results
    
    def validate_data_range(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        验证数据范围
        
        Args:
            data: 股票数据
            
        Returns:
            验证结果
        """
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'details': {}
        }
        
        try:
            price_rules = self.validation_rules['price_rules']
            volume_rules = self.validation_rules['volume_rules']
            
            # 检查价格范围
            price_columns = ['open_price', 'high_price', 'low_price', 'close_price']
            for col in price_columns:
                if col in data.columns:
                    # 检查负价格
                    negative_prices = data[data[col] < 0]
                    if not negative_prices.empty:
                        results['is_valid'] = False
                        results['errors'].append(f"{col}存在负值: {len(negative_prices)}条记录")
                    
                    # 检查极端价格
                    min_price = price_rules['min_price']
                    max_price = price_rules['max_price']
                    
                    extreme_low = data[data[col] < min_price]
                    if not extreme_low.empty:
                        results['warnings'].append(f"{col}存在异常低价: {len(extreme_low)}条记录 < {min_price}")
                    
                    extreme_high = data[data[col] > max_price]
                    if not extreme_high.empty:
                        results['warnings'].append(f"{col}存在异常高价: {len(extreme_high)}条记录 > {max_price}")
            
            # 检查成交量范围
            if 'volume' in data.columns:
                negative_volume = data[data['volume'] < 0]
                if not negative_volume.empty:
                    results['is_valid'] = False
                    results['errors'].append(f"成交量存在负值: {len(negative_volume)}条记录")
                
                # 检查成交量为0的比例
                zero_volume = data[data['volume'] == 0]
                zero_ratio = len(zero_volume) / len(data) if len(data) > 0 else 0
                
                if zero_ratio > volume_rules['volume_zero_tolerance']:
                    results['warnings'].append(f"成交量为0的比例过高: {zero_ratio:.2%}")
            
            # 统计信息
            results['details']['price_statistics'] = {}
            for col in price_columns:
                if col in data.columns:
                    results['details']['price_statistics'][col] = {
                        'min': float(data[col].min()),
                        'max': float(data[col].max()),
                        'mean': float(data[col].mean()),
                        'std': float(data[col].std())
                    }
            
            if 'volume' in data.columns:
                results['details']['volume_statistics'] = {
                    'min': int(data['volume'].min()),
                    'max': int(data['volume'].max()),
                    'mean': float(data['volume'].mean()),
                    'zero_count': int((data['volume'] == 0).sum())
                }
        
        except Exception as e:
            results['is_valid'] = False
            results['errors'].append(f"范围验证异常: {str(e)}")
        
        return results
    
    def check_price_logic(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        检查价格逻辑
        
        Args:
            data: 股票数据
            
        Returns:
            验证结果
        """
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'details': {}
        }
        
        try:
            if not all(col in data.columns for col in ['open_price', 'high_price', 'low_price', 'close_price']):
                results['errors'].append("缺少价格列，无法进行逻辑检查")
                results['is_valid'] = False
                return results
            
            # 检查 low <= open, close <= high
            logic_errors = data[
                (data['low_price'] > data['open_price']) |
                (data['low_price'] > data['close_price']) |
                (data['high_price'] < data['open_price']) |
                (data['high_price'] < data['close_price'])
            ]
            
            if not logic_errors.empty:
                results['is_valid'] = False
                results['errors'].append(f"价格逻辑错误: {len(logic_errors)}条记录")
                results['details']['logic_error_records'] = len(logic_errors)
                
                # 详细分析错误类型
                low_open_errors = len(data[data['low_price'] > data['open_price']])
                low_close_errors = len(data[data['low_price'] > data['close_price']])
                high_open_errors = len(data[data['high_price'] < data['open_price']])
                high_close_errors = len(data[data['high_price'] < data['close_price']])
                
                results['details']['error_breakdown'] = {
                    'low_price > open_price': low_open_errors,
                    'low_price > close_price': low_close_errors,
                    'high_price < open_price': high_open_errors,
                    'high_price < close_price': high_close_errors
                }
            
            # 检查涨跌幅是否合理
            if 'change_pct' in data.columns:
                max_change = self.validation_rules['price_rules']['max_daily_change']
                extreme_changes = data[abs(data['change_pct']) > max_change]
                
                if not extreme_changes.empty:
                    results['warnings'].append(f"异常涨跌幅: {len(extreme_changes)}条记录超过{max_change:.1%}")
            
            # 检查价格一致性
            results['details']['price_consistency'] = {
                'records_checked': len(data),
                'logic_errors': len(logic_errors),
                'error_rate': len(logic_errors) / len(data) if len(data) > 0 else 0
            }
        
        except Exception as e:
            results['is_valid'] = False
            results['errors'].append(f"价格逻辑检查异常: {str(e)}")
        
        return results
    
    def check_data_completeness(self, data: pd.DataFrame, stock_code: str = None, 
                              date_range: Tuple[str, str] = None) -> Dict[str, Any]:
        """
        检查数据完整性
        
        Args:
            data: 股票数据
            stock_code: 股票代码
            date_range: 预期日期范围
            
        Returns:
            验证结果
        """
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'details': {}
        }
        
        try:
            # 检查缺失值
            missing_analysis = {}
            for col in data.columns:
                missing_count = data[col].isnull().sum()
                if missing_count > 0:
                    missing_ratio = missing_count / len(data)
                    missing_analysis[col] = {
                        'count': int(missing_count),
                        'ratio': float(missing_ratio)
                    }
                    
                    if missing_ratio > 0.1:  # 超过10%缺失认为严重
                        results['warnings'].append(f"{col}列缺失值过多: {missing_ratio:.1%}")
            
            results['details']['missing_values'] = missing_analysis
            
            # 检查时间连续性
            if 'trade_date' in data.columns and len(data) > 1:
                data_sorted = data.sort_values('trade_date').copy()
                data_sorted['trade_date'] = pd.to_datetime(data_sorted['trade_date'])
                
                # 计算日期间隔
                date_diff = data_sorted['trade_date'].diff().dt.days
                
                # 检查异常间隔
                max_gap = self.validation_rules['temporal_rules']['max_gap_days']
                large_gaps = date_diff[date_diff > max_gap].dropna()
                
                if not large_gaps.empty:
                    results['warnings'].append(f"存在{len(large_gaps)}个超过{max_gap}天的数据间隔")
                
                results['details']['temporal_analysis'] = {
                    'date_range': {
                        'start': str(data_sorted['trade_date'].min().date()),
                        'end': str(data_sorted['trade_date'].max().date())
                    },
                    'total_days': int((data_sorted['trade_date'].max() - data_sorted['trade_date'].min()).days),
                    'data_points': len(data_sorted),
                    'max_gap_days': int(date_diff.max()) if not date_diff.empty else 0,
                    'avg_gap_days': float(date_diff.mean()) if not date_diff.empty else 0
                }
            
            # 检查重复记录
            if 'trade_date' in data.columns:
                if stock_code:
                    duplicates = data[data.duplicated(subset=['trade_date'], keep=False)]
                else:
                    duplicates = data[data.duplicated(subset=['stock_code', 'trade_date'], keep=False)]
                
                if not duplicates.empty:
                    results['warnings'].append(f"存在{len(duplicates)}条重复记录")
                    results['details']['duplicate_records'] = len(duplicates)
        
        except Exception as e:
            results['is_valid'] = False
            results['errors'].append(f"完整性检查异常: {str(e)}")
        
        return results
    
    def detect_anomalies(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        检测异常数据
        
        Args:
            data: 股票数据
            
        Returns:
            异常数据列表
        """
        anomalies = []
        
        try:
            # 基于统计方法检测价格异常
            price_columns = ['open_price', 'high_price', 'low_price', 'close_price']
            
            for col in price_columns:
                if col in data.columns:
                    # 使用Z-score检测异常值
                    z_scores = np.abs(stats.zscore(data[col].dropna()))
                    outliers = data[z_scores > 3]  # Z-score > 3 认为是异常值
                    
                    for idx, row in outliers.iterrows():
                        anomaly = {
                            'type': 'price_outlier',
                            'column': col,
                            'index': idx,
                            'value': float(row[col]),
                            'z_score': float(z_scores[idx]),
                            'trade_date': str(row.get('trade_date', 'unknown')),
                            'stock_code': row.get('stock_code', 'unknown')
                        }
                        anomalies.append(anomaly)
            
            # 检测成交量异常
            if 'volume' in data.columns:
                # 计算成交量的滚动平均和标准差
                data_sorted = data.sort_values('trade_date').copy()
                data_sorted['volume_ma20'] = data_sorted['volume'].rolling(window=20, min_periods=5).mean()
                data_sorted['volume_std20'] = data_sorted['volume'].rolling(window=20, min_periods=5).std()
                
                # 检测成交量暴增
                volume_spike_threshold = self.validation_rules['volume_rules']['max_volume_spike']
                
                volume_spikes = data_sorted[
                    (data_sorted['volume'] > data_sorted['volume_ma20'] * volume_spike_threshold) &
                    (data_sorted['volume_ma20'] > 0)
                ]
                
                for idx, row in volume_spikes.iterrows():
                    anomaly = {
                        'type': 'volume_spike',
                        'column': 'volume',
                        'index': idx,
                        'value': int(row['volume']),
                        'average': float(row['volume_ma20']),
                        'spike_ratio': float(row['volume'] / row['volume_ma20']),
                        'trade_date': str(row.get('trade_date', 'unknown')),
                        'stock_code': row.get('stock_code', 'unknown')
                    }
                    anomalies.append(anomaly)
            
            # 检测价格跳空
            if all(col in data.columns for col in ['trade_date', 'close_price', 'open_price']):
                data_sorted = data.sort_values('trade_date').copy()
                data_sorted['prev_close'] = data_sorted['close_price'].shift(1)
                data_sorted['gap_ratio'] = (data_sorted['open_price'] - data_sorted['prev_close']) / data_sorted['prev_close']
                
                # 检测异常跳空（超过5%）
                large_gaps = data_sorted[abs(data_sorted['gap_ratio']) > 0.05].dropna()
                
                for idx, row in large_gaps.iterrows():
                    anomaly = {
                        'type': 'price_gap',
                        'column': 'gap_ratio',
                        'index': idx,
                        'value': float(row['gap_ratio']),
                        'open_price': float(row['open_price']),
                        'prev_close': float(row['prev_close']),
                        'trade_date': str(row.get('trade_date', 'unknown')),
                        'stock_code': row.get('stock_code', 'unknown')
                    }
                    anomalies.append(anomaly)
        
        except Exception as e:
            self.logger.error(f"异常检测失败: {e}")
        
        return anomalies
    
    def validate_full_dataset(self, data: pd.DataFrame, stock_code: str = None) -> Dict[str, Any]:
        """
        完整数据集验证
        
        Args:
            data: 股票数据
            stock_code: 股票代码
            
        Returns:
            完整验证结果
        """
        full_results = {
            'overall_valid': True,
            'validation_time': datetime.now().isoformat(),
            'stock_code': stock_code,
            'total_records': len(data),
            'tests': {}
        }
        
        try:
            # 执行各项验证
            tests = [
                ('format_validation', self.validate_data_format),
                ('range_validation', self.validate_data_range),
                ('price_logic_check', self.check_price_logic),
                ('completeness_check', self.check_data_completeness)
            ]
            
            for test_name, test_func in tests:
                self.logger.info(f"执行{test_name}...")
                test_result = test_func(data)
                full_results['tests'][test_name] = test_result
                
                if not test_result['is_valid']:
                    full_results['overall_valid'] = False
            
            # 异常检测
            self.logger.info("执行异常检测...")
            anomalies = self.detect_anomalies(data)
            full_results['anomalies'] = {
                'count': len(anomalies),
                'details': anomalies[:50]  # 只保留前50个异常
            }
            
            # 生成验证摘要
            total_errors = sum(len(test['errors']) for test in full_results['tests'].values())
            total_warnings = sum(len(test['warnings']) for test in full_results['tests'].values())
            
            full_results['summary'] = {
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'total_anomalies': len(anomalies),
                'validation_passed': full_results['overall_valid'] and total_errors == 0
            }
        
        except Exception as e:
            full_results['overall_valid'] = False
            full_results['error'] = str(e)
            self.logger.error(f"完整验证失败: {e}")
        
        return full_results
    
    def generate_quality_report(self, validation_results: Dict[str, Any]) -> str:
        """
        生成数据质量报告
        
        Args:
            validation_results: 验证结果
            
        Returns:
            质量报告文本
        """
        report_lines = []
        
        # 报告头部
        report_lines.append("=" * 80)
        report_lines.append("数据质量报告")
        report_lines.append("=" * 80)
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"股票代码: {validation_results.get('stock_code', '未指定')}")
        report_lines.append(f"记录总数: {validation_results.get('total_records', 0)}")
        report_lines.append("")
        
        # 验证摘要
        summary = validation_results.get('summary', {})
        report_lines.append("验证摘要:")
        report_lines.append(f"  总体验证结果: {'通过' if summary.get('validation_passed', False) else '失败'}")
        report_lines.append(f"  错误数量: {summary.get('total_errors', 0)}")
        report_lines.append(f"  警告数量: {summary.get('total_warnings', 0)}")
        report_lines.append(f"  异常数量: {summary.get('total_anomalies', 0)}")
        report_lines.append("")
        
        # 详细测试结果
        tests = validation_results.get('tests', {})
        for test_name, test_result in tests.items():
            report_lines.append(f"{test_name}:")
            report_lines.append(f"  状态: {'通过' if test_result.get('is_valid', False) else '失败'}")
            
            errors = test_result.get('errors', [])
            if errors:
                report_lines.append("  错误:")
                for error in errors:
                    report_lines.append(f"    - {error}")
            
            warnings = test_result.get('warnings', [])
            if warnings:
                report_lines.append("  警告:")
                for warning in warnings:
                    report_lines.append(f"    - {warning}")
            
            report_lines.append("")
        
        # 异常详情
        anomalies = validation_results.get('anomalies', {})
        if anomalies.get('count', 0) > 0:
            report_lines.append("异常数据详情:")
            for anomaly in anomalies.get('details', [])[:10]:  # 只显示前10个
                report_lines.append(f"  - {anomaly.get('type', 'unknown')}: {anomaly.get('value', 'N/A')} "
                                  f"(日期: {anomaly.get('trade_date', 'unknown')})")
            
            if anomalies.get('count', 0) > 10:
                report_lines.append(f"  ... 还有 {anomalies.get('count', 0) - 10} 个异常")
            report_lines.append("")
        
        # 建议
        report_lines.append("建议:")
        if summary.get('total_errors', 0) > 0:
            report_lines.append("  - 修复所有数据错误后再使用数据")
        if summary.get('total_warnings', 0) > 0:
            report_lines.append("  - 关注警告信息，考虑是否需要数据清洗")
        if summary.get('total_anomalies', 0) > 0:
            report_lines.append("  - 检查异常数据，确认是否为真实市场情况")
        
        if summary.get('validation_passed', False):
            report_lines.append("  - 数据质量良好，可以正常使用")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_validation_report(self, validation_results: Dict[str, Any], 
                             report_path: str = None):
        """
        保存验证报告
        
        Args:
            validation_results: 验证结果
            report_path: 报告保存路径
        """
        if not report_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            stock_code = validation_results.get('stock_code', 'unknown')
            report_path = f"data_quality_report_{stock_code}_{timestamp}.txt"
        
        try:
            report_content = self.generate_quality_report(validation_results)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"验证报告已保存: {report_path}")
            
        except Exception as e:
            self.logger.error(f"保存验证报告失败: {e}")


def example_usage():
    """使用示例"""
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'stock_code': ['000001'] * 100,
        'trade_date': pd.date_range('2023-01-01', periods=100, freq='D'),
        'open_price': np.random.uniform(10, 15, 100),
        'high_price': np.random.uniform(12, 18, 100),
        'low_price': np.random.uniform(8, 12, 100),
        'close_price': np.random.uniform(10, 15, 100),
        'volume': np.random.randint(1000000, 10000000, 100),
        'amount': np.random.uniform(10000000, 100000000, 100)
    })
    
    # 确保价格逻辑正确
    test_data['high_price'] = np.maximum.reduce([test_data['open_price'], 
                                               test_data['close_price'], 
                                               test_data['high_price']])
    test_data['low_price'] = np.minimum.reduce([test_data['open_price'], 
                                              test_data['close_price'], 
                                              test_data['low_price']])
    
    # 添加一些异常数据进行测试
    test_data.loc[50, 'high_price'] = 1000  # 异常高价
    test_data.loc[60, 'volume'] = 0  # 零成交量
    test_data.loc[70, 'low_price'] = test_data.loc[70, 'high_price'] + 1  # 逻辑错误
    
    # 初始化验证器
    validator = DataValidator()
    
    # 执行完整验证
    print("执行数据验证...")
    results = validator.validate_full_dataset(test_data, '000001')
    
    # 生成报告
    print("\n" + "="*50)
    print("数据质量报告:")
    print("="*50)
    report = validator.generate_quality_report(results)
    print(report)
    
    # 保存报告
    validator.save_validation_report(results, 'test_validation_report.txt')


if __name__ == "__main__":
    example_usage()
