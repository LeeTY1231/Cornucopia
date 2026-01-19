from data import *

logger = logging.getLogger(__name__)

class DataManager:
    """数据库管理器类"""
    
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def initialize(self):
        """初始化数据库连接"""
        try:
            # 创建数据库引擎
            db_url = config.db_config.get_database_url()
            engine_config = config.db_config.get_engine_config()
            
            self._engine = create_engine(db_url, **engine_config)
            
            # 创建会话工厂
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            
            logger.info("数据库连接初始化成功")
            
        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}")
            raise
    
    @property
    def engine(self):
        """获取数据库引擎"""
        if self._engine is None:
            self.initialize()
        return self._engine
    
    @property
    def session_factory(self):
        """获取会话工厂"""
        if self._session_factory is None:
            self.initialize()
        return self._session_factory
    
    def create_session(self):
        """创建新的数据库会话"""
        return scoped_session(self.session_factory)
    
    @contextmanager
    def session_scope(self):
        """提供事务范围的会话上下文管理器"""
        session = self.create_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败，已回滚: {e}")
            raise
        finally:
            session.close()
    
    def test_connection(self):
        """测试数据库连接"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("数据库连接测试成功")
            return True
        except SQLAlchemyError as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
db_manager = DataManager()