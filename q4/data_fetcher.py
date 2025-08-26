"""
A股数据获取模块

使用akshare库获取A股市场数据，支持历史数据和增量更新。
提供完善的错误处理和重试机制。
"""

import akshare as ak
import pandas as pd
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import BoundedSemaphore
import requests


class StockDataFetcher:
    """股票数据获取器"""
    
    def __init__(self, retry_times: int = 3, request_delay: float = 0.1, max_workers: int = 5):
        """
        初始化数据获取器
        
        Args:
            retry_times: 重试次数
            request_delay: 请求延迟（秒）
            max_workers: 最大并发数
        """
        self.retry_times = retry_times
        self.request_delay = request_delay
        self.max_workers = max_workers
        self.semaphore = BoundedSemaphore(max_workers)
        self.stock_list = []
        
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def get_stock_list(self) -> List[Dict[str, str]]:
        """
        获取全A股股票列表
        
        Returns:
            股票列表，包含股票代码、名称等信息
        """
        try:
            self.logger.info("开始获取A股股票列表...")
            
            # 获取沪深A股基本信息
            stock_info = ak.stock_info_a_code_name()
            
            # 数据清洗和格式化
            stock_list = []
            for _, row in stock_info.iterrows():
                stock_data = {
                    'stock_code': row['code'],
                    'stock_name': row['name'],
                    'market': 'SH' if row['code'].startswith('6') else 'SZ'
                }
                stock_list.append(stock_data)
            
            self.stock_list = stock_list
            self.logger.info(f"成功获取{len(stock_list)}只A股股票信息")
            
            return stock_list
            
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_historical_data(self, stock_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        获取单只股票的历史行情数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            历史行情数据DataFrame
        """
        for attempt in range(self.retry_times):
            try:
                # 添加请求延迟，避免被限制
                time.sleep(self.request_delay)
                
                # 获取历史数据
                data = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust=""
                )
                
                if data.empty:
                    self.logger.warning(f"股票{stock_code}在{start_date}-{end_date}期间无数据")
                    return None
                
                # 数据清洗和标准化
                data = self._clean_stock_data(data, stock_code)
                
                self.logger.debug(f"成功获取股票{stock_code}历史数据，共{len(data)}条记录")
                return data
                
            except Exception as e:
                self.logger.warning(f"获取股票{stock_code}数据失败(第{attempt+1}次): {e}")
                if attempt < self.retry_times - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    self.logger.error(f"股票{stock_code}数据获取最终失败")
                    return None
    
    def get_latest_data(self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        获取最新交易日数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            最新交易日数据DataFrame
        """
        today = datetime.now().strftime("%Y%m%d")
        # 获取最近5个交易日的数据，确保能获取到最新数据
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")
        
        data = self.get_historical_data(stock_code, start_date, today)
        
        if data is not None and not data.empty:
            # 返回最新一条记录
            return data.tail(1)
        
        return None
    
    def batch_fetch_data(self, stock_codes: List[str], date_range: Tuple[str, str]) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票的历史数据
        
        Args:
            stock_codes: 股票代码列表
            date_range: 日期范围 (start_date, end_date)
            
        Returns:
            股票代码到数据的映射字典
        """
        start_date, end_date = date_range
        results = {}
        
        self.logger.info(f"开始批量获取{len(stock_codes)}只股票的数据...")
        
        # 使用线程池并发获取数据
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任务
            future_to_code = {
                executor.submit(self._fetch_single_stock_with_semaphore, code, start_date, end_date): code
                for code in stock_codes
            }
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_code):
                stock_code = future_to_code[future]
                try:
                    data = future.result()
                    if data is not None and not data.empty:
                        results[stock_code] = data
                    
                    completed += 1
                    if completed % 100 == 0:
                        self.logger.info(f"已完成{completed}/{len(stock_codes)}只股票数据获取")
                        
                except Exception as e:
                    self.logger.error(f"获取股票{stock_code}数据异常: {e}")
        
        self.logger.info(f"批量获取完成，成功获取{len(results)}只股票数据")
        return results
    
    def _fetch_single_stock_with_semaphore(self, stock_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        使用信号量限制并发的单股票数据获取
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            股票数据DataFrame
        """
        with self.semaphore:
            return self.get_historical_data(stock_code, start_date, end_date)
    
    def _clean_stock_data(self, data: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """
        清洗和标准化股票数据
        
        Args:
            data: 原始股票数据
            stock_code: 股票代码
            
        Returns:
            清洗后的数据
        """
        # 复制数据避免修改原始数据
        cleaned_data = data.copy()
        
        # 添加股票代码列
        cleaned_data['stock_code'] = stock_code
        
        # 重命名列名为英文标准格式
        column_mapping = {
            '日期': 'trade_date',
            '开盘': 'open_price',
            '收盘': 'close_price',
            '最高': 'high_price',
            '最低': 'low_price',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'change_pct',
            '涨跌额': 'change_amount',
            '换手率': 'turnover_rate'
        }
        
        cleaned_data = cleaned_data.rename(columns=column_mapping)
        
        # 确保日期列为datetime格式
        if 'trade_date' in cleaned_data.columns:
            cleaned_data['trade_date'] = pd.to_datetime(cleaned_data['trade_date'])
        
        # 确保数值列为正确的数据类型
        numeric_columns = ['open_price', 'close_price', 'high_price', 'low_price', 'volume', 'amount']
        for col in numeric_columns:
            if col in cleaned_data.columns:
                cleaned_data[col] = pd.to_numeric(cleaned_data[col], errors='coerce')
        
        # 移除包含空值的行
        cleaned_data = cleaned_data.dropna(subset=numeric_columns)
        
        # 重新排序列
        column_order = ['stock_code', 'trade_date', 'open_price', 'high_price', 'low_price', 
                       'close_price', 'volume', 'amount', 'turnover_rate', 'change_pct']
        
        available_columns = [col for col in column_order if col in cleaned_data.columns]
        cleaned_data = cleaned_data[available_columns]
        
        return cleaned_data
    
    def get_trading_calendar(self, start_date: str, end_date: str) -> List[str]:
        """
        获取交易日历
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            交易日列表
        """
        try:
            # 获取交易日历
            calendar = ak.tool_trade_date_hist_sina()
            
            # 筛选日期范围
            start_dt = datetime.strptime(start_date, "%Y%m%d")
            end_dt = datetime.strptime(end_date, "%Y%m%d")
            
            trading_days = []
            for date_str in calendar['trade_date']:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                if start_dt <= date_obj <= end_dt:
                    trading_days.append(date_obj.strftime("%Y%m%d"))
            
            return sorted(trading_days)
            
        except Exception as e:
            self.logger.error(f"获取交易日历失败: {e}")
            # 备用方案：生成工作日
            return self._generate_workdays(start_date, end_date)
    
    def _generate_workdays(self, start_date: str, end_date: str) -> List[str]:
        """
        生成工作日列表（周一到周五）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            工作日列表
        """
        start_dt = datetime.strptime(start_date, "%Y%m%d")
        end_dt = datetime.strptime(end_date, "%Y%m%d")
        
        workdays = []
        current_date = start_dt
        
        while current_date <= end_dt:
            # 周一到周五（0-4）
            if current_date.weekday() < 5:
                workdays.append(current_date.strftime("%Y%m%d"))
            current_date += timedelta(days=1)
        
        return workdays
    
    def get_stock_info_detail(self, stock_code: str) -> Optional[Dict]:
        """
        获取股票详细信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票详细信息字典
        """
        try:
            # 获取股票基本信息
            info = ak.stock_individual_info_em(symbol=stock_code)
            
            if info.empty:
                return None
            
            # 解析信息
            stock_info = {}
            for _, row in info.iterrows():
                key = row['item']
                value = row['value']
                stock_info[key] = value
            
            return stock_info
            
        except Exception as e:
            self.logger.error(f"获取股票{stock_code}详细信息失败: {e}")
            return None
    
    def validate_stock_code(self, stock_code: str) -> bool:
        """
        验证股票代码格式
        
        Args:
            stock_code: 股票代码
            
        Returns:
            是否为有效的股票代码
        """
        # A股股票代码规则
        if len(stock_code) != 6:
            return False
        
        if not stock_code.isdigit():
            return False
        
        # 沪市：60开头，科创板：68开头
        # 深市：00开头（主板），30开头（创业板），20开头（B股）
        valid_prefixes = ['60', '68', '00', '30', '20']
        
        return any(stock_code.startswith(prefix) for prefix in valid_prefixes)


def example_usage():
    """使用示例"""
    
    # 初始化数据获取器
    fetcher = StockDataFetcher(retry_times=3, request_delay=0.1, max_workers=5)
    
    # 获取股票列表
    print("获取股票列表...")
    stock_list = fetcher.get_stock_list()
    print(f"共获取{len(stock_list)}只股票")
    
    # 获取单只股票历史数据
    print("\n获取单只股票数据...")
    start_date = "20230101"
    end_date = "20231231"
    data = fetcher.get_historical_data("000001", start_date, end_date)
    if data is not None:
        print(f"平安银行(000001)数据预览:")
        print(data.head())
    
    # 批量获取数据（示例：前10只股票）
    print("\n批量获取数据...")
    sample_codes = [stock['stock_code'] for stock in stock_list[:10]]
    batch_data = fetcher.batch_fetch_data(sample_codes, (start_date, end_date))
    print(f"批量获取完成，成功获取{len(batch_data)}只股票数据")
    
    # 获取交易日历
    print("\n获取交易日历...")
    trading_days = fetcher.get_trading_calendar(start_date, end_date)
    print(f"2023年共有{len(trading_days)}个交易日")


if __name__ == "__main__":
    example_usage()
