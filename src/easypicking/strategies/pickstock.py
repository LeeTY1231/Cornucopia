"""
量化选股系统 v1.0
包含价值、成长、动量、质量等多种选股策略
"""

import pandas as pd
import numpy as np
from tqdm import tqdm
import yfinance as yf
import akshare as ak
from easypicking.strategy.strategyTemplate import StrategyResult, StrategyTemplate
import talib
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class QuantStockStrategy(StrategyTemplate):
    """量化选股策略 - 基于QuantStockSelector的多因子选股框架"""
    
    def __init__(self):
        super().__init__(
            name="QuantStockStrategy",
            description="多因子量化选股策略，包含价值、成长、动量、质量等多种选股方法"
        )
        
        # 定义必需参数和默认参数
        self.required_params = ["strategy_type"]
        self.default_params = {
            "strategy_type": "multi_factor",  # 策略类型: value, growth, momentum, quality, multi_factor
            "min_market_cap": 1e9,           # 最小市值
            "max_pe": 30,                    # 最大市盈率
            "max_pb": 3,                     # 最大市净率
            "min_revenue_growth": 0.1,       # 最小营收增长率
            "min_roe": 0.15,                 # 最小ROE
            "min_price": 10,                 # 最低价格
            "min_volume": 1e6,               # 最低成交量
            "max_debt_ratio": 1.0,           # 最大负债率
            "top_n": 20,                     # 选股数量
            "weights": {                     # 多因子权重
                'value': 0.25,
                'growth': 0.25,
                'momentum': 0.25,
                'quality': 0.25
            }
        }
        
        # 初始化选股器
        self.selector = QuantStockSelector()
    
    def execute(self, data: pd.DataFrame, **kwargs) -> StrategyResult:
        """
        执行量化选股策略
        
        Args:
            data: 股票数据DataFrame包含symbol列
            **kwargs: 策略参数
            
        Returns:
            StrategyResult: 策略执行结果
        """
        # 合并默认参数和传入参数
        params = {**self.default_params, **kwargs}
        
        # 验证参数
        if not self.validate_parameters(params):
            return StrategyResult(
                strategy_name=self.name,
                selected_stocks=[],
                execution_time=datetime.now(),
                parameters=params,
                score=0,
                message="参数验证失败"
            )
        
        try:
            # 获取股票代码列表
            symbols = data['symbol'].tolist() if 'symbol' in data.columns else []
            
            if not symbols:
                return StrategyResult(
                    strategy_name=self.name,
                    selected_stocks=[],
                    execution_time=datetime.now(),
                    parameters=params,
                    score=0,
                    message="未找到有效的股票代码"
                )
            
            # 获取股票数据
            print(f"正在获取 {len(symbols)} 只股票的数据...")
            self.selector.fetch_stock_data(symbols, source='akshare')
            
            # 根据策略类型执行选股
            strategy_type = params["strategy_type"]
            selected_stocks = []
            strategy_message = ""
            
            if strategy_type == "value":
                # 价值策略
                result_df = self.selector.value_strategy(
                    min_market_cap=params["min_market_cap"],
                    max_pe=params["max_pe"],
                    max_pb=params["max_pb"]
                )
                selected_stocks = result_df['symbol'].tolist() if not result_df.empty else []
                strategy_message = f"价值策略选股: 市值>{params['min_market_cap']/1e9}B, PE<{params['max_pe']}, PB<{params['max_pb']}"
                
            elif strategy_type == "growth":
                # 成长策略
                result_df = self.selector.growth_strategy(
                    min_revenue_growth=params["min_revenue_growth"],
                    min_roe=params["min_roe"]
                )
                selected_stocks = result_df['symbol'].tolist() if not result_df.empty else []
                strategy_message = f"成长策略选股: 营收增长>{params['min_revenue_growth']*100}%, ROE>{params['min_roe']*100}%"
                
            elif strategy_type == "momentum":
                # 动量策略
                result_df = self.selector.momentum_strategy(
                    min_price=params["min_price"],
                    min_volume=params["min_volume"]
                )
                selected_stocks = result_df['symbol'].tolist() if not result_df.empty else []
                strategy_message = f"动量策略选股: 价格>${params['min_price']}, 成交量>{params['min_volume']/1e6}M"
                
            elif strategy_type == "quality":
                # 质量策略
                result_df = self.selector.quality_strategy(
                    max_debt_ratio=params["max_debt_ratio"],
                    min_roe=params["min_roe"]
                )
                selected_stocks = result_df['symbol'].tolist() if not result_df.empty else []
                strategy_message = f"质量策略选股: 负债率<{params['max_debt_ratio']*100}%, ROE>{params['min_roe']*100}%"
                
            elif strategy_type == "multi_factor":
                # 多因子策略
                result_df = self.selector.multi_factor_selection(weights=params["weights"])
                selected_stocks = result_df['symbol'].tolist() if not result_df.empty else []
                strategy_message = f"多因子策略选股: 价值{params['weights']['value']*100}%, 成长{params['weights']['growth']*100}%, 动量{params['weights']['momentum']*100}%, 质量{params['weights']['quality']*100}%"
            
            # 限制选股数量
            if len(selected_stocks) > params["top_n"]:
                selected_stocks = selected_stocks[:params["top_n"]]
            
            # 计算策略得分
            score = len(selected_stocks) / min(len(symbols), params["top_n"])
            
            return StrategyResult(
                strategy_name=self.name,
                selected_stocks=selected_stocks,
                execution_time=datetime.now(),
                parameters=params,
                score=score,
                message=f"{strategy_message} - 选中{len(selected_stocks)}只股票",
                metadata={
                    "total_stocks": len(symbols),
                    "selected_count": len(selected_stocks),
                    "strategy_type": strategy_type
                }
            )
            
        except Exception as e:
            return StrategyResult(
                strategy_name=self.name,
                selected_stocks=[],
                execution_time=datetime.now(),
                parameters=params,
                score=0,
                message=f"策略执行失败: {str(e)}"
            )
        
class QuantStockSelector:
    """量化选股器"""
    
    def __init__(self, start_date=None, end_date=None):
        """
        初始化选股器
        Args:
            start_date: 开始日期，格式'YYYY-MM-DD'
            end_date: 结束日期，格式'YYYY-MM-DD'
        """
        self.start_date = start_date or (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        self.end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        self.stock_data = {}
        self.selected_stocks = pd.DataFrame()
        
    def fetch_stock_data(self, symbols, source='yfinance'):
        """
        获取股票数据
        Args:
            symbols: 股票代码列表
            source: 数据源 ('yfinance', 'akshare', 'baostock')
        """
        print(f"正在从 {source} 获取股票数据...")
        
        if source == 'yfinance':
            for symbol in tqdm(symbols, desc="获取股票数据"):
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(start=self.start_date, end=self.end_date)
                    
                    # 获取基本面数据
                    info = ticker.info
                    
                    self.stock_data[symbol] = {
                        'price_data': hist,
                        'fundamental': {
                            'market_cap': info.get('marketCap'),
                            'pe_ratio': info.get('trailingPE'),
                            'pb_ratio': info.get('priceToBook'),
                            'dividend_yield': info.get('dividendYield'),
                            'roe': info.get('returnOnEquity'),
                            'debt_to_equity': info.get('debtToEquity'),
                            'revenue_growth': info.get('revenueGrowth'),
                            'profit_margins': info.get('profitMargins')
                        }
                    }
                    print(f"已获取 {symbol} 数据")
                except Exception as e:
                    print(f"获取 {symbol} 数据失败: {e}")
                    
        elif source == 'akshare':
            # 使用akshare获取A股数据
            for symbol in tqdm(symbols, desc="获取A股数据"):
                try:
                    # 这里需要根据akshare的实际API调整
                    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                           start_date=self.start_date, end_date=self.end_date)
                    self.stock_data[symbol] = {
                        'price_data': df,
                        'fundamental': {}
                    }
                except Exception as e:
                    print(f"获取 {symbol} 数据失败: {e}")
                    
        return self.stock_data
    
    def calculate_technical_indicators(self, symbol):
        """计算技术指标"""
        if symbol not in self.stock_data:
            return {}
            
        df = self.stock_data[symbol]['price_data']
        if df.empty or len(df) < 50:
            return {}
            
        # 使用talib计算技术指标
        closes = df['Close'].values if 'Close' in df.columns else df['收盘'].values
        
        indicators = {
            'rsi': talib.RSI(closes, timeperiod=14)[-1],
            'macd': talib.MACD(closes)[0][-1],  # MACD值
            'bollinger_upper': talib.BBANDS(closes)[0][-1],  # 布林线上轨
            'bollinger_lower': talib.BBANDS(closes)[2][-1],  # 布林线下轨
            'sma_20': talib.SMA(closes, timeperiod=20)[-1],  # 20日均线
            'sma_50': talib.SMA(closes, timeperiod=50)[-1],  # 50日均线
            'atr': talib.ATR(df['High'].values, df['Low'].values, closes)[-1],  # 平均真实波幅
        }
        
        # 计算动量指标
        if len(closes) >= 30:
            returns_1m = (closes[-1] / closes[-21] - 1) * 100  # 1个月收益率
            returns_3m = (closes[-1] / closes[-63] - 1) * 100  # 3个月收益率
            returns_12m = (closes[-1] / closes[-252] - 1) * 100  # 12个月收益率
            
            indicators.update({
                'return_1m': returns_1m,
                'return_3m': returns_3m,
                'return_12m': returns_12m,
                'volatility': np.std(closes[-252:]) / np.mean(closes[-252:]) * 100 if len(closes) >= 252 else 0
            })
            
        return indicators
    
    def value_strategy(self, min_market_cap=1e9, max_pe=30, max_pb=3):
        """
        价值投资策略（格雷厄姆风格）
        筛选低市盈率、低市净率、高股息率的股票
        """
        value_stocks = []
        
        for symbol, data in tqdm(self.stock_data.items(), desc="筛选价值股"):
            fund = data.get('fundamental', {})
            
            # 检查是否有足够的基本面数据
            if not all(key in fund for key in ['pe_ratio', 'pb_ratio', 'dividend_yield']):
                continue
                
            pe = fund['pe_ratio']
            pb = fund['pb_ratio']
            div_yield = fund['dividend_yield'] or 0
            market_cap = fund['market_cap'] or 0
            
            # 价值筛选条件
            conditions = [
                market_cap >= min_market_cap,  # 最小市值要求
                pe is not None and pe > 0 and pe <= max_pe,  # 市盈率上限
                pb is not None and pb > 0 and pb <= max_pb,  # 市净率上限
                div_yield > 0  # 有股息
            ]
            
            if all(conditions):
                # 计算价值得分（越低越好）
                value_score = (pe / max_pe * 0.4 + pb / max_pb * 0.4 - div_yield * 10 * 0.2)
                
                value_stocks.append({
                    'symbol': symbol,
                    'pe_ratio': pe,
                    'pb_ratio': pb,
                    'dividend_yield': div_yield * 100,  # 转换为百分比
                    'market_cap': market_cap,
                    'value_score': value_score
                })
                
        return pd.DataFrame(value_stocks).sort_values('value_score').head(20)
    
    def growth_strategy(self, min_revenue_growth=0.1, min_roe=0.15):
        """
        成长股策略
        筛选高营收增长、高ROE的股票
        """
        growth_stocks = []
        
        for symbol, data in tqdm(self.stock_data.items(), desc="筛选成长股"):
            fund = data.get('fundamental', {})
            
            revenue_growth = fund.get('revenue_growth')
            roe = fund.get('roe')
            profit_margin = fund.get('profit_margins', 0)
            
            if revenue_growth is None or roe is None:
                continue
                
            # 成长筛选条件
            conditions = [
                revenue_growth >= min_revenue_growth,  # 最小营收增长率
                roe >= min_roe,  # 最小ROE
                profit_margin > 0  # 盈利
            ]
            
            if all(conditions):
                # 计算成长得分（越高越好）
                growth_score = (
                    revenue_growth * 0.4 + 
                    roe * 0.4 + 
                    profit_margin * 0.2
                )
                
                growth_stocks.append({
                    'symbol': symbol,
                    'revenue_growth': revenue_growth * 100,  # 转换为百分比
                    'roe': roe * 100,
                    'profit_margin': profit_margin * 100,
                    'growth_score': growth_score
                })
                
        return pd.DataFrame(growth_stocks).sort_values('growth_score', ascending=False).head(20)
    
    def momentum_strategy(self, min_price=10, min_volume=1e6):
        """
        动量策略
        筛选近期表现强势且有成交量的股票
        """
        momentum_stocks = []
        
        for symbol, data in tqdm(self.stock_data.items(), desc="筛选动量股"):
            price_data = data.get('price_data')
            if price_data is None or price_data.empty:
                continue
                
            # 计算技术指标
            indicators = self.calculate_technical_indicators(symbol)
            if not indicators:
                continue
                
            # 获取最新价格和成交量
            if 'Close' in price_data.columns:
                current_price = price_data['Close'].iloc[-1]
                volume = price_data['Volume'].iloc[-1] if 'Volume' in price_data.columns else 0
            else:
                current_price = price_data['收盘'].iloc[-1]
                volume = price_data['成交量'].iloc[-1] if '成交量' in price_data.columns else 0
            
            # 动量筛选条件
            conditions = [
                current_price >= min_price,  # 最低价格要求
                volume >= min_volume,  # 最低成交量
                indicators.get('return_1m', 0) > 5,  # 1个月涨幅>5%
                indicators.get('rsi', 0) > 50 and indicators.get('rsi', 100) < 70,  # RSI在合理区间
                indicators.get('macd', 0) > 0  # MACD向上
            ]
            
            if all(conditions):
                # 计算动量得分
                momentum_score = (
                    indicators.get('return_1m', 0) * 0.3 +
                    indicators.get('return_3m', 0) * 0.3 +
                    (indicators.get('rsi', 50) - 50) * 0.2 +
                    (current_price / indicators.get('sma_20', current_price) - 1) * 100 * 0.2
                )
                
                momentum_stocks.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'return_1m': indicators.get('return_1m', 0),
                    'return_3m': indicators.get('return_3m', 0),
                    'rsi': indicators.get('rsi', 0),
                    'macd': indicators.get('macd', 0),
                    'momentum_score': momentum_score
                })
                
        return pd.DataFrame(momentum_stocks).sort_values('momentum_score', ascending=False).head(20)
    
    def quality_strategy(self, max_debt_ratio=1.0, min_roe=0.1):
        """
        质量因子策略
        筛选高质量公司高ROE、低负债、稳定盈利
        """
        quality_stocks = []
        
        for symbol, data in tqdm(self.stock_data.items(), desc="筛选质量股"):
            fund = data.get('fundamental', {})
            
            roe = fund.get('roe')
            debt_to_equity = fund.get('debt_to_equity', 10)  # 默认高负债
            profit_margin = fund.get('profit_margins', 0)
            
            if roe is None:
                continue
                
            # 质量筛选条件
            conditions = [
                roe >= min_roe,
                debt_to_equity <= max_debt_ratio,
                profit_margin > 0.05  # 利润率>5%
            ]
            
            if all(conditions):
                # 计算质量得分
                quality_score = (
                    roe * 0.4 +
                    (1 - min(debt_to_equity / max_debt_ratio, 1)) * 0.3 +
                    profit_margin * 0.3
                )
                
                quality_stocks.append({
                    'symbol': symbol,
                    'roe': roe * 100,
                    'debt_to_equity': debt_to_equity,
                    'profit_margin': profit_margin * 100,
                    'quality_score': quality_score
                })
                
        return pd.DataFrame(quality_stocks).sort_values('quality_score', ascending=False).head(20)
    
    def multi_factor_selection(self, weights=None):
        """
        多因子综合选股
        Args:
            weights: 各策略权重字典
        """
        if weights is None:
            weights = {
                'value': 0.25,
                'growth': 0.25,
                'momentum': 0.25,
                'quality': 0.25
            }
        
        # 运行各个策略
        value_df = self.value_strategy()
        growth_df = self.growth_strategy()
        momentum_df = self.momentum_strategy()
        quality_df = self.quality_strategy()
        
        # 合并所有股票
        all_stocks = {}
        
        # 收集各策略的得分
        strategies = {
            'value': (value_df, 'value_score'),
            'growth': (growth_df, 'growth_score'),
            'momentum': (momentum_df, 'momentum_score'),
            'quality': (quality_df, 'quality_score')
        }
        
        for strategy_name, (df, score_col) in strategies.items():
            if not df.empty:
                for _, row in df.iterrows():
                    symbol = row['symbol']
                    if symbol not in all_stocks:
                        all_stocks[symbol] = {
                            'symbol': symbol,
                            'scores': {}
                        }
                    
                    # 标准化得分
                    if not df[score_col].empty:
                        normalized_score = (
                            (row[score_col] - df[score_col].min()) / 
                            (df[score_col].max() - df[score_col].min() + 1e-10)
                        )
                        all_stocks[symbol]['scores'][strategy_name] = normalized_score
        
        # 计算综合得分
        results = []
        for symbol, data in all_stocks.items():
            total_score = 0
            score_details = {}
            
            for strategy_name in weights.keys():
                score = data['scores'].get(strategy_name, 0)
                total_score += score * weights[strategy_name]
                score_details[f'{strategy_name}_score'] = score
            
            results.append({
                'symbol': symbol,
                'total_score': total_score,
                **score_details
            })
        
        self.selected_stocks = pd.DataFrame(results).sort_values('total_score', ascending=False)
        return self.selected_stocks.head(30)
    
    def risk_analysis(self, symbols=None):
        """
        风险分析
        Args:
            symbols: 要分析的股票列表
        """
        if symbols is None and not self.selected_stocks.empty:
            symbols = self.selected_stocks['symbol'].head(10).tolist()
        
        risk_results = []
        
        for symbol in symbols:
            if symbol not in self.stock_data:
                continue
                
            indicators = self.calculate_technical_indicators(symbol)
            if not indicators:
                continue
            
            # 计算风险指标
            volatility = indicators.get('volatility', 0)
            atr = indicators.get('atr', 0)
            current_price = self.stock_data[symbol]['price_data']['Close'].iloc[-1] if 'Close' in self.stock_data[symbol]['price_data'].columns else \
                           self.stock_data[symbol]['price_data']['收盘'].iloc[-1]
            
            # 计算最大回撤
            if 'price_data' in self.stock_data[symbol]:
                prices = self.stock_data[symbol]['price_data']['Close'].values if 'Close' in self.stock_data[symbol]['price_data'].columns else \
                        self.stock_data[symbol]['price_data']['收盘'].values
                
                if len(prices) > 0:
                    cumulative_returns = prices / prices[0] - 1
                    running_max = np.maximum.accumulate(cumulative_returns)
                    drawdown = (cumulative_returns - running_max) / (running_max + 1e-10)
                    max_drawdown = np.min(drawdown) * 100
                else:
                    max_drawdown = 0
            else:
                max_drawdown = 0
            
            # 风险评级
            risk_score = (
                min(volatility / 50, 1) * 0.3 +
                min(abs(max_drawdown) / 30, 1) * 0.3 +
                min(atr / current_price * 100 / 10, 1) * 0.4
            )
            
            risk_level = "低" if risk_score < 0.3 else "中" if risk_score < 0.7 else "高"
            
            risk_results.append({
                'symbol': symbol,
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'atr_percent': atr / current_price * 100,
                'risk_score': risk_score,
                'risk_level': risk_level
            })
        
        return pd.DataFrame(risk_results)
    
