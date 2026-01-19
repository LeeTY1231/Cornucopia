from data import *

class Repository:
    """通用的数据管理器"""
    
    def __init__(self, db_session: Session, model_class: Type[T]):
        """
        初始化数据管理器
        
        Args:
            db_session: SQLAlchemy数据库会话
            model_class: 模型类
        """
        self.db = db_session
        self.model = model_class
        
    def create(self, data: Dict[str, Any]) -> T:
        """
        创建新记录
        
        Args:
            data: 要创建的数据字典
            
        Returns:
            创建的模型实例
        """
        try:
            # 如果主键是UUID类型且未提供，自动生成
            primary_keys = self._get_primary_keys()
            for pk in primary_keys:
                if pk in self.model.__table__.columns:
                    column = self.model.__table__.columns[pk]
                    if (hasattr(column.type, '__visit_name__') and 
                        column.type.__visit_name__ == 'UUID' and 
                        data.get(pk) is None):
                        data[pk] = str(uuid.uuid4())
            
            # 处理时间字段
            if hasattr(self.model, 'cdt') and 'cdt' not in data:
                data['cdt'] = datetime.now()
            if hasattr(self.model, 'udt') and 'udt' not in data:
                data['udt'] = datetime.now()
            
            instance = self.model(**data)
            self.db.add(instance)
            self.db.flush()
            return instance
        except Exception as e:
            self.db.rollback()
            raise e
    
    def create_bulk(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """
        批量创建记录
        
        Args:
            data_list: 要创建的数据字典列表
            
        Returns:
            创建的模型实例列表
        """
        try:
            instances = []
            for data in data_list:
                instance = self.create(data)
                instances.append(instance)
            self.db.commit()
            return instances
        except Exception as e:
            self.db.rollback()
            raise e
        
    def get_by_id(self, id_value: Union[int, str, PyUUID]) -> Optional[T]:
        """
        根据主键获取记录
        
        Args:
            id_value: 主键值
            
        Returns:
            模型实例或None
        """
        primary_keys = self._get_primary_keys()
        
        if len(primary_keys) == 1:
            # 单主键情况
            pk = primary_keys[0]
            return self.db.query(self.model).filter(
                getattr(self.model, pk) == id_value
            ).first()
        else:
            # 多主键情况，id_value应该是字典
            if isinstance(id_value, dict):
                filters = []
                for pk in primary_keys:
                    if pk in id_value:
                        filters.append(getattr(self.model, pk) == id_value[pk])
                if filters:
                    return self.db.query(self.model).filter(and_(*filters)).first()
        return None
    
    def get_one_by_condition(self, **filters: Any) -> Optional[T]:
        """
        根据条件获取单个记录
        
        Args:
            **filters: 过滤条件
            
        Returns:
            模型实例或None
        """
        return self.db.query(self.model).filter_by(**filters).first()
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: Optional[int] = None,
        **filters: Any
    ) -> List[T]:
        """
        获取所有记录（可过滤）
        
        Args:
            skip: 跳过的记录数
            limit: 限制返回的记录数
            **filters: 过滤条件
            
        Returns:
            模型实例列表
        """
        query = self.db.query(self.model)
        
        if filters:
            query = query.filter_by(**filters)
        
        if skip:
            query = query.offset(skip)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def filter(
        self,
        *criterions,
        skip: int = 0,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[T]:
        """
        根据SQLAlchemy表达式过滤记录
        
        Args:
            *criterions: SQLAlchemy过滤条件
            skip: 跳过的记录数
            limit: 限制返回的记录数
            order_by: 排序字段
            order_desc: 是否降序
            
        Returns:
            模型实例列表
        """
        query = self.db.query(self.model)
        
        if criterions:
            query = query.filter(*criterions)
        
        if order_by:
            column = getattr(self.model, order_by, None)
            if column:
                if order_desc:
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
        
        if skip:
            query = query.offset(skip)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def query_by_sql(self, sql: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        执行原始SQL查询
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            结果字典列表
        """
        result = self.db.execute(text(sql), params or {})
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result]
    
    def count(self, **filters: Any) -> int:
        """
        统计记录数
        
        Args:
            **filters: 过滤条件
            
        Returns:
            记录数
        """
        query = self.db.query(self.model)
        
        if filters:
            query = query.filter_by(**filters)
        
        return query.count()
    
    def exists(self, **filters: Any) -> bool:
        """
        检查记录是否存在
        
        Args:
            **filters: 过滤条件
            
        Returns:
            bool
        """
        return self.db.query(self.model).filter_by(**filters).first() is not None
        
    def update(self, id_value: Union[int, str, PyUUID, Dict], data: Dict[str, Any]) -> Optional[T]:
        """
        更新记录
        
        Args:
            id_value: 主键值或主键字典
            data: 要更新的数据
            
        Returns:
            更新后的模型实例或None
        """
        try:
            instance = self.get_by_id(id_value)
            if not instance:
                return None
            
            # 排除主键字段
            primary_keys = self._get_primary_keys()
            for pk in primary_keys:
                data.pop(pk, None)
            
            # 更新时间字段
            if hasattr(self.model, 'udt'):
                data['udt'] = datetime.now()
            
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            self.db.commit()
            return instance
        except Exception as e:
            self.db.rollback()
            raise e
    
    def update_bulk(self, id_data_list: List[Dict]) -> int:
        """
        批量更新记录
        
        Args:
            id_data_list: 包含id和data的字典列表
            
        Returns:
            更新的记录数
        """
        try:
            updated_count = 0
            for item in id_data_list:
                if 'id' in item and 'data' in item:
                    instance = self.update(item['id'], item['data'])
                    if instance:
                        updated_count += 1
            self.db.commit()
            return updated_count
        except Exception as e:
            self.db.rollback()
            raise e
    
    def update_by_condition(self, data: Dict[str, Any], **filters: Any) -> int:
        """
        根据条件更新多个记录
        
        Args:
            data: 要更新的数据
            **filters: 过滤条件
            
        Returns:
            更新的记录数
        """
        try:
            # 排除主键字段
            primary_keys = self._get_primary_keys()
            for pk in primary_keys:
                data.pop(pk, None)
            
            # 更新时间字段
            if hasattr(self.model, 'udt'):
                data['udt'] = datetime.now()
            
            result = self.db.query(self.model).filter_by(**filters).update(
                data, synchronize_session=False
            )
            self.db.commit()
            return result
        except Exception as e:
            self.db.rollback()
            raise e
        
    def delete(self, id_value: Union[int, str, PyUUID, Dict]) -> bool:
        """
        删除记录
        
        Args:
            id_value: 主键值或主键字典
            
        Returns:
            是否成功删除
        """
        try:
            instance = self.get_by_id(id_value)
            if not instance:
                return False
            
            self.db.delete(instance)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e
    
    def delete_by_condition(self, **filters: Any) -> int:
        """
        根据条件删除多个记录
        
        Args:
            **filters: 过滤条件
            
        Returns:
            删除的记录数
        """
        try:
            result = self.db.query(self.model).filter_by(**filters).delete(
                synchronize_session=False
            )
            self.db.commit()
            return result
        except Exception as e:
            self.db.rollback()
            raise e
    
    def delete_bulk(self, id_list: List[Union[int, str, PyUUID]]) -> int:
        """
        批量删除记录
        
        Args:
            id_list: 主键值列表
            
        Returns:
            删除的记录数
        """
        try:
            deleted_count = 0
            for id_value in id_list:
                if self.delete(id_value):
                    deleted_count += 1
            self.db.commit()
            return deleted_count
        except Exception as e:
            self.db.rollback()
            raise e
        
    def begin_transaction(self):
        """开始事务"""
        pass 
    
    def commit(self):
        """提交事务"""
        self.db.commit()
    
    def rollback(self):
        """回滚事务"""
        self.db.rollback()
        
    def _get_primary_keys(self) -> List[str]:
        return [key.name for key in self.model.__table__.primary_key]
    
    def get_table_name(self) -> str:
        return self.model.__tablename__
    
    def get_columns(self) -> List[str]:
        return [column.name for column in self.model.__table__.columns]
    
    def refresh(self, instance: T) -> T:
        self.db.refresh(instance)
        return instance
    
    def save(self, instance: T) -> T:
        if instance not in self.db:
            self.db.add(instance)
        self.db.commit()
        return instance
