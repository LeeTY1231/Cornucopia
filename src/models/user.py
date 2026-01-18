from models import *

""" 用户相关模型定义 """

class User(ModelBase):
    """ 用户模型 """
    """
    	id uuid NOT NULL,
        username varchar NOT NULL,
        "password" varchar NOT NULL,
        mail varchar NOT NULL,
        "permission" varchar NULL,
        active bool DEFAULT false NOT NULL,
        last_login date NULL,
        CONSTRAINT user_pk PRIMARY KEY (id)
    """
    __tablename__ = 'user'

    id = Column(UUID, primary_key=True, comment="用户ID")
    username = Column(String, nullable=False, comment="用户名")
    password = Column(String, nullable=False, comment="密码")
    email = Column(String, nullable=True, comment="邮箱")
    cdt = Column(DateTime, default=datetime.now(timezone.utc), comment="创建时间")

class UserMarket(ModelBase):
    """ 用户持仓模型 """
    """
    	id bigserial NOT NULL,
        userid uuid NULL,
        costprice decimal NULL,
        amount decimal NULL,
        total decimal NULL,
        cdt date NULL,
    """
    __tablename__ = 'usermarket'

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment="持仓ID")
    userid = Column(UUID, nullable=False, comment="用户ID")
    costprice = Column(DECIMAL, nullable=False, comment="持仓成本价")
    amount = Column(DECIMAL, nullable=False, comment="持仓数量")
    total = Column(DECIMAL, nullable=False, comment="持仓总金额")
    cdt = Column(DateTime, nullable=False, comment="持仓创建时间")

class UserPick(ModelBase):
    """ 用户自选股模型 """
    """
        id uuid NOT NULL,
        userid uuid NULL,
        stockid varchar NULL,
        cdt date NULL,
    """
    __tablename__ = 'userpick'

    id = Column(UUID, primary_key=True, nullable=False, comment="自选ID")
    userid = Column(UUID, nullable=False, comment="用户ID")
    stockid = Column(String, nullable=False, comment="股票ID")
    cdt = Column(DateTime, nullable=False, comment="自选创建时间")

class UserOperate(ModelBase):
    """ 用户操作记录模型 """
    """
        id bigserial NOT NULL,
        userid uuid NULL,
        stockid varchar NULL,
        price decimal NULL,
        "change" decimal NULL,
        cdt date NULL,
    """
    __tablename__ = 'useroperate'

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment="操作记录ID")
    userid = Column(UUID, nullable=False, comment="用户ID")
    stockid = Column(String, nullable=False, comment="股票ID")
    price = Column(DECIMAL, nullable=False, comment="操作价格")
    change = Column(DECIMAL, nullable=False, comment="操作数量")
    cdt = Column(DateTime, nullable=False, comment="操作时间")
