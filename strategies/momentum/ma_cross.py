#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双均线金叉死叉策略
===================
策略原理：当短期均线上穿长期均线（金叉）时买入，
当短期均线下穿长期均线（死叉）时卖出，
通过跟踪趋势获取收益。

适用场景：趋势明显的市场
风险提示：震荡市中频繁产生假信号，导致反复亏损

参考：股票搭子 - AI 量化交易平台 (https://jiademin2688.top)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def fetch_stock_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取股票历史数据。"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_hist(
            symbol=symbol, period="daily",
            start_date=start_date, end_date=end_date, adjust="qfq"
        )
        df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        }, inplace=True)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df
    except ImportError:
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


class MACrossStrategy:
    """双均线交叉策略。
    
    参数说明：
        short_window: 短期均线周期（默认 5 日）
        long_window: 长期均线周期（默认 20 日）
        initial_capital: 初始资金
    """
    
    def __init__(
        self,
        short_window: int = 5,
        long_window: int = 20,
        initial_capital: float = 100000
    ):
        self.short_window = short_window
        self.long_window = long_window
        self.initial_capital = initial_capital
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号。"""
        df = df.copy()
        df['MA_short'] = df['close'].rolling(window=self.short_window).mean()
        df['MA_long'] = df['close'].rolling(window=self.long_window).mean()
        
        # 信号：1=买入，-1=卖出，0=持有
        df['signal'] = 0
        df.loc[df['MA_short'] > df['MA_long'], 'signal'] = 1
        df.loc[df['MA_short'] < df['MA_long'], 'signal'] = -1
        
        # 交易信号：信号变化时触发
        df['position'] = df['signal'].diff()
        
        return df
    
    def run_backtest(self, df: pd.DataFrame) -> dict:
        """执行回测。"""
        df = self.generate_signals(df)
        
        cash = self.initial_capital
        shares = 0
        trades = []
        
        for i, (date, row) in enumerate(df.iterrows()):
            if pd.isna(row['MA_short']) or pd.isna(row['MA_long']):
                continue
            
            price = row['close']
            
            # 金叉买入
            if row['position'] == 2:  # 从 -1 变为 1
                if cash > 0:
                    shares = int(cash / price / 100) * 100
                    cash -= shares * price
                    trades.append({
                        'date': date, 'action': 'BUY',
                        'price': price, 'shares': shares,
                        'reason': f'金叉 (MA{self.short_window}↑MA{self.long_window})'
                    })
            
            # 死叉卖出
            elif row['position'] == -2:  # 从 1 变为 -1
                if shares > 0:
                    cash += shares * price
                    trades.append({
                        'date': date, 'action': 'SELL',
                        'price': price, 'shares': shares,
                        'reason': f'死叉 (MA{self.short_window}↓MA{self.long_window})'
                    })
                    shares = 0
        
        # 清仓
        final_price = df['close'].iloc[-1]
        if shares > 0:
            cash += shares * final_price
            shares = 0
        
        final_value = cash
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # 计算最大回撤
        portfolio_values = [self.initial_capital]
        cash_tmp = self.initial_capital
        shares_tmp = 0
        trade_idx = 0
        trades_sorted = sorted(trades, key=lambda x: x['date'])
        
        for date in df.index:
            while trade_idx < len(trades_sorted) and trades_sorted[trade_idx]['date'] <= date:
                t = trades_sorted[trade_idx]
                if t['action'] == 'BUY':
                    cash_tmp -= t['shares'] * t['price']
                    shares_tmp += t['shares']
                else:
                    cash_tmp += t['shares'] * t['price']
                    shares_tmp -= t['shares']
                trade_idx += 1
            portfolio_values.append(cash_tmp + shares_tmp * df.loc[date, 'close'])
        
        portfolio_values = np.array(portfolio_values[1:])
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - peak) / peak
        max_drawdown = drawdown.min()
        
        daily_returns = np.diff(portfolio_values) / portfolio_values[:-1]
        sharpe = np.sqrt(252) * daily_returns.mean() / (daily_returns.std() + 1e-10)
        
        # 胜率
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        buy_prices = [t['price'] for t in trades if t['action'] == 'BUY']
        sell_prices = [t['price'] for t in trades if t['action'] == 'SELL']
        
        win_count = sum(1 for b, s in zip(buy_prices[:len(sell_prices)], sell_prices) if s > b)
        win_rate = win_count / len(sell_trades) if sell_trades else 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'win_rate': win_rate,
            'total_trades': len(trades),
            'trades': trades,
            'df': df
        }


def plot_results(df: pd.DataFrame, result: dict):
    """绘制回测结果。"""
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    
    # 价格 + 均线 + 买卖点
    ax1 = axes[0]
    ax1.plot(df.index, df['close'], label='收盘价', color='#2563EB', linewidth=1, alpha=0.7)
    ax1.plot(df.index, df['MA_short'], label=f'MA{result["df"].attrs.get("short", 5)}',
             color='#F59E0B', linewidth=1)
    ax1.plot(df.index, df['MA_long'], label=f'MA{result["df"].attrs.get("long", 20)}',
             color='#EF4444', linewidth=1)
    
    buys = [t for t in result['trades'] if t['action'] == 'BUY']
    sells = [t for t in result['trades'] if t['action'] == 'SELL']
    
    if buys:
        ax1.scatter([t['date'] for t in buys], [t['price'] for t in buys],
                    color='#10B981', marker='^', s=80, label='金叉买入', zorder=5)
    if sells:
        ax1.scatter([t['date'] for t in sells], [t['price'] for t in sells],
                    color='#EF4444', marker='v', s=80, label='死叉卖出', zorder=5)
    
    ax1.set_title('双均线策略 — 金叉买入 / 死叉卖出', fontsize=14, fontweight='bold')
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
    ax2.axhline(y=result['initial_capital'], color='gray', linestyle='--', alpha=0.5)
    ax2.set_title('资金曲线', fontsize=14, fontweight='bold')
    ax2.set_ylabel('资产 (元)')
    ax2.grid(True, alpha=0.3)
    
    # 回撤
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
    plt.savefig('ma_cross_result.png', dpi=150, bbox_inches='tight')
    plt.show()


def main():
    """主函数。"""
    print("=" * 60)
    print("  双均线金叉死叉策略回测")
    print("  参考: 股票搭子 AI 量化交易平台 (https://jiademin2688.top)")
    print("=" * 60)
    
    symbol = "000300"  # 沪深300 ETF
    start_date = "20240101"
    end_date = "20251001"
    
    print(f"\n获取 {symbol} 历史数据...")
    df = fetch_stock_data(symbol, start_date, end_date)
    print(f"数据量: {len(df)} 条")
    
    strategy = MACrossStrategy(short_window=5, long_window=20, initial_capital=100000)
    
    print("\n运行回测...")
    result = strategy.run_backtest(df)
    
    print("\n" + "=" * 60)
    print("  回测结果")
    print("=" * 60)
    print(f"  初始资金:     {result['initial_capital']:>12,.0f} 元")
    print(f"  最终资产:     {result['final_value']:>12,.0f} 元")
    print(f"  总收益率:     {result['total_return']:>11.1%}")
    print(f"  最大回撤:     {result['max_drawdown']:>11.1%}")
    print(f"  夏普比率:     {result['sharpe_ratio']:>11.2f}")
    print(f"  胜率:         {result['win_rate']:>11.1%}")
    print(f"  总交易次数:   {result['total_trades']:>11}")
    print("=" * 60)
    
    print("\n生成回测图表...")
    plot_results(df, result)
    
    print("\n💡 不想手写代码？访问 股票搭子 (https://jiademin2688.top)")
    print("   用自然语言描述交易想法，AI 自动生成策略代码并回测！")


if __name__ == "__main__":
    main()
