"""
主控制器模块

统一管理A股数据采集系统的各个组件，提供完整的数据采集、
存储、验证和维护功能。支持全量采集和增量更新。
"""

import logging
import os
import sys
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import schedule
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

# 导入自定义模块
from data_fetcher import StockDataFetcher
from database_manager import DatabaseManager
from data_validator import DataValidator


class StockDataController:
    """A股数据采集系统主控制器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化主控制器
        
        Args:
            config_path: 配置文件路径（保持兼容性，但不使用）
        """
        self.config_path = config_path or "config.yaml"  # 保持兼容性
        self.config = self._load_config()
        
        # 初始化日志
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # 初始化各组件
        self._init_components()
        
        # 系统状态
        self.system_status = {
            'last_full_update': None,
            'last_incremental_update': None,
            'total_stocks': 0,
            'total_records': 0,
            'system_health': 'unknown'
        }
        
        self.logger.info("股票数据采集系统初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        # 直接使用默认配置，不依赖外部配置文件
        print("使用内置默认配置")
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            'database': {
                'type': 'sqlite',
                'path': 'stock_data.db'  # 直接在当前目录
            },
            'akshare': {
                'retry_times': 3,
                'request_delay': 0.1,
                'timeout': 30
            },
            'data_fetch': {
                'batch_size': 50,
                'max_workers': 5,
                'start_date': (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            },
            'validation': {
                'enable_anomaly_detection': True,
                'price_change_threshold': 0.2,
                'volume_spike_threshold': 5.0
            },
            'backup': {
                'enable_auto_backup': True,
                'backup_frequency': 'daily',
                'backup_retention_days': 30,
                'backup_path': '.'  # 当前目录
            },
            'logging': {
                'level': 'INFO',
                'log_file': 'stock_data.log',  # 直接在当前目录
                'max_file_size': '100MB',
                'backup_count': 5
            },
            'schedule': {
                'incremental_update_time': '16:00',  # 每日下午4点增量更新
                'backup_time': '02:00',  # 每日凌晨2点备份
                'validation_time': '03:00'  # 每日凌晨3点数据验证
            }
        }
    
    def _setup_logging(self):
        """设置日志系统"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        log_file = log_config.get('log_file', './logs/stock_data.log')
        
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:  # 如果有目录路径才创建
            os.makedirs(log_dir, exist_ok=True)
        
        # 配置日志格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # 配置文件和控制台日志
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _init_components(self):
        """初始化系统组件"""
        try:
            # 初始化数据获取器
            akshare_config = self.config.get('akshare', {})
            data_fetch_config = self.config.get('data_fetch', {})
            
            self.fetcher = StockDataFetcher(
                retry_times=akshare_config.get('retry_times', 3),
                request_delay=akshare_config.get('request_delay', 0.1),
                max_workers=data_fetch_config.get('max_workers', 5)
            )
            
            # 初始化数据库管理器
            db_config = self.config.get('database', {})
            self.db_manager = DatabaseManager(db_config)
            
            # 初始化数据验证器
            validation_config = self.config.get('validation', {})
            self.validator = DataValidator(validation_config)
            
            self.logger.info("系统组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise
    
    def initialize_system(self):
        """
        系统初始化
        包括创建必要的目录、数据表等
        """
        try:
            self.logger.info("开始系统初始化...")
            
            # 系统会根据需要自动创建必要的文件
            self.logger.debug("系统初始化中...")
            
            # 测试数据库连接
            stats = self.db_manager.get_data_statistics()
            self.logger.info(f"数据库连接成功，当前统计: {stats}")
            
            # 更新系统状态
            self._update_system_status()
            
            self.logger.info("系统初始化完成")
            
        except Exception as e:
            self.logger.error(f"系统初始化失败: {e}")
            raise
    
    def full_data_collection(self):
        """
        全量数据采集
        获取所有A股的历史数据
        """
        try:
            self.logger.info("=" * 60)
            self.logger.info("开始全量数据采集")
            self.logger.info("=" * 60)
            
            start_time = datetime.now()
            
            # 1. 获取股票列表
            self.logger.info("步骤1: 获取股票列表")
            stock_list = self.fetcher.get_stock_list()
            
            if not stock_list:
                raise ValueError("获取股票列表失败")
            
            self.logger.info(f"成功获取{len(stock_list)}只股票信息")
            
            # 保存股票基本信息
            self.db_manager.insert_stock_info(stock_list)
            
            # 2. 批量获取历史数据
            self.logger.info("步骤2: 批量获取历史数据")
            
            data_fetch_config = self.config.get('data_fetch', {})
            start_date = data_fetch_config.get('start_date', 
                                             (datetime.now() - timedelta(days=365)).strftime("%Y%m%d"))
            end_date = datetime.now().strftime("%Y%m%d")
            
            # 分批处理股票
            batch_size = data_fetch_config.get('batch_size', 50)
            stock_codes = [stock['stock_code'] for stock in stock_list]
            
            total_batches = (len(stock_codes) + batch_size - 1) // batch_size
            successful_stocks = 0
            total_records = 0
            
            for i in range(0, len(stock_codes), batch_size):
                batch_codes = stock_codes[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                self.logger.info(f"处理第{batch_num}/{total_batches}批股票 ({len(batch_codes)}只)")
                
                # 批量获取数据
                batch_data = self.fetcher.batch_fetch_data(
                    batch_codes, 
                    (start_date, end_date)
                )
                
                # 逐只股票处理和验证
                for stock_code, data in batch_data.items():
                    try:
                        if data is not None and not data.empty:
                            # 数据验证
                            validation_result = self.validator.validate_full_dataset(data, stock_code)
                            
                            if validation_result['overall_valid']:
                                # 插入数据库
                                self.db_manager.insert_stock_data(data)
                                successful_stocks += 1
                                total_records += len(data)
                                
                                # 记录日志
                                self.db_manager.log_update(
                                    'full_collection', stock_code, start_date, end_date,
                                    'SUCCESS', len(data)
                                )
                            else:
                                self.logger.warning(f"股票{stock_code}数据验证失败，跳过")
                                self.db_manager.log_update(
                                    'full_collection', stock_code, start_date, end_date,
                                    'FAILED', 0, '数据验证失败'
                                )
                        
                    except Exception as e:
                        self.logger.error(f"处理股票{stock_code}数据失败: {e}")
                        self.db_manager.log_update(
                            'full_collection', stock_code, start_date, end_date,
                            'ERROR', 0, str(e)
                        )
                
                # 进度报告
                self.logger.info(f"批次{batch_num}完成，已成功处理{successful_stocks}只股票")
            
            # 3. 生成采集报告
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info("=" * 60)
            self.logger.info("全量数据采集完成")
            self.logger.info(f"耗时: {duration}")
            self.logger.info(f"成功处理: {successful_stocks}/{len(stock_codes)}只股票")
            self.logger.info(f"总记录数: {total_records}")
            self.logger.info("=" * 60)
            
            # 更新系统状态
            self.system_status['last_full_update'] = end_time
            self.system_status['total_stocks'] = successful_stocks
            self.system_status['total_records'] = total_records
            
            # 记录全局日志
            self.db_manager.log_update(
                'full_collection', None, start_date, end_date,
                'SUCCESS', total_records
            )
            
            return {
                'success': True,
                'duration': str(duration),
                'successful_stocks': successful_stocks,
                'total_stocks': len(stock_codes),
                'total_records': total_records
            }
            
        except Exception as e:
            self.logger.error(f"全量数据采集失败: {e}")
            self.logger.error(traceback.format_exc())
            
            # 记录错误日志
            self.db_manager.log_update(
                'full_collection', None, start_date, end_date,
                'ERROR', 0, str(e)
            )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def incremental_update(self):
        """
        增量数据更新
        获取最新的交易日数据
        """
        try:
            self.logger.info("开始增量数据更新")
            start_time = datetime.now()
            
            # 获取股票列表
            stock_codes = self.db_manager.get_stock_list_from_db()
            
            if not stock_codes:
                self.logger.warning("数据库中没有股票数据，建议先执行全量采集")
                return {'success': False, 'error': '没有股票数据'}
            
            # 获取最新数据日期
            latest_date = self.db_manager.get_latest_date()
            today = datetime.now().date()
            
            if latest_date and latest_date.date() >= today:
                self.logger.info("数据已是最新，无需更新")
                return {'success': True, 'message': '数据已是最新'}
            
            # 计算需要更新的日期
            if latest_date:
                start_date = (latest_date + timedelta(days=1)).strftime("%Y%m%d")
            else:
                start_date = (today - timedelta(days=7)).strftime("%Y%m%d")  # 默认获取一周数据
            
            end_date = today.strftime("%Y%m%d")
            
            self.logger.info(f"更新日期范围: {start_date} 到 {end_date}")
            
            # 批量更新数据
            updated_stocks = 0
            total_new_records = 0
            
            batch_size = self.config.get('data_fetch', {}).get('batch_size', 50)
            
            for i in range(0, len(stock_codes), batch_size):
                batch_codes = stock_codes[i:i + batch_size]
                
                # 批量获取最新数据
                batch_data = self.fetcher.batch_fetch_data(
                    batch_codes,
                    (start_date, end_date)
                )
                
                # 处理每只股票的数据
                for stock_code, data in batch_data.items():
                    try:
                        if data is not None and not data.empty:
                            # 增量更新
                            self.db_manager.update_incremental_data(stock_code, data)
                            updated_stocks += 1
                            total_new_records += len(data)
                            
                            # 记录日志
                            self.db_manager.log_update(
                                'incremental_update', stock_code, start_date, end_date,
                                'SUCCESS', len(data)
                            )
                    
                    except Exception as e:
                        self.logger.error(f"增量更新股票{stock_code}失败: {e}")
                        self.db_manager.log_update(
                            'incremental_update', stock_code, start_date, end_date,
                            'ERROR', 0, str(e)
                        )
            
            # 完成报告
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info(f"增量更新完成，耗时: {duration}")
            self.logger.info(f"更新股票数: {updated_stocks}")
            self.logger.info(f"新增记录数: {total_new_records}")
            
            # 更新系统状态
            self.system_status['last_incremental_update'] = end_time
            
            return {
                'success': True,
                'duration': str(duration),
                'updated_stocks': updated_stocks,
                'new_records': total_new_records
            }
            
        except Exception as e:
            self.logger.error(f"增量更新失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def disaster_recovery(self, backup_path: str = None):
        """
        灾难恢复
        从备份文件恢复数据
        
        Args:
            backup_path: 备份文件路径
        """
        try:
            self.logger.info("开始灾难恢复")
            
            if not backup_path:
                # 自动寻找最新的备份文件
                backup_dir = self.config.get('backup', {}).get('backup_path', './backups')
                backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db') or f.endswith('.sql')]
                
                if not backup_files:
                    raise FileNotFoundError("没有找到备份文件")
                
                # 选择最新的备份文件
                backup_path = os.path.join(backup_dir, sorted(backup_files)[-1])
            
            self.logger.info(f"从备份恢复: {backup_path}")
            
            # 执行恢复
            self.db_manager.restore_database(backup_path)
            
            # 验证恢复结果
            stats = self.db_manager.get_data_statistics()
            self.logger.info(f"恢复完成，数据统计: {stats}")
            
            # 更新系统状态
            self._update_system_status()
            
            return {'success': True, 'backup_path': backup_path, 'stats': stats}
            
        except Exception as e:
            self.logger.error(f"灾难恢复失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def daily_maintenance(self):
        """
        日常维护任务
        包括数据验证、备份、清理等
        """
        try:
            self.logger.info("开始日常维护任务")
            
            maintenance_results = {}
            
            # 1. 数据备份
            backup_config = self.config.get('backup', {})
            if backup_config.get('enable_auto_backup', True):
                backup_path = self._create_daily_backup()
                maintenance_results['backup'] = {'success': True, 'path': backup_path}
            
            # 2. 数据验证
            validation_results = self._validate_recent_data()
            maintenance_results['validation'] = validation_results
            
            # 3. 清理旧日志和备份
            cleanup_results = self._cleanup_old_files()
            maintenance_results['cleanup'] = cleanup_results
            
            # 4. 系统健康检查
            health_check = self._system_health_check()
            maintenance_results['health_check'] = health_check
            
            # 5. 生成维护报告
            report_path = self._generate_maintenance_report(maintenance_results)
            maintenance_results['report_path'] = report_path
            
            self.logger.info("日常维护任务完成")
            
            return maintenance_results
            
        except Exception as e:
            self.logger.error(f"日常维护失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_daily_backup(self) -> str:
        """创建日常备份"""
        backup_config = self.config.get('backup', {})
        backup_dir = backup_config.get('backup_path', './backups')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f"stock_data_backup_{timestamp}.db")
        
        self.db_manager.backup_database(backup_path)
        self.logger.info(f"备份完成: {backup_path}")
        
        return backup_path
    
    def _validate_recent_data(self) -> Dict[str, Any]:
        """验证最近的数据"""
        try:
            # 获取最近一周的数据进行验证
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            # 随机选择几只股票进行验证
            stock_codes = self.db_manager.get_stock_list_from_db()
            sample_codes = stock_codes[:10] if len(stock_codes) > 10 else stock_codes
            
            validation_results = []
            
            for stock_code in sample_codes:
                data = self.db_manager.get_stock_data(stock_code, start_date, end_date)
                if not data.empty:
                    result = self.validator.validate_full_dataset(data, stock_code)
                    validation_results.append({
                        'stock_code': stock_code,
                        'is_valid': result['overall_valid'],
                        'errors': result['summary']['total_errors'],
                        'warnings': result['summary']['total_warnings']
                    })
            
            return {
                'success': True,
                'validated_stocks': len(validation_results),
                'results': validation_results
            }
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _cleanup_old_files(self) -> Dict[str, Any]:
        """清理旧文件"""
        try:
            backup_config = self.config.get('backup', {})
            retention_days = backup_config.get('backup_retention_days', 30)
            
            cleanup_results = {
                'deleted_backups': 0,
                'deleted_logs': 0,
                'freed_space': 0
            }
            
            # 清理旧备份文件
            backup_dir = backup_config.get('backup_path', './backups')
            if os.path.exists(backup_dir):
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                for file in os.listdir(backup_dir):
                    file_path = os.path.join(backup_dir, file)
                    if os.path.isfile(file_path):
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time < cutoff_date:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleanup_results['deleted_backups'] += 1
                            cleanup_results['freed_space'] += file_size
            
            self.logger.info(f"清理完成，删除{cleanup_results['deleted_backups']}个备份文件")
            
            return cleanup_results
            
        except Exception as e:
            self.logger.error(f"文件清理失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _system_health_check(self) -> Dict[str, Any]:
        """系统健康检查"""
        try:
            health_status = {
                'database_connection': False,
                'data_freshness': False,
                'disk_space': 'unknown',
                'overall_health': 'unhealthy'
            }
            
            # 检查数据库连接
            try:
                stats = self.db_manager.get_data_statistics()
                health_status['database_connection'] = True
            except:
                health_status['database_connection'] = False
            
            # 检查数据新鲜度
            latest_date = self.db_manager.get_latest_date()
            if latest_date:
                days_old = (datetime.now().date() - latest_date.date()).days
                health_status['data_freshness'] = days_old <= 3  # 3天内为新鲜
                health_status['days_since_update'] = days_old
            
            # 简单的磁盘空间检查
            try:
                import shutil
                disk_usage = shutil.disk_usage('.')
                free_gb = disk_usage.free / (1024**3)
                health_status['disk_space'] = f"{free_gb:.1f}GB"
                health_status['disk_space_sufficient'] = free_gb > 1  # 至少1GB空闲
            except:
                pass
            
            # 综合健康状态
            if (health_status['database_connection'] and 
                health_status['data_freshness']):
                health_status['overall_health'] = 'healthy'
            elif health_status['database_connection']:
                health_status['overall_health'] = 'warning'
            else:
                health_status['overall_health'] = 'critical'
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return {'overall_health': 'error', 'error': str(e)}
    
    def _generate_maintenance_report(self, maintenance_results: Dict[str, Any]) -> str:
        """生成维护报告"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = f"maintenance_report_{timestamp}.txt"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("股票数据系统维护报告\n")
                f.write("=" * 80 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 备份结果
                if 'backup' in maintenance_results:
                    f.write("备份任务:\n")
                    backup_result = maintenance_results['backup']
                    if backup_result.get('success'):
                        f.write(f"  ✓ 备份成功: {backup_result['path']}\n")
                    else:
                        f.write(f"  ✗ 备份失败: {backup_result.get('error', 'unknown error')}\n")
                    f.write("\n")
                
                # 验证结果
                if 'validation' in maintenance_results:
                    f.write("数据验证:\n")
                    validation_result = maintenance_results['validation']
                    if validation_result.get('success'):
                        f.write(f"  验证股票数: {validation_result['validated_stocks']}\n")
                        for result in validation_result['results']:
                            status = "✓" if result['is_valid'] else "✗"
                            f.write(f"  {status} {result['stock_code']}: "
                                  f"错误{result['errors']}, 警告{result['warnings']}\n")
                    else:
                        f.write(f"  ✗ 验证失败: {validation_result.get('error', 'unknown error')}\n")
                    f.write("\n")
                
                # 健康检查
                if 'health_check' in maintenance_results:
                    f.write("系统健康检查:\n")
                    health = maintenance_results['health_check']
                    f.write(f"  整体状态: {health.get('overall_health', 'unknown')}\n")
                    f.write(f"  数据库连接: {'正常' if health.get('database_connection') else '异常'}\n")
                    f.write(f"  数据新鲜度: {'正常' if health.get('data_freshness') else '过期'}\n")
                    if 'days_since_update' in health:
                        f.write(f"  距离上次更新: {health['days_since_update']}天\n")
                    f.write("\n")
                
                f.write("=" * 80 + "\n")
            
            return report_path
            
        except Exception as e:
            self.logger.error(f"生成维护报告失败: {e}")
            return ""
    
    def _update_system_status(self):
        """更新系统状态"""
        try:
            stats = self.db_manager.get_data_statistics()
            self.system_status.update({
                'total_stocks': stats.get('total_stocks', 0),
                'total_records': stats.get('total_records', 0),
                'system_health': 'healthy'
            })
        except:
            self.system_status['system_health'] = 'unknown'
    
    def setup_scheduler(self):
        """设置定时任务调度器"""
        try:
            schedule_config = self.config.get('schedule', {})
            
            # 增量更新任务
            update_time = schedule_config.get('incremental_update_time', '16:00')
            schedule.every().day.at(update_time).do(self.incremental_update)
            
            # 备份任务
            backup_time = schedule_config.get('backup_time', '02:00')
            schedule.every().day.at(backup_time).do(self._create_daily_backup)
            
            # 维护任务
            maintenance_time = schedule_config.get('validation_time', '03:00')
            schedule.every().day.at(maintenance_time).do(self.daily_maintenance)
            
            self.logger.info("定时任务调度器设置完成")
            self.logger.info(f"增量更新时间: {update_time}")
            self.logger.info(f"备份时间: {backup_time}")
            self.logger.info(f"维护时间: {maintenance_time}")
            
        except Exception as e:
            self.logger.error(f"设置定时任务失败: {e}")
    
    def run_scheduler(self):
        """运行定时任务调度器"""
        self.logger.info("启动定时任务调度器")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            self.logger.info("定时任务调度器已停止")
        except Exception as e:
            self.logger.error(f"定时任务调度器运行异常: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            系统状态字典
        """
        self._update_system_status()
        
        return {
            'system_status': self.system_status,
            'database_stats': self.db_manager.get_data_statistics(),
            'latest_date': str(self.db_manager.get_latest_date()) if self.db_manager.get_latest_date() else None
        }
    
    def close(self):
        """关闭系统资源"""
        try:
            if hasattr(self, 'db_manager'):
                self.db_manager.close()
            self.logger.info("系统资源已释放")
        except Exception as e:
            self.logger.error(f"关闭系统资源失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='A股数据采集系统')
    parser.add_argument('--action', choices=['init', 'full', 'update', 'recovery', 'maintenance', 'status', 'schedule'], 
                       default='status', help='执行操作')
    parser.add_argument('--backup-path', help='恢复备份文件路径')
    
    args = parser.parse_args()
    
    # 初始化控制器（使用内置配置）
    controller = StockDataController()
    
    try:
        if args.action == 'init':
            print("初始化系统...")
            controller.initialize_system()
            print("系统初始化完成")
            
        elif args.action == 'full':
            print("开始全量数据采集...")
            result = controller.full_data_collection()
            if result['success']:
                print(f"全量采集完成: {result['successful_stocks']}/{result['total_stocks']}只股票")
            else:
                print(f"全量采集失败: {result['error']}")
                
        elif args.action == 'update':
            print("开始增量更新...")
            result = controller.incremental_update()
            if result['success']:
                print(f"增量更新完成: 更新{result['updated_stocks']}只股票，新增{result['new_records']}条记录")
            else:
                print(f"增量更新失败: {result['error']}")
                
        elif args.action == 'recovery':
            print("开始灾难恢复...")
            result = controller.disaster_recovery(args.backup_path)
            if result['success']:
                print(f"恢复完成: {result['stats']}")
            else:
                print(f"恢复失败: {result['error']}")
                
        elif args.action == 'maintenance':
            print("开始日常维护...")
            result = controller.daily_maintenance()
            print(f"维护完成，报告: {result.get('report_path', 'N/A')}")
            
        elif args.action == 'status':
            print("系统状态:")
            status = controller.get_system_status()
            print(f"  总股票数: {status['database_stats'].get('total_stocks', 0)}")
            print(f"  总记录数: {status['database_stats'].get('total_records', 0)}")
            print(f"  最新日期: {status['latest_date']}")
            print(f"  系统健康: {status['system_status']['system_health']}")
            
        elif args.action == 'schedule':
            print("启动定时任务...")
            controller.setup_scheduler()
            controller.run_scheduler()
            
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"执行失败: {e}")
    finally:
        controller.close()


if __name__ == "__main__":
    main()
