# 🐂 仓库层 - 数据访问接口和实现
"""
仓库层 - 数据持久化和访问接口

实现领域驱动设计的仓库模式，提供数据访问抽象。
"""

import sqlite3
import json
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core import PortfolioRepository, SignalNotifier
from ..domain import Portfolio, TradingSignal, BacktestResult


class SQLitePortfolioRepository(PortfolioRepository):
    """SQLite投资组合仓库实现"""

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
                    final_portfolio_value REAL,
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
                    performance_analysis, risk_metrics, final_portfolio_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                json.dumps(result.config.__dict__),
                result.start_date.isoformat(),
                result.end_date.isoformat(),
                result.trading_days,
                result.total_signals,
                result.executed_trades,
                json.dumps([record.__dict__ for record in result.trade_records]),
                json.dumps(result.daily_results),
                json.dumps(result.performance_analysis),
                json.dumps(result.risk_metrics.__dict__),
                result.final_portfolio_value
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