#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础网格交易策略
=================
策略原理：在设定的价格区间内，将资金等分为 N 份，
价格每下跌一格买入一份，每上涨一格卖出一份，
通过震荡行情中的低买高卖获取收益。

适用场景：震荡市、波动率适中的标的
风险提示：单边行情中可能持续买入或卖空

参考：股票搭子 - AI 量化交易平台 (https://jiademin2688.top)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime


def fetch_stock_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取股票历史数据。
    
    Args:
        symbol: 股票代码，如 '600519'
        start_date: 开始日期 'YYYYMMDD'
        end_date: 结束日期 'YYYYMMDD'
    
    Returns:
        包含 OHLCV 数据的 DataFrame
    """
    try:
        import akshare as ak
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        }, inplace=True)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df
    except ImportError:
        print("请安装 akshare: pip install akshare")
        # 生成模拟数据用于演示
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        np.random.seed(42)
        price = 50
        prices = []
        for _ in range(len(dates)):
            price *= (1 + np.random.normal(0.0005, 0.02))
            prices.append(price)
        return pd.DataFrame({
            'open': prices, 'close': prices,
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.99 for p in prices],
            'volume': np.random.randint(10000, 100000, len(dates))
        }, index=dates)


class GridTradingStrategy:
    """网格交易策略。
    
    参数说明：
        grid_num: 网格数量（将资金分为 grid_num 份）
        upper_price: 网格上限价格
        lower_price: 网格下限价格
        initial_capital: 初始资金
    """
    
    def __init__(
        self,
        grid_num: int = 10,
        upper_price: float = None,
        lower_price: float = None,
        initial_capital: float = 100000
    ):
        self.grid_num = grid_num
        self.upper_price = upper_price
        self.lower_price = lower_price
        self.initial_capital = initial_capital
        self.grid_step = None
        self.grid_levels = None
        
    def setup_grid(self, current_price: float):
        """根据当前价格设置网格参数。"""
        if self.upper_price is None:
            self.upper_price = current_price * 1.2
        if self.lower_price is None:
            self.lower_price = current_price * 0.8
        
        self.grid_step = (self.upper_price - self.lower_price) / self.grid_num
        self.grid_levels = [
            self.lower_price + i * self.grid_step
            for i in range(self.grid_num + 1)
        ]
        
        print(f"网格参数:")
        print(f"  价格区间: {self.lower_price:.2f} - {self.upper_price:.2f}")
        print(f"  网格数量: {self.grid_num}")
        print(f"  每格价差: {self.grid_step:.2f}")
        print(f"  每格资金: {self.initial_capital / self.grid_num:.2f}")
    
    def run_backtest(self, df: pd.DataFrame) -> dict:
        """执行回测。
        
        Args:
            df: 包含 'close' 列的行情数据
        
        Returns:
            回测结果字典
        """
        self.setup_grid(df['close'].iloc[0])
        
        cash = self.initial_capital
        shares = 0
        trades = []
        last_grid_idx = None
        
        per_grid_cash = self.initial_capital / self.grid_num
        
        for i, (date, row) in enumerate(df.iterrows()):
            price = row['close']
            
            # 确定当前价格所在的网格层级
            current_grid_idx = int((price - self.lower_price) / self.grid_step)
            current_grid_idx = max(0, min(current_grid_idx, self.grid_num))
            
            # 首次不交易
            if last_grid_idx is None:
                last_grid_idx = current_grid_idx
                continue
            
            # 价格下跌穿越网格线 → 买入
            if current_grid_idx < last_grid_idx:
                buy_shares = int(per_grid_cash / price / 100) * 100
                if buy_shares > 0 and cash >= buy_shares * price:
                    cash -= buy_shares * price
                    shares += buy_shares
                    trades.append({
                        'date': date, 'action': 'BUY',
                        'price': price, 'shares': buy_shares,
                        'grid_level': current_grid_idx
                    })
            
            # 价格上涨穿越网格线 → 卖出
            elif current_grid_idx > last_grid_idx:
                sell_shares = int(shares / (self.grid_num - current_grid_idx + 1) / 100) * 100
                if sell_shares > 0 and shares >= sell_shares:
                    cash += sell_shares * price
                    shares -= sell_shares
                    trades.append({
                        'date': date, 'action': 'SELL',
                        'price': price, 'shares': sell_shares,
                        'grid_level': current_grid_idx
                    })
            
            last_grid_idx = current_grid_idx
        
        # 计算最终资产
        final_price = df['close'].iloc[-1]
        final_value = cash + shares * final_price
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # 计算最大回撤
        portfolio_values = []
        cash_tmp = self.initial_capital
        shares_tmp = 0
        for i, (date, row) in enumerate(df.iterrows()):
            for t in trades:
                if t['date'] == date:
                    if t['action'] == 'BUY':
                        cash_tmp -= t['shares'] * t['price']
                        shares_tmp += t['shares']
                    else:
                        cash_tmp += t['shares'] * t['price']
                        shares_tmp -= t['shares']
            portfolio_values.append(cash_tmp + shares_tmp * row['close'])
        
        portfolio_values = np.array(portfolio_values)
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - peak) / peak
        max_drawdown = drawdown.min()
        
        # 计算夏普比率（简化版）
        daily_returns = np.diff(portfolio_values) / portfolio_values[:-1]
        sharpe = np.sqrt(252) * daily_returns.mean() / (daily_returns.std() + 1e-10)
        
        # 计算胜率
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        buy_trades = [t for t in trades if t['action'] == 'BUY']
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'total_trades': len(trades),
            'buy_count': len(buy_trades),
            'sell_count': len(sell_trades),
            'trades': trades
        }


def plot_results(df: pd.DataFrame, result: dict):
    """绘制回测结果图表。"""
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    
    # 价格走势 + 买卖点
    ax1 = axes[0]
    ax1.plot(df.index, df['close'], label='收盘价', color='#2563EB', linewidth=1)
    
    buys = [t for t in result['trades'] if t['action'] == 'BUY']
    sells = [t for t in result['trades'] if t['action'] == 'SELL']
    
    if buys:
        ax1.scatter([t['date'] for t in buys], [t['price'] for t in buys],
                    color='#10B981', marker='^', s=60, label='买入', zorder=5)
    if sells:
        ax1.scatter([t['date'] for t in sells], [t['price'] for t in sells],
                    color='#EF4444', marker='v', s=60, label='卖出', zorder=5)
    
    ax1.set_title('网格交易策略 — 价格走势与买卖信号', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.set_ylabel('价格 (元)')
    ax1.grid(True, alpha=0.3)
    
    # 资金曲线
    ax2 = axes[1]
    portfolio_values = [result['initial_capital']]
    cash = result['initial_capital']
    shares = 0
    trade_idx = 0
    trades_sorted = sorted(result['trades'], key=lambda x: x['date'])
    
    for date in df.index:
        while trade_idx < len(trades_sorted) and trades_sorted[trade_idx]['date'] <= date:
            t = trades_sorted[trade_idx]
            if t['action'] == 'BUY':
                cash -= t['shares'] * t['price']
                shares += t['shares']
            else:
                cash += t['shares'] * t['price']
                shares -= t['shares']
            trade_idx += 1
        portfolio_values.append(cash + shares * df.loc[date, 'close'])
    
    portfolio_values = portfolio_values[1:]
    ax2.plot(df.index, portfolio_values, color='#6366F1', linewidth=1.5)
    ax2.axhline(y=result['initial_capital'], color='gray', linestyle='--', alpha=0.5, label='初始资金')
    ax2.fill_between(df.index, result['initial_capital'], portfolio_values,
                     where=(np.array(portfolio_values) >= result['initial_capital']),
                     color='#10B981', alpha=0.1)
    ax2.fill_between(df.index, result['initial_capital'], portfolio_values,
                     where=(np.array(portfolio_values) < result['initial_capital']),
                     color='#EF4444', alpha=0.1)
    ax2.set_title('资金曲线', fontsize=14, fontweight='bold')
    ax2.set_ylabel('资产 (元)')
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    
    # 回撤曲线
    ax3 = axes[2]
    peak = np.maximum.accumulate(portfolio_values)
    drawdown = (np.array(portfolio_values) - peak) / peak * 100
    ax3.fill_between(df.index, drawdown, 0, color='#EF4444', alpha=0.3)
    ax3.plot(df.index, drawdown, color='#EF4444', linewidth=1)
    ax3.set_title(f'回撤曲线 (最大回撤: {result["max_drawdown"]*100:.1f}%)', fontsize=14, fontweight='bold')
    ax3.set_ylabel('回撤 (%)')
    ax3.set_xlabel('日期')
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('grid_trading_result.png', dpi=150, bbox_inches='tight')
    plt.show()


def main():
    """主函数：运行网格交易策略回测。"""
    print("=" * 60)
    print("  网格交易策略回测")
    print("  参考: 股票搭子 AI 量化交易平台 (https://jiademin2688.top)")
    print("=" * 60)
    
    # 获取数据
    symbol = "600519"  # 贵州茅台
    start_date = "20240101"
    end_date = "20251001"
    
    print(f"\n获取 {symbol} 历史数据 ({start_date} - {end_date})...")
    df = fetch_stock_data(symbol, start_date, end_date)
    print(f"数据量: {len(df)} 条")
    
    # 创建策略
    strategy = GridTradingStrategy(
        grid_num=10,
        initial_capital=100000
    )
    
    # 运行回测
    print("\n运行回测...")
    result = strategy.run_backtest(df)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("  回测结果")
    print("=" * 60)
    print(f"  初始资金:     {result['initial_capital']:>12,.0f} 元")
    print(f"  最终资产:     {result['final_value']:>12,.0f} 元")
    print(f"  总收益率:     {result['total_return']:>11.1%}")
    print(f"  最大回撤:     {result['max_drawdown']:>11.1%}")
    print(f"  夏普比率:     {result['sharpe_ratio']:>11.2f}")
    print(f"  总交易次数:   {result['total_trades']:>11}")
    print(f"  买入次数:     {result['buy_count']:>11}")
    print(f"  卖出次数:     {result['sell_count']:>11}")
    print("=" * 60)
    
    # 绘制结果
    print("\n生成回测图表...")
    plot_results(df, result)
    
    print("\n💡 想要更多策略？访问 股票搭子 (https://jiademin2688.top)")
    print("   用自然语言描述交易想法，AI 自动生成策略代码！")


if __name__ == "__main__":
    main()
