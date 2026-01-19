"""
股票服务模块
提供股票数据的获取、更新、查询等功能
"""

import logging
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Optional
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError

from src.data.data_manager import DataManager
from src.resources.akshare_client import akshare_client
from src.models.stock import Stock

# 配置日志
logger = logging.getLogger(__name__)


class StockService:
    """股票服务类"""

    def __init__(self):
        """初始化股票服务"""
        self.data_manager = DataManager()
        self.akshare_client = akshare_client
        logger.info("股票服务初始化成功")

    def updatestockmodel(self, force_update: bool = False) -> Dict[str, any]:
        """
        更新股票基础数据模型
        从akshare获取所有A股股票信息，并写入数据库

        Args:
            force_update: 是否强制更新所有数据，默认为False（只更新新增或变更的数据）

        Returns:
            dict: 更新结果统计信息
        """
        try:
            logger.info("开始更新股票基础数据...")

            # 获取A股股票列表
            stock_df = self.akshare_client.get_stock_info("603883")
            with self.data_manager.session_scope() as session:
                stock = Stock(
                    stockid=stock_df["股票代码"],
                    name=stock_df["股票简称"],
                    location=stock_df["行业"],
                    symbol=stock_df["ts_code"],
                    industry=None,  # 行业信息需要从其他接口获取
                    ipo_date=None,  # 上市日期需要从其他接口获取
                    downipo_date=None,  # 退市日期
                )
                session.add(stock)

            return
            # if stock_df is None or stock_df.empty:
            #     logger.error("获取股票列表失败，数据为空")
            #     return {
            #         "status": "error",
            #         "message": "获取股票列表失败",
            #         "total_stocks": 0,
            #         "updated": 0,
            #         "added": 0,
            #         "failed": 0
            #     }
            logger.info(f"成功获取 {len(stock_df)} 只股票数据")

            # 统计信息
            stats = {
                "total_stocks": len(stock_df),
                "updated": 0,
                "added": 0,
                "failed": 0,
                "start_time": datetime.now().isoformat(),
            }

            # 批量处理股票数据
            with self.data_manager.session_scope() as session:
                # 获取数据库中已有的股票代码
                existing_stocks = session.query(Stock.stockid).all()
                existing_stock_ids = {stock[0] for stock in existing_stocks}

                for index, row in stock_df.iterrows():
                    try:
                        stock_id = row["ts_code"]
                        stock_name = row["name"]

                        # 解析股票代码，确定市场信息
                        market_info = self._parse_stock_market(stock_id)

                        # 检查股票是否已存在
                        existing_stock = (
                            session.query(Stock)
                            .filter(Stock.stockid == stock_id)
                            .first()
                        )

                        if existing_stock:
                            # 更新现有股票信息
                            if force_update or self._should_update(existing_stock, row):
                                self._update_stock_info(
                                    existing_stock, row, market_info
                                )
                                stats["updated"] += 1
                                logger.debug(f"更新股票信息: {stock_id} - {stock_name}")
                        else:
                            # 添加新股票
                            new_stock = self._create_stock_from_row(row, market_info)
                            session.add(new_stock)
                            stats["added"] += 1
                            logger.info(f"添加新股票: {stock_id} - {stock_name}")

                    except Exception as e:
                        stats["failed"] += 1
                        logger.error(
                            f"处理股票 {row.get('ts_code', '未知')} 时出错: {e}"
                        )
                        continue

            stats["end_time"] = datetime.now().isoformat()
            stats["status"] = "success"
            stats["message"] = (
                f"股票基础数据更新完成，共处理 {stats['total_stocks']} 只股票"
            )

            logger.info(
                f"股票基础数据更新完成: 新增 {stats['added']} 只，更新 {stats['updated']} 只，失败 {stats['failed']} 只"
            )

            return stats

        except Exception as e:
            logger.error(f"更新股票基础数据失败: {e}")
            return {
                "status": "error",
                "message": f"更新股票基础数据失败: {str(e)}",
                "total_stocks": 0,
                "updated": 0,
                "added": 0,
                "failed": 0,
            }

    def _parse_stock_market(self, stock_id: str) -> Dict[str, str]:
        """
        解析股票市场信息

        Args:
            stock_id: 股票代码

        Returns:
            dict: 包含location和symbol的市场信息
        """
        if stock_id.endswith(".SH"):
            return {"location": "上海", "symbol": "SH"}
        elif stock_id.endswith(".SZ"):
            return {"location": "深圳", "symbol": "SZ"}
        elif stock_id.endswith(".BJ"):
            return {"location": "北京", "symbol": "BJ"}
        else:
            return {"location": "未知", "symbol": "未知"}

    def _should_update(self, existing_stock: Stock, new_data: pd.Series) -> bool:
        """
        判断是否需要更新股票信息

        Args:
            existing_stock: 数据库中现有的股票对象
            new_data: 新的股票数据

        Returns:
            bool: 是否需要更新
        """
        # 检查股票名称是否发生变化
        if existing_stock.name != new_data["name"]:
            return True

        # 这里可以添加更多的更新判断逻辑
        # 比如：检查其他字段是否发生变化

        return False

    def _create_stock_from_row(
        self, row: pd.Series, market_info: Dict[str, str]
    ) -> Stock:
        """
        从数据行创建Stock对象

        Args:
            row: 股票数据行
            market_info: 市场信息

        Returns:
            Stock: 股票对象
        """
        return Stock(
            stockid=row["ts_code"],
            name=row["name"],
            location=market_info["location"],
            symbol=market_info["symbol"],
            industry=None,  # 行业信息需要从其他接口获取
            ipo_date=None,  # 上市日期需要从其他接口获取
            downipo_date=None,  # 退市日期
        )

    def _update_stock_info(
        self, stock: Stock, new_data: pd.Series, market_info: Dict[str, str]
    ):
        """
        更新股票信息

        Args:
            stock: 要更新的股票对象
            new_data: 新的股票数据
            market_info: 市场信息
        """
        stock.name = new_data["name"]
        stock.location = market_info["location"]
        stock.symbol = market_info["symbol"]
        # 保留原有的行业和日期信息，避免覆盖

    def get_stock_by_id(self, stock_id: str) -> Optional[Stock]:
        """
        根据股票代码获取股票信息

        Args:
            stock_id: 股票代码

        Returns:
            Stock: 股票对象，如果不存在返回None
        """
        try:
            with self.data_manager.session_scope() as session:
                stock = session.query(Stock).filter(Stock.stockid == stock_id).first()
                return stock
        except Exception as e:
            logger.error(f"获取股票 {stock_id} 信息失败: {e}")
            return None

    def get_all_stocks(self) -> List[Stock]:
        """
        获取所有股票信息

        Returns:
            list: 股票对象列表
        """
        try:
            with self.data_manager.session_scope() as session:
                stocks = session.query(Stock).all()
                return stocks
        except Exception as e:
            logger.error(f"获取所有股票信息失败: {e}")
            return []

    def search_stocks(self, keyword: str, limit: int = 50) -> List[Stock]:
        """
        搜索股票

        Args:
            keyword: 搜索关键词（股票代码或名称）
            limit: 返回结果数量限制

        Returns:
            list: 股票对象列表
        """
        try:
            with self.data_manager.session_scope() as session:
                stocks = (
                    session.query(Stock)
                    .filter(
                        or_(
                            Stock.stockid.like(f"%{keyword}%"),
                            Stock.name.like(f"%{keyword}%"),
                        )
                    )
                    .limit(limit)
                    .all()
                )
                return stocks
        except Exception as e:
            logger.error(f"搜索股票失败: {e}")
            return []

    def delete_stock(self, stock_id: str) -> bool:
        """
        删除股票

        Args:
            stock_id: 股票代码

        Returns:
            bool: 是否删除成功
        """
        try:
            with self.data_manager.session_scope() as session:
                stock = session.query(Stock).filter(Stock.stockid == stock_id).first()

                if stock:
                    session.delete(stock)
                    logger.info(f"删除股票: {stock_id}")
                    return True
                else:
                    logger.warning(f"股票 {stock_id} 不存在，无法删除")
                    return False
        except Exception as e:
            logger.error(f"删除股票 {stock_id} 失败: {e}")
            return False


stock_service = StockService()

__all__ = ["StockService", "stock_service"]
