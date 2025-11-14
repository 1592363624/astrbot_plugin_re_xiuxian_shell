import sqlite3
import os
from typing import List
from astrbot.api import logger


def run_migrations(db_path: str, migrations_path: str):
    """运行数据库迁移脚本"""
    # 确保数据库目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建 migrations 表来跟踪已应用的迁移
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 获取已应用的迁移
    cursor.execute('SELECT name FROM migrations')
    applied_migrations = {row[0] for row in cursor.fetchall()}
    
    # 获取所有迁移文件
    if not os.path.exists(migrations_path):
        os.makedirs(migrations_path)
        logger.info(f"创建迁移目录: {migrations_path}")
        return
    
    migration_files = sorted([
        f for f in os.listdir(migrations_path) 
        if f.endswith('.sql') and os.path.isfile(os.path.join(migrations_path, f))
    ])
    
    # 应用未应用的迁移
    for migration_file in migration_files:
        migration_name = migration_file
        if migration_name not in applied_migrations:
            migration_path = os.path.join(migrations_path, migration_file)
            try:
                with open(migration_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                
                # 执行迁移脚本
                cursor.executescript(sql_script)
                
                # 记录已应用的迁移
                cursor.execute(
                    'INSERT INTO migrations (name) VALUES (?)',
                    (migration_name,)
                )
                
                logger.info(f"成功应用迁移: {migration_name}")
            except Exception as e:
                logger.error(f"应用迁移 {migration_name} 失败: {e}")
                conn.rollback()
                raise
        else:
            logger.debug(f"迁移已应用，跳过: {migration_name}")
    
    # 提交更改
    conn.commit()
    conn.close()
    logger.info("数据库迁移完成")