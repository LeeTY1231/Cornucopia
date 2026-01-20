# strategy_manager.py
import os
import sys
import importlib
import pkgutil
import inspect
from typing import Dict, Type, List, Optional, Any
import pandas as pd
from datetime import datetime
import logging
import traceback
from src.easypicking.strategy.strategyTemplate import StrategyTemplate, StrategyResult


class StrategyManager:
    """策略管理器 - 自动扫描并注册策略"""

    def __init__(self, strategy_dir: str = "strategies", auto_scan: bool = True):
        """
        初始化策略管理器

        Args:
            strategy_dir: 策略目录路径
            auto_scan: 是否自动扫描目录
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        strategy_dir = os.path.join(base_dir, "..", "easypicking", "strategies")
        strategy_dir = os.path.abspath(strategy_dir)
        self.strategy_dir = strategy_dir
        self.strategy_classes: Dict[str, Type[StrategyTemplate]] = {}
        self.strategy_instances: Dict[str, StrategyTemplate] = {}
        self.logger = self._setup_logger()
        if auto_scan:
            self.auto_discover_strategies()

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("StrategyManager")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def auto_discover_strategies(self) -> None:
        """
        自动扫描策略目录，发现并注册所有继承自 StrategyTemplate 的策略类
        """
        self.logger.info(f"开始自动扫描策略目录: {self.strategy_dir}")

        if not os.path.exists(self.strategy_dir):
            self.logger.warning(f"策略目录不存在: {self.strategy_dir}")
            return

        # 确保目录在 Python 路径中
        if self.strategy_dir not in sys.path:
            sys.path.insert(0, self.strategy_dir)

        try:
            # 直接扫描目录中的Python文件
            for filename in os.listdir(self.strategy_dir):
                if filename.endswith(".py") and filename != "__init__.py":
                    module_name = filename[:-3]  # 移除.py后缀
                    try:
                        # 使用相对导入路径
                        full_module_path = f"src.easypicking.strategies.{module_name}"
                        module = importlib.import_module(full_module_path)
                        self._register_module_classes(module)
                    except ImportError as e:
                        self.logger.warning(
                            f"导入模块 {full_module_path} 失败: {str(e)}"
                        )
                        # 尝试直接导入模块
                        try:
                            # 将策略目录添加到Python路径并直接导入
                            if self.strategy_dir not in sys.path:
                                sys.path.insert(0, self.strategy_dir)
                            module = importlib.import_module(module_name)
                            self._register_module_classes(module)
                        except Exception as e2:
                            self.logger.error(f"导入模块 {module_name} 失败: {str(e2)}")
                            continue

            # 如果自动扫描没有找到策略，尝试手动注册
            if not self.strategy_classes:
                return
            self.logger.info(f"策略扫描完成，发现 {len(self.strategy_classes)} 个策略")
        except Exception as e:
            self.logger.error(f"自动扫描策略失败: {str(e)}")
            self.logger.debug(traceback.format_exc())
            raise

    def _register_module_classes(self, module) -> None:
        """
        注册模块中的所有策略类

        Args:
            module: Python模块对象
        """
        for name, obj in inspect.getmembers(module):
            # 检查是否是类、且是 StrategyTemplate 的子类、且不是 StrategyTemplate 自身
            if (
                inspect.isclass(obj)
                and issubclass(obj, StrategyTemplate)
                and obj != StrategyTemplate
            ):

                try:
                    # 尝试实例化以获取策略名称
                    instance = obj()
                    strategy_name = instance.name

                    if strategy_name in self.strategy_classes:
                        self.logger.warning(
                            f"策略名称冲突: {strategy_name}，将使用 {obj.__name__}"
                        )

                    self.strategy_classes[strategy_name] = obj
                    self.strategy_instances[strategy_name] = instance
                    self.logger.info(f"注册策略: {strategy_name} ({obj.__name__})")

                except Exception as e:
                    self.logger.error(f"注册策略类 {obj.__name__} 失败: {str(e)}")

    def register_strategy_class(self, strategy_class: Type[StrategyTemplate]) -> None:
        """
        手动注册策略类

        Args:
            strategy_class: 策略类
        """
        try:
            instance = strategy_class()
            strategy_name = instance.strategy_name

            if strategy_name in self.strategy_classes:
                self.logger.warning(f"策略 {strategy_name} 已存在，将被覆盖")

            self.strategy_classes[strategy_name] = strategy_class
            self.strategy_instances[strategy_name] = instance

            self.logger.info(f"手动注册策略: {strategy_name}")

        except Exception as e:
            self.logger.error(f"注册策略类失败: {str(e)}")
            raise

    def get_strategy(
        self, strategy_name: str, create_new: bool = True
    ) -> Optional[StrategyTemplate]:
        """
        获取策略实例

        Args:
            strategy_name: 策略名称
            create_new: 如果实例不存在，是否创建新实例

        Returns:
            Optional[StrategyTemplate]: 策略实例，如果不存在则返回None
        """
        if strategy_name in self.strategy_instances:
            return self.strategy_instances[strategy_name]

        if create_new and strategy_name in self.strategy_classes:
            try:
                strategy_class = self.strategy_classes[strategy_name]
                instance = strategy_class()
                self.strategy_instances[strategy_name] = instance
                return instance
            except Exception as e:
                self.logger.error(f"创建策略实例 {strategy_name} 失败: {str(e)}")
                return None

        return None

    def execute_strategy(
        self, strategy_name: str, data: pd.DataFrame, **params
    ) -> StrategyResult:
        """
        执行策略

        Args:
            strategy_name: 策略名称
            data: 输入数据
            **params: 策略参数

        Returns:
            StrategyResult: 策略执行结果

        Raises:
            ValueError: 如果策略不存在或参数验证失败
        """
        # 获取策略实例
        strategy = self.get_strategy(strategy_name)
        if strategy is None:
            raise ValueError(f"策略 {strategy_name} 不存在或无法创建实例")

        # 合并默认参数
        default_params = strategy.get_default_parameters()
        execution_params = {**default_params, **params}

        # # 验证参数
        if not strategy.validate_parameters(execution_params):
            missing_params = [
                p for p in strategy.required_params if p not in execution_params
            ]
            raise ValueError(f"策略 {strategy_name} 缺少必需参数: {missing_params}")

        self.logger.info(f"执行策略: {strategy_name}，参数: {execution_params}")

        try:
            result = strategy.execute(data, **execution_params)
            self.logger.info(
                f"策略 {strategy_name} 执行成功，选中 {len(result.selected_stocks)} 只股票"
            )
            return result
        except Exception as e:
            self.logger.error(f"策略 {strategy_name} 执行失败: {str(e)}")
            self.logger.debug(traceback.format_exc())
            raise

    def batch_execute(
        self, strategies: List[Dict[str, Any]], data: pd.DataFrame
    ) -> Dict[str, StrategyResult]:
        """
        批量执行策略

        Args:
            strategies: 策略配置列表，每个元素包含strategy_name和params
            data: 输入数据

        Returns:
            Dict[str, StrategyResult]: 策略执行结果字典
        """
        results = {}

        for config in strategies:
            strategy_name = config.get("strategy_name")
            if not strategy_name:
                self.logger.warning("跳过未指定策略名称的配置")
                continue

            params = config.get("params", {})

            try:
                result = self.execute_strategy(strategy_name, data, **params)
                results[strategy_name] = result
            except Exception as e:
                self.logger.error(f"批量执行中策略 {strategy_name} 失败: {e}")
                # 可以选择继续执行其他策略
                continue

        return results

    def list_strategies(self) -> List[Dict[str, Any]]:
        """列出所有已注册的策略信息"""
        strategies_info = []

        for strategy_name, strategy_class in self.strategy_classes.items():
            try:
                instance = self.get_strategy(strategy_name)
                if instance:
                    info = instance.get_strategy_info()
                    strategies_info.append(info)
            except Exception as e:
                self.logger.error(f"获取策略 {strategy_name} 信息失败: {e}")
                strategies_info.append(
                    {
                        "name": strategy_name,
                        "class_name": strategy_class.__name__,
                        "error": str(e),
                    }
                )

        return strategies_info

    def get_strategy_info(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """获取指定策略的详细信息"""
        strategy = self.get_strategy(strategy_name, create_new=True)
        if strategy:
            return strategy.get_strategy_info()
        return None

    def reload_strategies(self) -> None:
        """重新加载所有策略"""
        self.logger.info("重新加载策略...")

        # 清空当前策略
        self.strategy_classes.clear()
        self.strategy_instances.clear()

        # 重新扫描
        self.auto_discover_strategies()
