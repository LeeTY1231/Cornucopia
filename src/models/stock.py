from models import *

""" 个股相关模型定义 """


class Stock(ModelBase):
    """个股基本信息模型"""

    """	
        stockid varchar NOT NULL,
        name varchar NULL,
        "location" varchar NULL,
        symbol varchar NULL,
        industry varchar NULL,
        ipo_date date NULL,
        downipo_date date NULL,
        CONSTRAINT stockmodel_pk PRIMARY KEY (stockid)
    """
    __tablename__ = "stockmodel"
    stockid = Column(String, primary_key=True, nullable=False, comment="股票ID")
    name = Column(String, nullable=False, comment="股票名称")
    location = Column(String, nullable=True, comment="股票上市地点")
    symbol = Column(String, nullable=True, comment="股票所属交易行")
    industry = Column(String, nullable=True, comment="股票所属板块")
    ipo_date = Column(Date, nullable=True, comment="股票上市日期")
    downipo_date = Column(Date, nullable=True, comment="股票退市日期")


class Finance(ModelBase):
    """个股财务信息模型"""

    """
        stockid varchar NULL,
        "date" date NULL,
        total_revenue decimal NULL,
        net_profit decimal NULL,
        total_assets decimal NULL,
        total_liabilities decimal NULL,
        net_assets decimal NULL,
        roe decimal NULL,
        roa decimal NULL,
        gross_margin decimal NULL,
        net_margin decimal NULL,
        debt_ratio decimal NULL,
        current_ratio decimal NULL,
        quick_ratio decimal NULL,
        eps decimal NULL,
        bps decimal NULL,
        cdt date NULL,
        id uuid NOT NULL,
    """
    __tablename__ = "financemodel"
    stockid = Column(String, nullable=False, comment="股票ID")
    date = Column(Date, nullable=False, comment="日期")
    total_revenue = Column(DECIMAL, nullable=True, comment="总营收")
    net_profit = Column(DECIMAL, nullable=True, comment="净利润")
    total_assets = Column(DECIMAL, nullable=True, comment="总资产")
    total_liabilities = Column(DECIMAL, nullable=True, comment="总负债")
    net_assets = Column(DECIMAL, nullable=True, comment="净资产")
    roe = Column(DECIMAL, nullable=True, comment="净资产收益率")
    roa = Column(DECIMAL, nullable=True, comment="总资产收益率")
    gross_margin = Column(DECIMAL, nullable=True, comment="毛利率")
    net_margin = Column(DECIMAL, nullable=True, comment="净利率")
    debt_ratio = Column(DECIMAL, nullable=True, comment="负债比")
    current_ratio = Column(DECIMAL, nullable=True, comment="流动比率")
    quick_ratio = Column(DECIMAL, nullable=True, comment="快速比率")
    eps = Column(DECIMAL, nullable=True, comment="每股收益")
    bps = Column(DECIMAL, nullable=True, comment="每股净资产")
    cdt = Column(Date, nullable=True, comment="创建日期")
    id = Column(UUID, primary_key=True, nullable=False, comment="唯一标识符")


class Valuation(ModelBase):
    """个股估值模型"""

    """
    	id uuid NOT NULL,
        stockid varchar NULL,
        "date" date NULL,
        pe decimal NULL,
        pe_ttm decimal NULL,
        pb decimal NULL,
        ps decimal NULL,
        ps_ttm decimal NULL,
        total_mv decimal NULL,
        circ_mv decimal NULL,
        dividend_ratio decimal NULL,
        cdt date NULL,
    """
    __tablename__ = "valuationmodel"
    id = Column(UUID, primary_key=True, nullable=False, comment="唯一标识符")
    stockid = Column(String, nullable=False, comment="股票ID")
    date = Column(Date, nullable=False, comment="日期")
    pe = Column(DECIMAL, nullable=True, comment="市盈率")
    pe_ttm = Column(DECIMAL, nullable=True, comment="市盈率TTM")
    pb = Column(DECIMAL, nullable=True, comment="市净率")
    ps = Column(DECIMAL, nullable=True, comment="市销率")
    ps_ttm = Column(DECIMAL, nullable=True, comment="市销率TTM")
    total_mv = Column(DECIMAL, nullable=True, comment="总市值")
    circ_mv = Column(DECIMAL, nullable=True, comment="流通市值")
    dividend_ratio = Column(DECIMAL, nullable=True, comment="股息率")
    cdt = Column(Date, nullable=True, comment="创建日期")


class StockRealTime(ModelBase):
    """个股实时行情模型"""

    """
        id bigserial NOT NULL,
        stockid varchar NULL,
        price decimal NULL,
        "change" decimal NULL,
        change_pct decimal NULL,
        volume decimal NULL,
        amount decimal NULL,
        amplitude decimal NULL,
        turnover_rate decimal NULL,
        volume_ratio decimal NULL,
        cdt date NULL,
    """
    __tablename__ = "stockrealtime"
    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment="实时行情ID")
    stockid = Column(String, nullable=False, comment="股票ID")
    price = Column(DECIMAL, nullable=True, comment="实时价格")
    change = Column(DECIMAL, nullable=True, comment="实时涨跌")
    change_pct = Column(DECIMAL, nullable=True, comment="实时涨跌幅")
    volume = Column(DECIMAL, nullable=True, comment="实时成交量")
    amount = Column(DECIMAL, nullable=True, comment="实时成交额")
    amplitude = Column(DECIMAL, nullable=True, comment="实时振幅")
    turnover_rate = Column(DECIMAL, nullable=True, comment="实时换手率")
    volume_ratio = Column(DECIMAL, nullable=True, comment="实时量比")
    cdt = Column(Date, nullable=True, comment="创建日期")


class StockDaily(ModelBase):
    """个股每日行情模型"""
    """
        id uuid NOT NULL,
        stockid varchar NOT NULL,
        "date" date NOT NULL,
        openprice decimal NOT NULL,
        closeprice decimal NULL,
        highprice decimal NULL,
        lowprice decimal NULL,
        change_gross decimal NULL,
        change_pct decimal NULL,
        gross decimal NULL,
        amount decimal NULL,
        turnover_rate decimal NULL,
        cdt date NULL,
    """
    __tablename__ = "stockdaily"
    id = Column(UUID, primary_key=True, nullable=False, comment="唯一标识符")
    stockid = Column(String, nullable=False, comment="股票ID")
    date = Column(Date, nullable=False, comment="日期")
    openprice = Column(DECIMAL, nullable=True, comment="开盘价")
    closeprice = Column(DECIMAL, nullable=True, comment="收盘价")
    highprice = Column(DECIMAL, nullable=True, comment="最高价")
    lowprice = Column(DECIMAL, nullable=True, comment="最低价")
    change_gross = Column(DECIMAL, nullable=True, comment="涨跌")
    change_pct = Column(DECIMAL, nullable=True, comment="涨跌幅")
    gross = Column(DECIMAL, nullable=True, comment="成交量")
    amount = Column(DECIMAL, nullable=True, comment="成交额")
    turnover_rate = Column(DECIMAL, nullable=True, comment="换手率")
    cdt = Column(Date, nullable=True, comment="创建日期")


class StockTimeSharing(ModelBase):
    """个股分时行情模型"""
    """
    	stockid varchar NULL,
        "date" date NULL,
        price decimal NULL,
        avg_price decimal NULL,
        volume decimal NULL,
        amount decimal NULL,
        id bigserial NOT NULL,
    """
    __tablename__ = "stocktimesharing"
    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment="分时行情ID")
    stockid = Column(String, nullable=False, comment="股票ID")
    date = Column(Date, nullable=False, comment="日期")
    price = Column(DECIMAL, nullable=True, comment="分时价格")
    avg_price = Column(DECIMAL, nullable=True, comment="分时均价")
    volume = Column(DECIMAL, nullable=True, comment="分时成交量")
    amount = Column(DECIMAL, nullable=True, comment="分时成交额")
