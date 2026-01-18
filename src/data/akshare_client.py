"""
AkShare数据客户端
提供免费的股票数据获取功能
"""

import os
from contextlib import contextmanager

import akshare as ak
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import time

from src.utils.logger import logger
from src.utils.exceptions import DataFetchError
from src.utils.decorators import retry, timing, cache_result


@contextmanager
def _temporary_disable_proxies():
    """临时禁用系统代理环境变量（用于处理本地代理未启动导致的请求失败）。"""
    keys = [
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "no_proxy",
    ]
    old = {k: os.environ.get(k) for k in keys if k in os.environ}

    try:
        for k in [
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
        ]:
            os.environ.pop(k, None)
        # 保险起见：全量绕过代理
        os.environ["NO_PROXY"] = "*"
        os.environ["no_proxy"] = "*"
        yield
    finally:
        # 还原原环境变量
        for k in keys:
            if k in old:
                os.environ[k] = old[k]
            else:
                os.environ.pop(k, None)


class AkShareClient:
    """AkShare数据客户端类"""

    def __init__(self):
        """初始化AkShare客户端"""
        self.name = "AkShare"
        logger.info("AkShare客户端初始化成功")

    @retry(max_attempts=3, delay=1)
    @timing
    def get_stock_list(self) -> Optional[pd.DataFrame]:
        """
        获取A股股票列表

        Returns:
            DataFrame: 股票列表数据
                - 代码
                - 名称
                - 市场
                - 上市日期
        """
        try:
            # 优先获取沪深京A股实时行情数据（字段更丰富）
            df = None
            try:
                try:
                    df = ak.stock_zh_a_spot_em()
                except Exception as e:
                    logger.warning(f"实时行情列表获取失败，改用股票代码表: {e}")

                if df is not None and not df.empty:
                    # 重命名列
                    df = df.rename(
                        columns={
                            "代码": "ts_code",
                            "名称": "name",
                            "最新价": "close",
                            "涨跌幅": "pct_chg",
                            "总市值": "total_mv",
                            "流通市值": "circ_mv",
                        }
                    )

                    # 标准化股票代码格式
                    df["ts_code"] = df["ts_code"].apply(self._format_ts_code)

                    logger.info(f"成功获取股票列表，共{len(df)}只股票")
                    return df[
                        ["ts_code", "name", "close", "pct_chg", "total_mv", "circ_mv"]
                    ]

            except Exception as e:
                # 某些网络环境下 stock_zh_a_spot_em 可能被重置连接；退化为更稳定的股票代码/名称列表。
                logger.warning(f"实时行情列表获取失败，改用股票代码表: {e}")

            # fallback: 获取股票代码/名称（更稳定）
            df2 = ak.stock_info_a_code_name()
            if df2 is None or df2.empty:
                logger.warning("获取股票代码表为空")
                return None

            df2 = df2.rename(columns={"code": "ts_code", "name": "name"})
            df2["ts_code"] = df2["ts_code"].apply(self._format_ts_code)

            logger.info(f"成功获取股票代码表，共{len(df2)}只股票")
            return df2[["ts_code", "name"]]

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise DataFetchError(f"AkShare获取股票列表失败: {e}")

    @retry(max_attempts=3, delay=1)
    @timing
    def get_stock_daily(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq",
    ) -> Optional[pd.DataFrame]:
        """
        获取股票日线数据

        Args:
            symbol: 股票代码 (如: '000001')
            start_date: 开始日期 (格式: YYYYMMDD)
            end_date: 结束日期 (格式: YYYYMMDD)
            adjust: 复权类型 ('qfq'-前复权, 'hfq'-后复权, ''-不复权)

        Returns:
            DataFrame: 日线数据
        """
        try:
            # 转换日期格式
            if start_date:
                start_date = pd.to_datetime(start_date).strftime("%Y%m%d")
            else:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

            if end_date:
                end_date = pd.to_datetime(end_date).strftime("%Y%m%d")
            else:
                end_date = datetime.now().strftime("%Y%m%d")

            # 获取历史行情数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
            )

            if df is not None and not df.empty:
                # 重命名列
                df = df.rename(
                    columns={
                        "日期": "trade_date",
                        "开盘": "open",
                        "收盘": "close",
                        "最高": "high",
                        "最低": "low",
                        "成交量": "vol",
                        "成交额": "amount",
                        "涨跌幅": "pct_chg",
                        "涨跌额": "change",
                        "换手率": "turnover_rate",
                    }
                )

                # 添加股票代码
                df["ts_code"] = self._format_ts_code(symbol)

                # 转换日期格式
                df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime(
                    "%Y%m%d"
                )

                logger.info(f"成功获取{symbol}日线数据，共{len(df)}条记录")
                return df

            logger.warning(f"获取{symbol}日线数据为空")
            return None

        except Exception as e:
            logger.error(f"获取{symbol}日线数据失败: {e}")
            raise DataFetchError(f"AkShare获取日线数据失败: {e}")

    @retry(max_attempts=3, delay=1)
    def get_stock_realtime(self, symbols: List[str] = None) -> Optional[pd.DataFrame]:
        """
        获取实时行情数据

        Args:
            symbols: 股票代码列表，如果为None则获取全部

        Returns:
            DataFrame: 实时行情数据
        """
        try:
            try:
                df = ak.stock_zh_a_spot_em()
            except Exception as e:
                if _looks_like_proxy_error(e):
                    logger.warning("检测到代理错误，尝试绕过系统代理重试 AkShare 请求")
                    with _temporary_disable_proxies():
                        df = ak.stock_zh_a_spot_em()
                else:
                    raise

            if df is not None and not df.empty:
                # 重命名列
                df = df.rename(
                    columns={
                        "代码": "ts_code",
                        "名称": "name",
                        "最新价": "price",
                        "涨跌幅": "pct_chg",
                        "涨跌额": "change",
                        "成交量": "volume",
                        "成交额": "amount",
                        "振幅": "amplitude",
                        "最高": "high",
                        "最低": "low",
                        "今开": "open",
                        "昨收": "pre_close",
                        "量比": "volume_ratio",
                        "换手率": "turnover_rate",
                        "市盈率-动态": "pe",
                        "市净率": "pb",
                        "总市值": "total_mv",
                        "流通市值": "circ_mv",
                    }
                )

                df["ts_code"] = df["ts_code"].apply(self._format_ts_code)

                # 如果指定了股票代码，则筛选
                if symbols:
                    formatted_symbols = [self._format_ts_code(s) for s in symbols]
                    df = df[df["ts_code"].isin(formatted_symbols)]

                logger.info(f"成功获取实时行情数据，共{len(df)}只股票")
                return df

            return None

        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            raise DataFetchError(f"AkShare获取实时行情失败: {e}")

    @retry(max_attempts=3, delay=1)
    @timing
    def get_stock_intraday(
        self, symbol: str, trade_date: str = None, period: str = "1"
    ) -> Optional[pd.DataFrame]:
        """获取分钟级分时数据（东方财富分钟K）

        Args:
            symbol: 股票代码（支持 000001 / 000001.SZ / 600000.SH）
            trade_date: 交易日 (YYYYMMDD 或 YYYY-MM-DD)，默认今天
            period: 分钟周期，默认 1 分钟

        Returns:
            DataFrame: 包含 时间/开盘/收盘/最高/最低/成交量/成交额/均价
        """
        try:
            code = str(symbol).strip()
            if "." in code:
                code = code.split(".")[0]

            if not trade_date:
                trade_date = datetime.now().strftime("%Y-%m-%d")
            else:
                trade_date = str(trade_date).strip()
                if len(trade_date) == 8 and trade_date.isdigit():
                    trade_date = pd.to_datetime(trade_date).strftime("%Y-%m-%d")

            start_dt = f"{trade_date} 09:30:00"
            end_dt = f"{trade_date} 15:00:00"

            df = ak.stock_zh_a_hist_min_em(
                symbol=code,
                start_date=start_dt,
                end_date=end_dt,
                period=str(period),
                adjust="",
            )

            if df is None or df.empty:
                return None

            return df
        except Exception as e:
            logger.error(f"获取{symbol}分时数据失败: {e}")
            raise

    @retry(max_attempts=3, delay=2)
    @timing
    def get_stock_financial(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取财务报表数据

        Args:
            symbol: 股票代码

        Returns:
            DataFrame: 财务数据
        """
        try:
            # 获取财务指标数据
            df = ak.stock_financial_analysis_indicator(symbol=symbol)

            if df is not None and not df.empty:
                df["ts_code"] = self._format_ts_code(symbol)
                logger.info(f"成功获取{symbol}财务数据，共{len(df)}条记录")
                return df

            return None

        except Exception as e:
            logger.error(f"获取{symbol}财务数据失败: {e}")
            raise DataFetchError(f"AkShare获取财务数据失败: {e}")

    @cache_result(ttl=3600)
    @retry(max_attempts=3, delay=1)
    def get_trade_calendar(
        self, start_date: str = None, end_date: str = None
    ) -> Optional[pd.DataFrame]:
        """
        获取交易日历

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 交易日历
        """
        try:
            df = ak.tool_trade_date_hist_sina()

            if df is not None and not df.empty:
                df = df.rename(columns={"trade_date": "cal_date"})
                df["cal_date"] = pd.to_datetime(df["cal_date"]).dt.strftime("%Y%m%d")

                # 筛选日期范围
                if start_date:
                    df = df[df["cal_date"] >= start_date]
                if end_date:
                    df = df[df["cal_date"] <= end_date]

                logger.info(f"成功获取交易日历，共{len(df)}个交易日")
                return df

            return None

        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            raise DataFetchError(f"AkShare获取交易日历失败: {e}")

    @retry(max_attempts=3, delay=1)
    def get_index_daily(
        self, symbol: str = "000001", start_date: str = None, end_date: str = None
    ) -> Optional[pd.DataFrame]:
        """
        获取指数日线数据

        Args:
            symbol: 指数代码 ('000001'-上证指数, '399001'-深证成指, '399006'-创业板指)
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame: 指数日线数据
        """
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")

            # 获取指数历史数据
            df = ak.stock_zh_index_daily(symbol=f"sh{symbol}")

            if df is not None and not df.empty:
                df = df.rename(
                    columns={
                        "date": "trade_date",
                        "open": "open",
                        "close": "close",
                        "high": "high",
                        "low": "low",
                        "volume": "vol",
                    }
                )

                df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime(
                    "%Y%m%d"
                )
                df["ts_code"] = f"{symbol}.SH"

                # 筛选日期
                df = df[
                    (df["trade_date"] >= start_date) & (df["trade_date"] <= end_date)
                ]

                logger.info(f"成功获取{symbol}指数数据，共{len(df)}条记录")
                return df

            return None

        except Exception as e:
            logger.error(f"获取指数数据失败: {e}")
            raise DataFetchError(f"AkShare获取指数数据失败: {e}")

    @retry(max_attempts=3, delay=1)
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            dict: 股票基本信息
        """
        try:
            # 获取个股信息
            df = ak.stock_individual_info_em(symbol=symbol)

            if df is not None and not df.empty:
                info = dict(zip(df["item"], df["value"]))
                info["ts_code"] = self._format_ts_code(symbol)
                logger.info(f"成功获取{symbol}基本信息")
                return info

            return None

        except Exception as e:
            logger.error(f"获取{symbol}基本信息失败: {e}")
            return None

    @staticmethod
    def _format_ts_code(code: str) -> str:
        """
        格式化股票代码为Tushare标准格式

        Args:
            code: 原始代码

        Returns:
            str: 格式化后的代码 (如: 000001.SZ, 600000.SH)
        """
        code = str(code).strip()

        # 如果已经是标准格式，直接返回
        if "." in code:
            return code

        # 根据代码前缀判断市场
        if code.startswith("6"):
            return f"{code}.SH"  # 上海
        elif code.startswith(("0", "3")):
            return f"{code}.SZ"  # 深圳
        elif code.startswith("8") or code.startswith("4"):
            return f"{code}.BJ"  # 北京
        else:
            return f"{code}.SH"  # 默认上海

    def batch_get_daily(
        self, symbols: List[str], start_date: str, end_date: str, delay: float = 0.2
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取日线数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            delay: 请求间隔(秒)

        Returns:
            dict: {股票代码: DataFrame}
        """
        result = {}

        for symbol in symbols:
            try:
                df = self.get_stock_daily(symbol, start_date, end_date)
                if df is not None:
                    result[symbol] = df
                time.sleep(delay)  # 避免请求过快
            except Exception as e:
                logger.error(f"批量获取{symbol}数据失败: {e}")
                continue

        logger.info(f"批量获取完成，成功{len(result)}/{len(symbols)}只股票")
        return result


# 创建全局实例
akshare_client = AkShareClient()


__all__ = ["AkShareClient", "akshare_client"]
