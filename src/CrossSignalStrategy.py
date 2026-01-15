"""
A股均线交叉分析脚本
不使用backtrader，纯pandas/numpy实现
使用多种开源接口获取A股数据
"""

import pandas as pd
import numpy as np
import akshare as ak
import yfinance as yf
import datetime
from datetime import timedelta
import warnings
import time
import os
import json
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from tqdm import tqdm

warnings.filterwarnings('ignore')

class AShareDataFetcher:
    """A股数据获取器 - 支持多种数据源"""
    
    def __init__(self, cache_dir='./data/cache', max_workers=20):
        """
        初始化数据获取器
        
        Args:
            cache_dir: 缓存目录
            max_workers: 最大并发线程数
        """
        self.cache_dir = cache_dir
        self.max_workers = max_workers
        
        # 创建缓存目录
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(os.path.join(cache_dir, 'stocks'), exist_ok=True)
        
        # 定义数据源优先级
        self.data_sources = [
            self._fetch_from_akshare,
            self._fetch_from_yfinance,
            self._fetch_from_eastmoney,
        ]
    
    def get_all_a_stocks(self) -> pd.DataFrame:
        """
        获取所有A股列表
        
        Returns:
            DataFrame包含股票代码和名称
        """
        cache_file = os.path.join(self.cache_dir, 'a_stocks_list.pkl')
        
        # 检查缓存（1天内的缓存有效）
        if os.path.exists(cache_file):
            cache_time = datetime.datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.datetime.now() - cache_time < timedelta(days=1):
                try:
                    stocks_df = pd.read_pickle(cache_file)
                    print(f"从缓存加载 {len(stocks_df)} 只A股")
                    return stocks_df
                except:
                    pass
        
        print("正在获取A股列表...")
        
        stocks_list = []
        
        try:
            # 方法1: 使用akshare获取A股列表
            print("尝试方法1: akshare...")
            stock_info_a_code_name_df = ak.stock_info_a_code_name()
            if not stock_info_a_code_name_df.empty:
                stocks_list = stock_info_a_code_name_df[['code', 'name']].copy()
                stocks_list.columns = ['symbol', 'name']
                print(f"从akshare获取到 {len(stocks_list)} 只股票")
        except Exception as e:
            print(f"akshare获取失败: {e}")
        
        # 如果akshare失败，尝试其他方法
        if stocks_list is None or stocks_list.empty:
            try:
                # 方法2: 使用聚宽数据（模拟）
                print("尝试方法2: 本地股票列表...")
                # 这里可以添加一个本地的股票列表文件
                # 或者使用预定义的常见股票
                stocks_list = self._get_local_stock_list()
            except Exception as e:
                print(f"本地列表获取失败: {e}")
        
        if stocks_list is None or stocks_list.empty:
            # 创建一个基本的股票列表（上证50 + 沪深300部分股票）
            stocks_list = self._create_basic_stock_list()
        
        # 保存到缓存
        df = pd.DataFrame(stocks_list)
        df.to_pickle(cache_file)
        
        print(f"获取到 {len(df)} 只A股")
        return df
    
    def _get_local_stock_list(self) -> List[Dict]:
        """获取本地股票列表"""
        # 这里可以返回一些常见的A股
        common_stocks = [
            {"symbol": "000001", "name": "平安银行"},
            {"symbol": "000002", "name": "万科A"},
            {"symbol": "000858", "name": "五粮液"},
            {"symbol": "000333", "name": "美的集团"},
            {"symbol": "000651", "name": "格力电器"},
            {"symbol": "600519", "name": "贵州茅台"},
            {"symbol": "600036", "name": "招商银行"},
            {"symbol": "601318", "name": "中国平安"},
            {"symbol": "601888", "name": "中国中免"},
            {"symbol": "300750", "name": "宁德时代"},
            {"symbol": "002415", "name": "海康威视"},
            {"symbol": "002594", "name": "比亚迪"},
            {"symbol": "300059", "name": "东方财富"},
            {"symbol": "600276", "name": "恒瑞医药"},
            {"symbol": "600887", "name": "伊利股份"},
        ]
        return common_stocks
    
    def _create_basic_stock_list(self) -> List[Dict]:
        """创建基础股票列表"""
        # 主要指数的成分股
        index_stocks = [
            # 上证50
            {"symbol": "600519", "name": "贵州茅台"},
            {"symbol": "600036", "name": "招商银行"},
            {"symbol": "601318", "name": "中国平安"},
            {"symbol": "600276", "name": "恒瑞医药"},
            {"symbol": "600887", "name": "伊利股份"},
            {"symbol": "601166", "name": "兴业银行"},
            {"symbol": "600030", "name": "中信证券"},
            {"symbol": "600837", "name": "海通证券"},
            {"symbol": "601668", "name": "中国建筑"},
            
            # 沪深300
            {"symbol": "000858", "name": "五粮液"},
            {"symbol": "000333", "name": "美的集团"},
            {"symbol": "000651", "name": "格力电器"},
            {"symbol": "002415", "name": "海康威视"},
            {"symbol": "002594", "name": "比亚迪"},
            {"symbol": "300750", "name": "宁德时代"},
            {"symbol": "300059", "name": "东方财富"},
            
            # 创业板
            {"symbol": "300760", "name": "迈瑞医疗"},
            {"symbol": "300124", "name": "汇川技术"},
            {"symbol": "300142", "name": "沃森生物"},
        ]
        return index_stocks
    
    def get_stock_data(self, symbol: str, name: str, days: int = 120) -> Optional[pd.DataFrame]:
        """
        获取单只股票的历史数据
        
        Args:
            symbol: 股票代码
            name: 股票名称
            days: 需要多少天的数据
            
        Returns:
            DataFrame包含OHLCV数据
        """
        cache_file = os.path.join(self.cache_dir, 'stocks', f'{symbol}.pkl')
        
        # 检查缓存
        if os.path.exists(cache_file):
            cache_time = datetime.datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.datetime.now() - cache_time < timedelta(hours=6):
                try:
                    df = pd.read_pickle(cache_file)
                    if not df.empty and len(df) >= 20:
                        return df
                except:
                    pass
        
        # 计算日期范围
        end_date = datetime.datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = None
        
        # 尝试不同的数据源
        for source_func in self.data_sources:
            try:
                df = source_func(symbol, start_date, end_date)
                if df is not None and not df.empty and len(df) >= 20:
                    # 添加股票信息
                    df['symbol'] = symbol
                    df['name'] = name
                    
                    # 保存到缓存
                    try:
                        df.to_pickle(cache_file)
                    except:
                        pass
                    
                    return df
            except Exception as e:
                continue
        
        return None
    
    def _fetch_from_akshare(self, symbol: str, start_date: datetime.datetime, 
                           end_date: datetime.datetime) -> Optional[pd.DataFrame]:
        """使用akshare获取数据"""
        try:
            # 格式化股票代码
            if symbol.startswith('6'):
                ts_code = f"{symbol}.SH"
            elif symbol.startswith('0') or symbol.startswith('3'):
                ts_code = f"{symbol}.SZ"
            else:
                ts_code = symbol
            
            # 获取数据
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                   start_date=start_date.strftime('%Y%m%d'),
                                   end_date=end_date.strftime('%Y%m%d'),
                                   adjust="qfq")
            
            if df.empty:
                return None
            
            # 重命名列
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })
            
            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            df = df.sort_index()
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            # print(f"akshare获取 {symbol} 失败: {e}")
            return None
    
    def _fetch_from_yfinance(self, symbol: str, start_date: datetime.datetime,
                            end_date: datetime.datetime) -> Optional[pd.DataFrame]:
        """使用yfinance获取数据"""
        try:
            # 格式化股票代码（yfinance使用SS/SZ后缀）
            if symbol.startswith('6'):
                yf_symbol = f"{symbol}.SS"
            elif symbol.startswith('0') or symbol.startswith('3'):
                yf_symbol = f"{symbol}.SZ"
            else:
                yf_symbol = symbol
            
            # 获取数据
            stock = yf.Ticker(yf_symbol)
            df = stock.history(start=start_date, end=end_date)
            
            if df.empty:
                return None
            
            # 重命名列
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            # print(f"yfinance获取 {symbol} 失败: {e}")
            return None
    
    def _fetch_from_eastmoney(self, symbol: str, start_date: datetime.datetime,
                             end_date: datetime.datetime) -> Optional[pd.DataFrame]:
        """使用东方财富接口获取数据"""
        try:
            # 东方财富API
            if symbol.startswith('6'):
                market = 'SH'
            else:
                market = 'SZ'
            
            # 构建URL
            url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                'secid': f"{market}.{symbol}",
                'fields1': 'f1,f2,f3,f4,f5',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
                'klt': '101',  # 日线
                'fqt': '1',    # 前复权
                'beg': start_date.strftime('%Y%m%d'),
                'end': end_date.strftime('%Y%m%d'),
                'lmt': '10000'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data['data'] is None or 'klines' not in data['data']:
                return None
            
            klines = data['data']['klines']
            
            # 解析数据
            records = []
            for kline in klines:
                items = kline.split(',')
                records.append({
                    'date': items[0],
                    'open': float(items[1]),
                    'close': float(items[2]),
                    'high': float(items[3]),
                    'low': float(items[4]),
                    'volume': float(items[5]),
                    'amount': float(items[6])
                })
            
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            df = df.sort_index()
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            # print(f"东方财富获取 {symbol} 失败: {e}")
            return None

class MovingAverageAnalyzer:
    """移动平均线分析器"""
    
    def __init__(self, ma_periods=[5, 10, 20, 30, 60]):
        """
        初始化均线分析器
        
        Args:
            ma_periods: 均线周期列表
        """
        self.ma_periods = sorted(ma_periods)
        self.fast_ma = self.ma_periods[0]  # 最快均线（5日）
    
    def calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            df: 包含close价格列的DataFrame
            
        Returns:
            添加了均线列的DataFrame
        """
        df_ma = df.copy()
        
        for period in self.ma_periods:
            ma_column = f'MA{period}'
            df_ma[ma_column] = df_ma['close'].rolling(window=period, min_periods=1).mean()
        
        return df_ma
    
    def find_crossovers(self, df_ma: pd.DataFrame, lookback_days: int = 3) -> List[Dict]:
        """
        查找均线交叉信号
        
        Args:
            df_ma: 包含均线的DataFrame
            lookback_days: 回顾多少天
            
        Returns:
            交叉信号列表
        """
        if len(df_ma) < max(self.ma_periods) + lookback_days:
            return []
        
        crossovers = []
        fast_ma_col = f'MA{self.fast_ma}'
        
        # 检查最近lookback_days
        for i in range(min(lookback_days, len(df_ma) - 1)):
            idx = -1 - i  # 从最新数据开始
            
            for slow_period in self.ma_periods[1:]:  # 跳过快速均线
                slow_ma_col = f'MA{slow_period}'
                
                # 检查当前是否有数据
                if pd.isna(df_ma.iloc[idx][fast_ma_col]) or pd.isna(df_ma.iloc[idx][slow_ma_col]):
                    continue
                
                # 检查前一天是否有数据
                if idx - 1 < -len(df_ma) or (pd.isna(df_ma.iloc[idx-1][fast_ma_col]) or 
                                           pd.isna(df_ma.iloc[idx-1][slow_ma_col])):
                    continue
                
                # 检查金叉：快速均线上穿慢速均线
                current_cross = df_ma.iloc[idx][fast_ma_col] > df_ma.iloc[idx][slow_ma_col]
                prev_cross = df_ma.iloc[idx-1][fast_ma_col] <= df_ma.iloc[idx-1][slow_ma_col]
                
                if current_cross and prev_cross:
                    crossover_info = {
                        'date': df_ma.index[idx].strftime('%Y-%m-%d'),
                        'fast_ma': self.fast_ma,
                        'slow_ma': slow_period,
                        'fast_ma_value': round(df_ma.iloc[idx][fast_ma_col], 2),
                        'slow_ma_value': round(df_ma.iloc[idx][slow_ma_col], 2),
                        'close_price': round(df_ma.iloc[idx]['close'], 2),
                        'signal_strength': self._calculate_signal_strength(
                            df_ma.iloc[idx][fast_ma_col],
                            df_ma.iloc[idx][slow_ma_col]
                        )
                    }
                    crossovers.append(crossover_info)
        
        return crossovers
    
    def _calculate_signal_strength(self, fast_ma: float, slow_ma: float) -> str:
        """计算信号强度"""
        if slow_ma == 0:
            return "弱"
        
        diff_pct = (fast_ma - slow_ma) / slow_ma * 100
        
        if diff_pct > 2:
            return "强"
        elif diff_pct > 1:
            return "中等"
        else:
            return "弱"

class StockScreener:
    """股票筛选器"""
    
    def __init__(self, data_fetcher: AShareDataFetcher, 
                 analyzer: MovingAverageAnalyzer):
        """
        初始化股票筛选器
        
        Args:
            data_fetcher: 数据获取器
            analyzer: 均线分析器
        """
        self.data_fetcher = data_fetcher
        self.analyzer = analyzer
    
    def screen_stocks(self, max_stocks: Optional[int] = None, 
                     lookback_days: int = 3,
                     min_data_days: int = 60) -> pd.DataFrame:
        """
        筛选符合条件的股票
        
        Args:
            max_stocks: 最大分析股票数量
            lookback_days: 回顾天数
            min_data_days: 最小数据天数
            
        Returns:
            包含筛选结果的DataFrame
        """
        print("开始筛选股票...")
        
        # 获取所有A股
        all_stocks = self.data_fetcher.get_all_a_stocks()
        
        if max_stocks:
            all_stocks = all_stocks.head(max_stocks)
        
        results = []
        total = len(all_stocks)
        
        print(f"开始分析 {total} 只股票...")
        
        # 使用进度条
        with tqdm(total=total, desc="分析进度") as pbar:
            for idx, stock in all_stocks.iterrows():
                symbol = stock['symbol']
                name = stock['name']
                
                # 获取股票数据
                df = self.data_fetcher.get_stock_data(symbol, name, days=120)
                
                if df is not None and len(df) >= min_data_days:
                    # 计算均线
                    df_ma = self.analyzer.calculate_moving_averages(df)
                    
                    # 查找交叉信号
                    crossovers = self.analyzer.find_crossovers(df_ma, lookback_days)
                    
                    if crossovers:
                        for crossover in crossovers:
                            result = {
                                '股票代码': symbol,
                                '股票名称': name,
                                '交叉日期': crossover['date'],
                                '上穿均线': f"MA{crossover['slow_ma']}",
                                '收盘价': crossover['close_price'],
                                '5日均线值': crossover['fast_ma_value'],
                                f"MA{crossover['slow_ma']}值": crossover['slow_ma_value'],
                                '信号强度': crossover['signal_strength'],
                                '数据天数': len(df)
                            }
                            results.append(result)
                
                pbar.update(1)
                
                # 添加延迟，避免请求过快
                time.sleep(0.1)
        
        if results:
            results_df = pd.DataFrame(results)
            
            # 排序：按交叉日期倒序，信号强度排序
            results_df['交叉日期'] = pd.to_datetime(results_df['交叉日期'])
            results_df = results_df.sort_values(['交叉日期', '信号强度'], ascending=[False, False])
            
            print(f"\n筛选完成！共发现 {len(results_df)} 个交叉信号")
            return results_df
        else:
            print("\n未发现符合条件的股票")
            return pd.DataFrame()

class ReportGenerator:
    """报告生成器"""
    
    @staticmethod
    def generate_text_report(results_df: pd.DataFrame, output_file: str = None):
        """
        生成文本报告
        
        Args:
            results_df: 筛选结果DataFrame
            output_file: 输出文件路径
        """
        if results_df.empty:
            print("没有发现交叉信号")
            return
        
        print("\n" + "="*80)
        print("A股5日均线上穿其他均线股票筛选报告")
        print("="*80)
        print(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"发现股票数量: {len(results_df)}")
        print("="*80)
        
        # 按股票分组
        grouped = results_df.groupby(['股票代码', '股票名称'])
        
        for (code, name), group in grouped:
            print(f"\n{code} - {name}")
            print("-" * 60)
            
            for _, row in group.iterrows():
                print(f"  交叉日期: {row['交叉日期'].strftime('%Y-%m-%d')}")
                print(f"  信号: 5日均线上穿{row['上穿均线']}")
                print(f"  收盘价: {row['收盘价']}")
                print(f"  5日均线: {row['5日均线值']}")
                print(f"  {row['上穿均线']}: {row[f'{row["上穿均线"]}值']}")
                print(f"  信号强度: {row['信号强度']}")
                print()
        
        print("="*80)
        
        # 保存到文件
        if output_file:
            results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n详细结果已保存到: {output_file}")
    
    @staticmethod
    def generate_summary_report(results_df: pd.DataFrame):
        """生成摘要报告"""
        if results_df.empty:
            return
        
        print("\n" + "="*80)
        print("筛选结果摘要")
        print("="*80)
        
        # 统计信息
        unique_stocks = results_df[['股票代码', '股票名称']].drop_duplicates()
        cross_types = results_df['上穿均线'].value_counts()
        
        print(f"发现交叉的股票数量: {len(unique_stocks)}")
        print("\n交叉类型统计:")
        for ma_type, count in cross_types.items():
            print(f"  {ma_type}: {count}次")
        
        # 最新交叉的股票
        latest_date = results_df['交叉日期'].max()
        latest_stocks = results_df[results_df['交叉日期'] == latest_date]
        
        print(f"\n最新交叉日期: {latest_date.strftime('%Y-%m-%d')}")
        print(f"当日交叉股票数量: {len(latest_stocks)}")
        
        if len(latest_stocks) > 0:
            print("\n最新交叉股票列表:")
            for _, row in latest_stocks.iterrows():
                print(f"  {row['股票代码']} - {row['股票名称']}: 上穿{row['上穿均线']}")

def main():
    """主函数"""
    print("="*80)
    print("A股均线交叉分析系统")
    print("功能: 筛选最近3天5日均线上穿其他均线的股票")
    print("="*80)
    
    # 初始化组件
    print("\n初始化组件...")
    data_fetcher = AShareDataFetcher(cache_dir='./data/cache', max_workers=20)
    analyzer = MovingAverageAnalyzer(ma_periods=[5, 10, 20, 30, 60])
    screener = StockScreener(data_fetcher, analyzer)
    
    # 用户选择
    print("\n请选择分析模式:")
    print("1. 快速分析（前50只股票）")
    print("2. 完整分析（所有股票）")
    print("3. 自定义数量分析")
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    if choice == '1':
        max_stocks = 50
        print(f"\n开始快速分析（前{max_stocks}只股票）...")
    elif choice == '2':
        max_stocks = None
        print("\n开始完整分析（所有股票）...")
    elif choice == '3':
        try:
            max_stocks = int(input("请输入要分析的股票数量: "))
            print(f"\n开始分析（前{max_stocks}只股票）...")
        except:
            max_stocks = 100
            print(f"\n输入无效，使用默认值: 前{max_stocks}只股票")
    else:
        max_stocks = 100
        print(f"\n使用默认值: 前{max_stocks}只股票")
    
    # 筛选股票
    results_df = screener.screen_stocks(
        max_stocks=max_stocks,
        lookback_days=3,
        min_data_days=60
    )
    
    # 生成报告
    if not results_df.empty:
        # 文本报告
        ReportGenerator.generate_text_report(results_df, 'ma_cross_results.csv')
        
        # 摘要报告
        ReportGenerator.generate_summary_report(results_df)
        
        # 保存详细结果
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        detailed_file = f'./data/ma_cross_detailed_{timestamp}.xlsx'
        
        with pd.ExcelWriter(detailed_file, engine='openpyxl') as writer:
            results_df.to_excel(writer, sheet_name='交叉信号', index=False)
            
            # 添加统计信息
            stats_df = pd.DataFrame({
                '统计项': ['分析时间', '股票总数', '发现信号数', '涉及股票数'],
                '数值': [
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    max_stocks or "全部",
                    len(results_df),
                    len(results_df[['股票代码', '股票名称']].drop_duplicates())
                ]
            })
            stats_df.to_excel(writer, sheet_name='统计信息', index=False)
        
        print(f"\n详细结果已保存到: {detailed_file}")
    else:
        print("\n未发现符合条件的股票")
        print("可能的原因:")
        print("1. 当前市场没有5日均线上穿其他均线的股票")
        print("2. 数据获取存在问题，请检查网络连接")
        print("3. 尝试增加分析的天数范围")
    
    print("\n" + "="*80)
    print("分析完成！")

if __name__ == "__main__":
    # 检查依赖
    required_packages = ['pandas', 'numpy', 'akshare', 'yfinance']
    
    print("检查依赖包...")
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} 未安装")
            print(f"   请运行: pip install {package}")
    
    print("\n" + "="*80)
    
    # 运行主函数
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        print(f"\n发生错误: {e}")
        print("\n故障排除:")
        print("1. 检查网络连接")
        print("2. 确保已安装所有依赖包")
        print("3. 尝试重新运行")
        print("4. 如果akshare有问题，可以注释掉相关代码")