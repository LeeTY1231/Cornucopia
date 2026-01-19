from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, Date, UUID, BigInteger, DECIMAL
from sqlalchemy.sql import func
from datetime import datetime, timezone
ModelBase = declarative_base()

""" 通用模型定义 """

class Log(ModelBase):
    """ 日志模型 """
    """
        "event" varchar NULL,
        "level" int NULL,
        message varchar NULL,
        cdt date NULL,
        opid varchar NULL,
        id uuid NOT NULL,
        CONSTRAINT syslog_pk PRIMARY KEY (id)
    """
    __tablename__ = 'syslog'
    event = Column(String, nullable=True, comment="事件")
    level = Column(Integer, nullable=True, comment="日志级别")
    message = Column(String, nullable=True, comment="日志消息")
    cdt = Column(DateTime, nullable=True, comment="创建时间")
    opid = Column(String, nullable=True, comment="操作人ID")
    id = Column(UUID, primary_key=True, comment="日志ID")
