# 🐂 基础设施模块
# 优雅的依赖倒置实现

import sqlite3
import json
from abc import ABC
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import asdict

import akshare as ak

from .core import (
    MarketDataProvider, PortfolioRepository, SignalNotifier,
    MarketData, Portfolio, TradingSignal, BacktestResult,
    AnalysisConfig
)


class AKShareMarketDataProvider(MarketDataProvider):
    """AKShare市场数据提供者"""

    def __init__(self):
        self._cache = {}
        self._cache_timestamps = {}

    def get_sector_stocks(self, sector_code: str) -> List[MarketData]:
        """
        获取板块成分股数据
        使用AKShare获取实时数据
        """
        try:
            # 检查缓存
            cache_key = f"sector_{sector_code}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5分钟缓存
                return self._cache[cache_key]

            # 获取板块数据
            df = ak.stock_board_concept_cons_em(symbol=sector_code)

            market_data_list = []
            for _, row in df.iterrows():
                # 构造MarketData对象
                market_data = MarketData(
                    symbol=row['代码'],
                    name=row['名称'],
                    price=float(row.get('最新价', 0)),
                    change_pct=float(row.get('涨跌幅', 0)),
                    volume=int(row.get('成交量', 0)),
                    amount=float(row.get('成交额', 0)),
                    sector=sector_code,
                    timestamp=datetime.now(),
                    additional_data={
                        'avg_volume': row.get('量比', 1) * 100000,  # 估算平均成交量
                        'market_cap': row.get('总市值', 0),
                        'pe_ratio': row.get('市盈率-动态', 0),
                    }
                )
                market_data_list.append(market_data)

            # 更新缓存
            self._cache[cache_key] = market_data_list
            self._cache_timestamps[cache_key] = datetime.now().timestamp()

            return market_data_list

        except Exception as e:
            print(f"获取板块数据失败 {sector_code}: {e}")
            return []

    def get_stock_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取股票历史数据
        """
        try:
            cache_key = f"history_{symbol}_{days}"
            if self._is_cache_valid(cache_key, ttl=1800):  # 30分钟缓存
                return self._cache[cache_key]

            # 获取历史数据
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date="20240101")
            recent_data = df.tail(days)

            history_list = []
            for _, row in recent_data.iterrows():
                history_list.append({
                    'date': row['日期'],
                    'open': float(row['开盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'close': float(row['收盘']),
                    'volume': int(row['成交量']),
                    'amount': float(row['成交额']),
                    'change_pct': float(row['涨跌幅']),
                })

            # 更新缓存
            self._cache[cache_key] = history_list
            self._cache_timestamps[cache_key] = datetime.now().timestamp()

            return history_list

        except Exception as e:
            print(f"获取历史数据失败 {symbol}: {e}")
            return []

    def get_market_sentiment(self) -> float:
        """
        获取市场情绪指标
        返回0-100之间的情绪分数
        """
        try:
            cache_key = "market_sentiment"
            if self._is_cache_valid(cache_key, ttl=60):  # 1分钟缓存
                return self._cache[cache_key]

            # 获取市场整体数据
            market_data = ak.stock_zh_a_spot_em()

            # 计算情绪指标
            total_stocks = len(market_data)
            rising_stocks = len(market_data[market_data['涨跌幅'] > 0])
            falling_stocks = len(market_data[market_data['涨跌幅'] < 0])

            # 涨停股比例
            limit_up_stocks = len(market_data[market_data['涨跌幅'] >= 9.8])
            limit_up_ratio = limit_up_stocks / total_stocks if total_stocks > 0 else 0

            # 计算综合情绪分数
            sentiment_score = 50.0  # 基准分

            # 上涨家数占比
            rising_ratio = rising_stocks / total_stocks if total_stocks > 0 else 0
            sentiment_score += (rising_ratio - 0.5) * 40

            # 涨停股过多表示情绪过热
            if limit_up_ratio > 0.05:
                sentiment_score -= 20
            elif limit_up_ratio > 0.02:
                sentiment_score += 10

            # 确保分数在0-100范围内
            sentiment_score = max(0, min(100, sentiment_score))

            # 更新缓存
            self._cache[cache_key] = sentiment_score
            self._cache_timestamps[cache_key] = datetime.now().timestamp()

            return sentiment_score

        except Exception as e:
            print(f"获取市场情绪失败: {e}")
            return 50.0  # 返回中性情绪

    def _is_cache_valid(self, cache_key: str, ttl: int) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache_timestamps:
            return False

        elapsed = datetime.now().timestamp() - self._cache_timestamps[cache_key]
        return elapsed < ttl


class SQLitePortfolioRepository(PortfolioRepository):
    """SQLite投资组合仓库"""

    def __init__(self, db_path: str = "data/db/portfolio.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cash REAL NOT NULL,
                    positions TEXT,  -- JSON格式
                    total_value REAL NOT NULL,
                    daily_pnl REAL NOT NULL,
                    total_pnl REAL NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config TEXT,  -- JSON格式
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    trading_days INTEGER,
                    total_signals INTEGER,
                    executed_trades INTEGER,
                    trade_records TEXT,  -- JSON格式
                    daily_results TEXT,  -- JSON格式
                    performance_analysis TEXT,  -- JSON格式
                    risk_metrics TEXT,  -- JSON格式
                    final_portfolio TEXT,  -- JSON格式
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save_portfolio(self, portfolio: Portfolio) -> None:
        """保存投资组合"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO portfolio (cash, positions, total_value, daily_pnl, total_pnl)
                VALUES (?, ?, ?, ?, ?)
            """, (
                portfolio.cash,
                json.dumps(portfolio.positions),
                portfolio.total_value,
                portfolio.daily_pnl,
                portfolio.total_pnl
            ))

    def load_portfolio(self) -> Portfolio:
        """加载最新的投资组合"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT cash, positions, total_value, daily_pnl, total_pnl
                FROM portfolio
                ORDER BY updated_at DESC
                LIMIT 1
            """)

            row = cursor.fetchone()
            if row:
                return Portfolio(
                    cash=row[0],
                    positions=json.loads(row[1]),
                    total_value=row[2],
                    daily_pnl=row[3],
                    total_pnl=row[4]
                )

        # 返回默认投资组合
        return Portfolio()

    def save_backtest_result(self, result: BacktestResult) -> None:
        """保存回测结果"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO backtest_results (
                    config, start_date, end_date, trading_days, total_signals,
                    executed_trades, trade_records, daily_results,
                    performance_analysis, risk_metrics, final_portfolio
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                json.dumps(asdict(result.config)),
                result.start_date.isoformat(),
                result.end_date.isoformat(),
                result.trading_days,
                result.total_signals,
                result.executed_trades,
                json.dumps([asdict(tr) for tr in result.trade_records]),
                json.dumps(result.daily_results),
                json.dumps(result.performance_analysis),
                json.dumps(asdict(result.risk_metrics)),
                json.dumps({
                    'cash': result.final_portfolio.cash,
                    'positions': result.final_portfolio.positions,
                    'total_value': result.final_portfolio.total_value,
                    'daily_pnl': result.final_portfolio.daily_pnl,
                    'total_pnl': result.final_portfolio.total_pnl,
                })
            ))


class ConsoleSignalNotifier(SignalNotifier):
    """控制台信号通知器"""

    def notify_signal(self, signal: TradingSignal) -> None:
        """控制台输出信号通知"""
        print(f"📡 交易信号: {signal.name}({signal.symbol}) - {signal.action.value}")
        print(f"   置信度: {signal.confidence}%, 价格: ¥{signal.price:.2f}")
        print(f"   理由: {signal.reason}")
        print(f"   风险等级: {signal.risk_level.value}")
        print("-" * 50)

    def notify_backtest_result(self, result: BacktestResult) -> None:
        """控制台输出回测结果通知"""
        print("📊 回测完成！")
        print(f"总收益率: {result.total_return_pct:.2f}%")
        print(f"胜率: {result.risk_metrics.win_rate:.1f}%")
        print(f"最大回撤: {result.risk_metrics.max_drawdown:.2f}%")
        print(f"夏普比率: {result.risk_metrics.sharpe_ratio:.2f}")
        print(f"总交易: {result.executed_trades}")
        print("-" * 50)


class EmailSignalNotifier(SignalNotifier):
    """邮件信号通知器"""

    def __init__(self, smtp_config: Dict[str, str]):
        self.smtp_config = smtp_config

    def notify_signal(self, signal: TradingSignal) -> None:
        """发送邮件通知信号"""
        # 这里实现邮件发送逻辑
        print(f"📧 发送邮件通知信号: {signal.name}({signal.symbol})")

    def notify_backtest_result(self, result: BacktestResult) -> None:
        """发送邮件通知回测结果"""
        print("📧 发送邮件通知回测结果")


class WebhookSignalNotifier(SignalNotifier):
    """Webhook信号通知器"""

    def __init__(self, webhook_url: str, webhook_type: str = "dingtalk"):
        self.webhook_url = webhook_url
        self.webhook_type = webhook_type

    def notify_signal(self, signal: TradingSignal) -> None:
        """发送Webhook通知信号"""
        print(f"🔗 发送Webhook通知: {signal.name}({signal.symbol})")

    def notify_backtest_result(self, result: BacktestResult) -> None:
        """发送Webhook通知回测结果"""
        print("🔗 发送Webhook通知回测结果")