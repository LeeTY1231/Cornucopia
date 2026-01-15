import backtrader as bt
import pandas as pd
import numpy as np
import tushare as ts
import datetime
from datetime import timedelta
import warnings

warnings.filterwarnings('ignore')


class CrossSignalStrategy(bt.Strategy):
    """
    均线交叉策略
    检测5日均线是否上穿其他均线
    """
    params = (
        ('ma_fast', 5),  # 快速均线（5日）
        ('ma_slow_list', [10, 20, 30, 60]),  # 其他均线列表
    )

    def __init__(self):
        # 创建5日均线
        self.ma_fast = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.ma_fast
        )

        # 创建其他均线
        self.ma_slows = []
        for period in self.params.ma_slow_list:
            ma = bt.indicators.SimpleMovingAverage(
                self.data.close, period=period
            )
            self.ma_slows.append(ma)

    def next(self):
        # 只在最近3个交易日检查
        if len(self.data) >= 5:  # 确保有足够的数据
            # 检查今天和过去2天的交叉情况
            for i in range(3):
                idx = -1 - i  # 从今天开始向前追溯
                if idx < -len(self.data):
                    break

                for j, ma_slow in enumerate(self.ma_slows):
                    period = self.params.ma_slow_list[j]

                    # 检查5日均线是否上穿该均线
                    if (self.ma_fast[idx] > ma_slow[idx] and
                            self.ma_fast[idx - 1] <= ma_slow[idx - 1]):

                        # 记录交叉信号
                        cross_info = {
                            'date': self.data.datetime.date(idx),
                            'stock_code': self.data._name,
                            'cross_ma': f'MA{period}',
                            'fast_ma_value': self.ma_fast[idx],
                            'slow_ma_value': ma_slow[idx]
                        }

                        if hasattr(self, 'cross_signals'):
                            self.cross_signals.append(cross_info)
                        else:
                            self.cross_signals = [cross_info]


class StockAnalyzer:
    def __init__(self, token=None):
        """
        初始化股票分析器

        Args:
            token: tushare token，如果为None则使用免费接口
        """
        self.token = token
        # if token:
        #     ts.set_token(token)
        # self.pro = ts.pro_api()

    def get_all_stocks(self):
        """获取所有A股列表"""
        print("正在获取A股列表...")

        # 获取所有股票列表
        try:
            stock_list = self.get_all_stocks(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,list_date'
            )
        except:
            # 如果pro接口失败，使用通用接口
            stock_list = ts.get_stock_basics()
            if hasattr(stock_list, 'index'):
                stock_list.reset_index(inplace=True)
                stock_list.rename(columns={'code': 'ts_code', 'name': 'name'}, inplace=True)

        # 过滤A股（排除创业板、科创板等，如果需要可以调整）
        a_shares = stock_list[
            stock_list['ts_code'].str.endswith(('.SH', '.SZ'))
        ].copy()

        print(f"获取到 {len(a_shares)} 只A股")
        return a_shares

    def get_stock_data(self, ts_code, start_date, end_date):
        """获取单只股票的历史数据"""
        try:
            # 尝试多种方式获取数据
            if hasattr(self, 'pro'):
                df = self.pro.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                # 使用通用接口
                symbol = ts_code.split('.')[0]
                df = ts.get_k_data(
                    symbol,
                    start=start_date,
                    end=end_date,
                    ktype='D'
                )
                df.rename(columns={
                    'date': 'trade_date',
                    'code': 'ts_code',
                    'close': 'close',
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'volume': 'vol'
                }, inplace=True)

            if df.empty:
                return None

            # 格式化数据
            df = df.sort_values('trade_date')
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df.set_index('trade_date', inplace=True)

            return df

        except Exception as e:
            print(f"获取 {ts_code} 数据失败: {e}")
            return None

    def analyze_stock(self, ts_code, name, days_back=60):
        """分析单只股票的均线交叉情况"""
        # 计算日期范围
        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - timedelta(days=days_back)).strftime('%Y%m%d')

        # 获取数据
        df = self.get_stock_data(ts_code, start_date, end_date)

        if df is None or len(df) < 30:  # 至少需要30天数据
            return []

        # 创建Cerebro引擎
        cerebro = bt.Cerebro()

        # 添加数据
        data = bt.feeds.PandasData(
            dataname=df,
            datetime=None,  # 使用索引作为日期
            open='open',
            high='high',
            low='low',
            close='close',
            volume='vol',
            openinterest=-1
        )
        data._name = f"{ts_code}_{name}"  # 设置数据名称以便识别

        cerebro.adddata(data)

        # 添加策略
        cerebro.addstrategy(CrossSignalStrategy)

        # 运行策略
        try:
            results = cerebro.run()

            # 收集交叉信号
            cross_signals = []
            for result in results:
                if hasattr(result, 'cross_signals'):
                    for signal in result.cross_signals:
                        signal['stock_name'] = name
                        cross_signals.append(signal)

            return cross_signals

        except Exception as e:
            print(f"分析 {ts_code} 时出错: {e}")
            return []

    def find_cross_stocks(self, recent_days=3, max_stocks=None, use_cache=True):
        """
        查找最近出现均线交叉的股票

        Args:
            recent_days: 检查最近多少天的交叉
            max_stocks: 最大分析股票数量（None表示所有）
            use_cache: 是否使用缓存（加快测试速度）
        """
        print("开始分析A股均线交叉情况...")

        # 获取所有A股
        all_stocks = self.get_all_stocks()

        if max_stocks:
            all_stocks = all_stocks.head(max_stocks)

        # 收集所有交叉信号
        all_cross_signals = []
        processed = 0

        for _, stock in all_stocks.iterrows():
            ts_code = stock['ts_code']
            name = stock.get('name', 'Unknown')

            processed += 1
            if processed % 100 == 0:
                print(f"已处理 {processed}/{len(all_stocks)} 只股票")

            # 分析股票
            cross_signals = self.analyze_stock(ts_code, name)

            # 过滤最近3天的信号
            recent_date = datetime.datetime.now() - timedelta(days=recent_days)
            for signal in cross_signals:
                if signal['date'] >= recent_date.date():
                    all_cross_signals.append(signal)

        print(f"\n分析完成！共发现 {len(all_cross_signals)} 个交叉信号")

        return all_cross_signals

    def save_results(self, cross_signals, output_file='cross_signals.csv'):
        """保存结果到CSV文件"""
        if not cross_signals:
            print("没有发现交叉信号")
            return

        # 转换为DataFrame
        df = pd.DataFrame(cross_signals)

        # 按日期和股票代码排序
        df = df.sort_values(['date', 'stock_code'], ascending=[False, True])

        # 保存到CSV
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"结果已保存到: {output_file}")

        return df


def main():
    """主函数"""
    print("=" * 60)
    print("A股均线交叉分析工具")
    print("查找最近3天出现5日均线上穿其他均线的股票")
    print("=" * 60)

    # 创建分析器
    # 如果需要使用tushare pro，请在这里设置你的token
    # analyzer = StockAnalyzer(token='你的tushare_token')
    analyzer = StockAnalyzer()  # 使用免费接口

    # 查找交叉股票（这里限制分析50只股票作为演示，实际使用时可以去掉max_stocks参数）
    cross_signals = analyzer.find_cross_stocks(
        recent_days=3,
        max_stocks=50,  # 演示时限制股票数量，实际使用时设为None分析所有股票
        use_cache=True
    )

    # 保存并显示结果
    if cross_signals:
        df = analyzer.save_results(cross_signals, 'ma_cross_signals.csv')

        # 按股票分组显示
        print("\n" + "=" * 60)
        print("发现以下股票的5日均线出现上穿信号：")
        print("=" * 60)

        # 提取唯一股票
        unique_stocks = {}
        for signal in cross_signals:
            code = signal['stock_code'].split('_')[0] if '_' in signal['stock_code'] else signal['stock_code']
            name = signal['stock_name']
            key = f"{code}_{name}"

            if key not in unique_stocks:
                unique_stocks[key] = {
                    'code': code,
                    'name': name,
                    'crosses': []
                }

            cross_info = f"{signal['date']} 上穿{signal['cross_ma']}"
            unique_stocks[key]['crosses'].append(cross_info)

        # 打印结果
        for i, (key, stock_info) in enumerate(unique_stocks.items(), 1):
            print(f"\n{i}. {stock_info['code']} - {stock_info['name']}")
            for cross in stock_info['crosses']:
                print(f"   {cross}")

        print(f"\n总计发现 {len(unique_stocks)} 只符合条件的股票")
    else:
        print("未发现符合条件的股票")


if __name__ == "__main__":
    # 注意事项
    print("注意事项：")
    print("1. 需要安装以下库：backtrader, pandas, numpy, tushare")
    print("2. 可以使用 pip install backtrader pandas numpy tushare 安装")
    print("3. 如需分析所有A股，请将 max_stocks 参数设为 None")
    print("4. 使用 tushare pro 接口可以获得更稳定的数据，需要注册获取token")
    print()

    main()