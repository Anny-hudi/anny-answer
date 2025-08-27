"""
数据库管理
支持多种数据库的股票数据存储和查询
"""

import sqlite3
import pandas as pd
import logging
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import pymysql
import psycopg2
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Date, Numeric, DateTime, BigInteger
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import json


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_config: Dict[str, Any]):
        # 初始化数据库配置
        self.db_config = db_config
        self.db_type = db_config.get('type', 'sqlite')
        self.engine = None
        self.connection = None
        self.session = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 连接数据库
        self._init_connection()
        
        # 建表
        self.create_tables()
    
    def _init_connection(self):
        """连接数据库"""
        try:
            if self.db_type.lower() == 'sqlite':
                db_path = self.db_config.get('path', './stock_data.db')
                # 创建目录
                os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
                
                connection_string = f"sqlite:///{db_path}"
                
            elif self.db_type.lower() == 'mysql':
                host = self.db_config.get('host', 'localhost')
                port = self.db_config.get('port', 3306)
                username = self.db_config.get('username', 'root')
                password = self.db_config.get('password', '')
                database = self.db_config.get('database', 'stock_market')
                
                connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset=utf8mb4"
                
            elif self.db_type.lower() == 'postgresql':
                host = self.db_config.get('host', 'localhost')
                port = self.db_config.get('port', 5432)
                username = self.db_config.get('username', 'postgres')
                password = self.db_config.get('password', '')
                database = self.db_config.get('database', 'stock_market')
                
                connection_string = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
            
            else:
                raise ValueError(f"不支持的数据库类型: {self.db_type}")
            
            # 创建数据库引擎
            self.engine = create_engine(connection_string, echo=False)
            
            # 创建会话
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            
            self.logger.info(f"成功连接到{self.db_type}数据库")
            
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            raise
    
    def create_tables(self):
        """建表"""
        try:
            # 股票信息表
            stock_info_sql = """
            CREATE TABLE IF NOT EXISTS stock_info (
                stock_code VARCHAR(10) PRIMARY KEY,
                stock_name VARCHAR(50) NOT NULL,
                market VARCHAR(10) NOT NULL,
                listing_date DATE,
                industry VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            # 行情数据表
            if self.db_type.lower() == 'sqlite':
                daily_quotes_sql = """
                CREATE TABLE IF NOT EXISTS daily_quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code VARCHAR(10) NOT NULL,
                    trade_date DATE NOT NULL,
                    open_price DECIMAL(10,2),
                    high_price DECIMAL(10,2),
                    low_price DECIMAL(10,2),
                    close_price DECIMAL(10,2),
                    volume BIGINT,
                    amount DECIMAL(20,2),
                    turnover_rate DECIMAL(8,4),
                    change_pct DECIMAL(8,4),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(stock_code, trade_date)
                )
                """
                
                # 索引
                indexes_sql = [
                    "CREATE INDEX IF NOT EXISTS idx_stock_code ON daily_quotes(stock_code)",
                    "CREATE INDEX IF NOT EXISTS idx_trade_date ON daily_quotes(trade_date)",
                    "CREATE INDEX IF NOT EXISTS idx_stock_date ON daily_quotes(stock_code, trade_date)"
                ]
                
            else:
                daily_quotes_sql = """
                CREATE TABLE IF NOT EXISTS daily_quotes (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    stock_code VARCHAR(10) NOT NULL,
                    trade_date DATE NOT NULL,
                    open_price DECIMAL(10,2),
                    high_price DECIMAL(10,2),
                    low_price DECIMAL(10,2),
                    close_price DECIMAL(10,2),
                    volume BIGINT,
                    amount DECIMAL(20,2),
                    turnover_rate DECIMAL(8,4),
                    change_pct DECIMAL(8,4),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_stock_date (stock_code, trade_date),
                    INDEX idx_trade_date (trade_date),
                    INDEX idx_stock_code (stock_code)
                )
                """
                
                indexes_sql = []
            
            # 日志表
            update_logs_sql = """
            CREATE TABLE IF NOT EXISTS update_logs (
                id INTEGER PRIMARY KEY {},
                update_type VARCHAR(20) NOT NULL,
                stock_code VARCHAR(10),
                start_date DATE,
                end_date DATE,
                status VARCHAR(20) NOT NULL,
                records_count INTEGER,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """.format("AUTOINCREMENT" if self.db_type.lower() == 'sqlite' else "AUTO_INCREMENT")
            
            # 执行SQL
            with self.engine.connect() as conn:
                conn.execute(text(stock_info_sql))
                conn.execute(text(daily_quotes_sql))
                conn.execute(text(update_logs_sql))
                conn.commit()
                
                # 建索引
                for index_sql in indexes_sql:
                    try:
                        conn.execute(text(index_sql))
                    except Exception as e:
                        self.logger.warning(f"建索引失败: {e}")
                
                conn.commit()
            
            self.logger.info("建表完成")
            
        except Exception as e:
            self.logger.error(f"建表失败: {e}")
            raise
    
    def insert_stock_info(self, stock_list: List[Dict[str, str]]):
        """插入股票基本信息"""
        try:
            # 转为DataFrame
            df = pd.DataFrame(stock_list)
            
            # 加时间戳
            df['created_at'] = datetime.now()
            df['updated_at'] = datetime.now()
            
            # 存入数据库
            df.to_sql('stock_info', self.engine, if_exists='replace', index=False, method='multi')
            
            self.logger.info(f"插入{len(stock_list)}条股票信息")
            
        except Exception as e:
            self.logger.error(f"插入股票信息失败: {e}")
            raise
    
    def insert_stock_data(self, data: pd.DataFrame, batch_size: int = 1000):
        """插入股票数据"""
        try:
            if data.empty:
                self.logger.warning("数据为空，跳过插入")
                return
            
            # 数据预处理
            data = self._prepare_data_for_insert(data)
            
            # 批量入库
            total_records = len(data)
            inserted_records = 0
            
            for i in range(0, total_records, batch_size):
                batch_data = data.iloc[i:i+batch_size]
                
                # 处理重复数据
                if self.db_type.lower() == 'sqlite':
                    batch_data.to_sql('daily_quotes', self.engine, if_exists='append', 
                                    index=False, method='multi')
                else:
                    # MySQL/PostgreSQL用upsert
                    self._upsert_data(batch_data)
                
                inserted_records += len(batch_data)
                
                if inserted_records % 10000 == 0:
                    self.logger.info(f"已插入{inserted_records}/{total_records}条记录")
            
            self.logger.info(f"插入{inserted_records}条数据")
            
        except Exception as e:
            self.logger.error(f"插入股票数据失败: {e}")
            raise
    
    def _prepare_data_for_insert(self, data: pd.DataFrame) -> pd.DataFrame:
        """数据预处理"""
        # 复制数据
        prepared_data = data.copy()
        
        # 检查必要字段
        required_columns = ['stock_code', 'trade_date', 'open_price', 'high_price', 
                          'low_price', 'close_price', 'volume', 'amount']
        
        for col in required_columns:
            if col not in prepared_data.columns:
                if col == 'stock_code':
                    raise ValueError("必须包含stock_code列")
                elif col == 'trade_date':
                    raise ValueError("必须包含trade_date列")
                else:
                    prepared_data[col] = None
        
        # 类型转换
        prepared_data['trade_date'] = pd.to_datetime(prepared_data['trade_date']).dt.date
        
        # 加时间戳
        prepared_data['created_at'] = datetime.now()
        
        # 去重
        prepared_data = prepared_data.drop_duplicates(subset=['stock_code', 'trade_date'])
        
        return prepared_data
    
    def _upsert_data(self, data: pd.DataFrame):
        """upsert操作（插入或更新）"""
        # 这里简化处理，先删除再插入
        with self.engine.connect() as conn:
            for _, row in data.iterrows():
                # 删除可能存在的记录
                delete_sql = text("""
                    DELETE FROM daily_quotes 
                    WHERE stock_code = :stock_code AND trade_date = :trade_date
                """)
                conn.execute(delete_sql, {
                    'stock_code': row['stock_code'],
                    'trade_date': row['trade_date']
                })
            
            conn.commit()
        
        # 插入新数据
        data.to_sql('daily_quotes', self.engine, if_exists='append', index=False)
    
    def update_incremental_data(self, stock_code: str, data: pd.DataFrame):
        """增量更新数据"""
        try:
            # 获取数据库中该股票的最新日期
            latest_date = self.get_latest_date(stock_code)
            
            if latest_date:
                # 过滤出新于最新日期的数据
                data['trade_date'] = pd.to_datetime(data['trade_date'])
                new_data = data[data['trade_date'] > latest_date]
            else:
                new_data = data
            
            if not new_data.empty:
                self.insert_stock_data(new_data)
                self.logger.info(f"股票{stock_code}增量更新{len(new_data)}条记录")
            else:
                self.logger.info(f"股票{stock_code}无新数据需要更新")
                
        except Exception as e:
            self.logger.error(f"增量更新失败: {e}")
            raise
    
    def get_latest_date(self, stock_code: str = None) -> Optional[datetime]:
        """获取最新数据日期"""
        try:
            if stock_code:
                sql = text("""
                    SELECT MAX(trade_date) as latest_date 
                    FROM daily_quotes 
                    WHERE stock_code = :stock_code
                """)
                params = {'stock_code': stock_code}
            else:
                sql = text("SELECT MAX(trade_date) as latest_date FROM daily_quotes")
                params = {}
            
            with self.engine.connect() as conn:
                result = conn.execute(sql, params).fetchone()
                
                if result and result[0]:
                    return result[0] if isinstance(result[0], datetime) else datetime.strptime(str(result[0]), '%Y-%m-%d')
                
            return None
            
        except Exception as e:
            self.logger.error(f"获取最新日期失败: {e}")
            return None
    
    def get_stock_data(self, stock_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """查询股票数据"""
        try:
            sql = "SELECT * FROM daily_quotes WHERE stock_code = :stock_code"
            params = {'stock_code': stock_code}
            
            if start_date:
                sql += " AND trade_date >= :start_date"
                params['start_date'] = start_date
            
            if end_date:
                sql += " AND trade_date <= :end_date"
                params['end_date'] = end_date
            
            sql += " ORDER BY trade_date"
            
            return pd.read_sql(text(sql), self.engine, params=params)
            
        except Exception as e:
            self.logger.error(f"查询股票数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_list_from_db(self) -> List[str]:
        """
        从数据库获取股票列表
        
        Returns:
            股票代码列表
        """
        try:
            sql = "SELECT DISTINCT stock_code FROM daily_quotes ORDER BY stock_code"
            
            with self.engine.connect() as conn:
                result = conn.execute(text(sql)).fetchall()
                return [row[0] for row in result]
                
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            return []
    
    def count_records(self, stock_code: str = None) -> int:
        """统计记录数量"""
        try:
            if stock_code:
                sql = text("SELECT COUNT(*) FROM daily_quotes WHERE stock_code = :stock_code")
                params = {'stock_code': stock_code}
            else:
                sql = text("SELECT COUNT(*) FROM daily_quotes")
                params = {}
            
            with self.engine.connect() as conn:
                result = conn.execute(sql, params).fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            self.logger.error(f"统计记录数量失败: {e}")
            return 0
    
    def count_stocks(self) -> int:
        """统计股票数量"""
        try:
            sql = text("SELECT COUNT(DISTINCT stock_code) FROM daily_quotes")
            
            with self.engine.connect() as conn:
                result = conn.execute(sql).fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            self.logger.error(f"统计股票数量失败: {e}")
            return 0
    
    def count_trading_days(self) -> int:
        """统计交易日数量"""
        try:
            sql = text("SELECT COUNT(DISTINCT trade_date) FROM daily_quotes")
            
            with self.engine.connect() as conn:
                result = conn.execute(sql).fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            self.logger.error(f"统计交易日数量失败: {e}")
            return 0
    
    def backup_database(self, backup_path: str):
        """备份数据库"""
        try:
            # 确保备份目录存在
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            if self.db_type.lower() == 'sqlite':
                # SQLite直接复制文件
                db_path = self.db_config.get('path', './stock_data.db')
                shutil.copy2(db_path, backup_path)
            else:
                # 其他数据库导出为SQL文件或CSV文件
                self._export_to_csv(backup_path)
            
            self.logger.info(f"数据库备份完成: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"数据库备份失败: {e}")
            raise
    
    def _export_to_csv(self, backup_dir: str):
        """导出数据为CSV文件"""
        # 导出股票信息
        stock_info_df = pd.read_sql("SELECT * FROM stock_info", self.engine)
        stock_info_df.to_csv(os.path.join(backup_dir, 'stock_info.csv'), index=False)
        
        # 导出行情数据
        daily_quotes_df = pd.read_sql("SELECT * FROM daily_quotes", self.engine)
        daily_quotes_df.to_csv(os.path.join(backup_dir, 'daily_quotes.csv'), index=False)
        
        # 导出日志数据
        try:
            logs_df = pd.read_sql("SELECT * FROM update_logs", self.engine)
            logs_df.to_csv(os.path.join(backup_dir, 'update_logs.csv'), index=False)
        except:
            pass
    
    def restore_database(self, backup_path: str):
        """
        从备份恢复数据库
        
        Args:
            backup_path: 备份路径
        """
        try:
            if self.db_type.lower() == 'sqlite':
                # SQLite直接复制文件
                db_path = self.db_config.get('path', './stock_data.db')
                shutil.copy2(backup_path, db_path)
                # 重新初始化连接
                self._init_connection()
            else:
                # 从CSV文件恢复
                self._restore_from_csv(backup_path)
            
            self.logger.info(f"数据库恢复完成: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"数据库恢复失败: {e}")
            raise
    
    def _restore_from_csv(self, backup_dir: str):
        """从CSV文件恢复数据"""
        # 清空现有数据
        with self.engine.connect() as conn:
            conn.execute(text("DELETE FROM daily_quotes"))
            conn.execute(text("DELETE FROM stock_info"))
            conn.execute(text("DELETE FROM update_logs"))
            conn.commit()
        
        # 恢复股票信息
        stock_info_file = os.path.join(backup_dir, 'stock_info.csv')
        if os.path.exists(stock_info_file):
            stock_info_df = pd.read_csv(stock_info_file)
            stock_info_df.to_sql('stock_info', self.engine, if_exists='append', index=False)
        
        # 恢复行情数据
        daily_quotes_file = os.path.join(backup_dir, 'daily_quotes.csv')
        if os.path.exists(daily_quotes_file):
            daily_quotes_df = pd.read_csv(daily_quotes_file)
            daily_quotes_df.to_sql('daily_quotes', self.engine, if_exists='append', index=False)
    
    def log_update(self, update_type: str, stock_code: str = None, 
                  start_date: str = None, end_date: str = None,
                  status: str = 'SUCCESS', records_count: int = 0, 
                  error_message: str = None):
        """记录更新日志"""
        try:
            log_data = {
                'update_type': update_type,
                'stock_code': stock_code,
                'start_date': start_date,
                'end_date': end_date,
                'status': status,
                'records_count': records_count,
                'error_message': error_message,
                'created_at': datetime.now()
            }
            
            log_df = pd.DataFrame([log_data])
            log_df.to_sql('update_logs', self.engine, if_exists='append', index=False)
            
        except Exception as e:
            self.logger.error(f"记录日志失败: {e}")
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        try:
            stats = {}
            
            # 基本统计
            stats['total_stocks'] = self.count_stocks()
            stats['total_records'] = self.count_records()
            stats['trading_days'] = self.count_trading_days()
            
            # 日期范围
            with self.engine.connect() as conn:
                date_range = conn.execute(text("""
                    SELECT MIN(trade_date) as min_date, MAX(trade_date) as max_date 
                    FROM daily_quotes
                """)).fetchone()
                
                if date_range:
                    stats['date_range'] = {
                        'start_date': str(date_range[0]) if date_range[0] else None,
                        'end_date': str(date_range[1]) if date_range[1] else None
                    }
                
                # 市场分布
                market_dist = conn.execute(text("""
                    SELECT market, COUNT(*) as count 
                    FROM stock_info 
                    GROUP BY market
                """)).fetchall()
                
                stats['market_distribution'] = {row[0]: row[1] for row in market_dist}
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def close(self):
        """关闭数据库连接"""
        try:
            if self.session:
                self.session.close()
            if self.engine:
                self.engine.dispose()
            self.logger.info("数据库连接已关闭")
        except Exception as e:
            self.logger.error(f"关闭数据库连接失败: {e}")


def example_usage():
    """测试代码"""
    
    # SQLite配置
    sqlite_config = {
        'type': 'sqlite',
        'path': './data/stock_data.db'
    }
    
    # MySQL配置示例
    mysql_config = {
        'type': 'mysql',
        'host': 'localhost',
        'port': 3306,
        'username': 'root',
        'password': 'password',
        'database': 'stock_market'
    }
    
    # 初始化数据库管理器
    db_manager = DatabaseManager(sqlite_config)
    
    # 插入测试数据
    test_stock_info = [
        {'stock_code': '000001', 'stock_name': '平安银行', 'market': 'SZ'},
        {'stock_code': '000002', 'stock_name': '万科A', 'market': 'SZ'}
    ]
    
    db_manager.insert_stock_info(test_stock_info)
    
    # 创建测试行情数据
    test_data = pd.DataFrame({
        'stock_code': ['000001', '000001'],
        'trade_date': ['2023-01-01', '2023-01-02'],
        'open_price': [10.0, 10.5],
        'high_price': [10.5, 11.0],
        'low_price': [9.8, 10.2],
        'close_price': [10.2, 10.8],
        'volume': [1000000, 1200000],
        'amount': [10200000, 12960000]
    })
    
    db_manager.insert_stock_data(test_data)
    
    # 查询数据
    result = db_manager.get_stock_data('000001')
    print("查询结果:")
    print(result)
    
    # 获取统计信息
    stats = db_manager.get_data_statistics()
    print("\n统计信息:")
    print(stats)
    
    # 关闭连接
    db_manager.close()


if __name__ == "__main__":
    example_usage()
