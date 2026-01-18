from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, Date, BigInteger, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from models import *
""" 个股相关模型定义 """

class Stock(ModelBase):
    """ 个股基本信息模型 """
    __tablename__ = 'stock'

class Finance(ModelBase):
    """ 个股财务信息模型 """
    __tablename__ = 'finance'

class Valuation(ModelBase):
    """ 个股估值模型 """
    __tablename__ = 'valuation'

class StockRealTime(ModelBase):
    """ 个股实时行情模型 """
    __tablename__ = 'stock_realtime'

class StockDaily(ModelBase):
    """ 个股每日行情模型 """
    __tablename__ = 'stock_daily'

class StockTimeSharing(ModelBase):
    """ 个股分时行情模型 """
    __tablename__ = 'stock_timesharing'

