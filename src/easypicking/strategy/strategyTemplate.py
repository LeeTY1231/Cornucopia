from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class StrategyResult:
    """策略执行结果"""
    strategy_name: str
    selected_stocks: List[str] 
    execution_time: datetime
    parameters: Dict[str, Any]
    score: Optional[float] = None  
    message: Optional[str] = None  

class StrategyTemplate(ABC):
    """策略基类"""
    
    def __init__(self, name: str, description: str = ""):
        """
        初始化策略
        
        Args:
            name: 策略名称
            description: 策略描述
        """
        self.name = name
        self.description = description
        self.required_params = []  # 必需参数列表
        self.default_params = {}   # 默认参数
    
    @abstractmethod
    def execute(self, data: pd.DataFrame, **kwargs) -> StrategyResult:
        """
        执行策略
        
        Args:
            data: 输入数据
            **kwargs: 策略参数
            
        Returns:
            StrategyResult: 策略执行结果
        """
        pass
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """
        验证参数是否满足要求
        
        Args:
            params: 参数字典
            
        Returns:
            bool: 是否验证通过
        """
        for required_param in self.required_params:
            if required_param not in params:
                return False
        return True
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """获取策略默认参数"""
        return self.default_params