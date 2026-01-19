import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    # PostgreSQL连接配置
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', '127.0.0.1')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'cornucopia')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'admin')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'admin!@#')
    @classmethod
    def get_database_url(cls):
        """获取数据库连接URL"""
        return f"postgresql://{cls.POSTGRES_USER}:{quote_plus(cls.POSTGRES_PASSWORD)}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
    # 连接池配置
    POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
    MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
    POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))
    @classmethod
    def get_engine_config(cls):
        return {
            'pool_size': cls.POOL_SIZE,
            'max_overflow': cls.MAX_OVERFLOW,
            'pool_recycle': cls.POOL_RECYCLE,
            'echo': False,  # 设置为True可以查看SQL语句
        }
    
db_config = DatabaseConfig()
