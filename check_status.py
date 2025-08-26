#!/usr/bin/env python3
"""
检查数据采集状态脚本
"""

from database_manager import DatabaseManager
import sys

def check_status():
    try:
        # 连接数据库
        db_config = {'type': 'sqlite', 'path': './data/stock_data.db'}
        db = DatabaseManager(db_config)
        
        # 获取统计信息
        stats = db.get_data_statistics()
        
        print("=" * 60)
        print("📊 当前数据采集状态")
        print("=" * 60)
        print(f"已采集股票数: {stats['total_stocks']}")
        print(f"总记录数: {stats['total_records']:,}")
        print(f"交易日数: {stats['trading_days']}")
        
        if stats['date_range']['start_date']:
            print(f"数据日期范围: {stats['date_range']['start_date']} 到 {stats['date_range']['end_date']}")
        
        # 市场分布
        if stats.get('market_distribution'):
            print(f"市场分布: {stats['market_distribution']}")
        
        # 获取最新数据日期
        latest_date = db.get_latest_date()
        if latest_date:
            print(f"最新数据日期: {latest_date.strftime('%Y-%m-%d')}")
        
        # 检查部分股票的数据
        stock_list = db.get_stock_list_from_db()
        if stock_list:
            print(f"数据库中股票列表样例: {stock_list[:10]}...")
            
            # 检查第一只股票的记录数
            first_stock = stock_list[0]
            count = db.count_records(first_stock)
            print(f"股票 {first_stock} 的记录数: {count}")
        
        print("=" * 60)
        
        db.close()
        
        return {
            'total_stocks': stats['total_stocks'],
            'total_records': stats['total_records'],
            'has_data': stats['total_stocks'] > 0
        }
        
    except Exception as e:
        print(f"❌ 检查状态失败: {e}")
        return {'has_data': False}

if __name__ == "__main__":
    result = check_status()
    sys.exit(0 if result['has_data'] else 1)
