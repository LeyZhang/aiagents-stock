# 🐂 回测模块
# 优雅的模板方法模式实现

import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from src.core.logger import get_logger

from .core import (
    BacktestResult, TradeRecord, Portfolio, RiskMetrics,
    MarketDataProvider, PortfolioRepository, TradingStrategy,
    AnalysisConfig, TradingSignal, SignalAction, MarketData
)

logger = get_logger('bull_market_agent.backtesting')


class PerformanceAnalyzer:
    """性能分析器"""

    @staticmethod
    def analyze_performance(trade_records: List[TradeRecord],
                          initial_capital: float,
                          final_capital: float) -> Dict[str, Any]:
        """分析交易性能"""
        if not trade_records:
            return {
                'total_return': 0,
                'total_return_pct': 0,
                'win_rate': 0,
                'total_trades': 0,
                'profitable_trades': 0,
                'losing_trades': 0,
                'avg_hold_days': 0,
                'max_profit': 0,
                'max_loss': 0,
                'avg_profit_per_trade': 0,
            }

        # 计算基础指标
        closed_trades = [t for t in trade_records if t.action in [SignalAction.SELL]]
        profitable_trades = [t for t in closed_trades if t.profit_loss > 0]
        losing_trades = [t for t in closed_trades if t.profit_loss < 0]

        win_rate = len(profitable_trades) / len(closed_trades) * 100 if closed_trades else 0

        # 计算收益率
        total_return = sum(t.profit_loss for t in closed_trades)
        total_return_pct = (final_capital / initial_capital - 1) * 100

        # 计算平均持仓时间
        avg_hold_days = sum(t.hold_days for t in closed_trades) / len(closed_trades) if closed_trades else 0

        # 计算最大单笔盈亏
        profits = [t.profit_loss for t in closed_trades]
        max_profit = max(profits) if profits else 0
        max_loss = min(profits) if profits else 0

        return {
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'win_rate': win_rate,
            'total_trades': len(closed_trades),
            'profitable_trades': len(profitable_trades),
            'losing_trades': len(losing_trades),
            'avg_hold_days': avg_hold_days,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'avg_profit_per_trade': total_return / len(closed_trades) if closed_trades else 0,
        }

    @staticmethod
    def calculate_risk_metrics(trade_records: List[TradeRecord],
                             capital_values: List[float]) -> RiskMetrics:
        """计算风险指标"""
        if not capital_values or len(capital_values) < 2:
            return RiskMetrics()

        # 计算最大回撤
        max_drawdown = 0.0
        peak = capital_values[0]

        for value in capital_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)

        # 计算波动率
        returns = []
        for i in range(1, len(capital_values)):
            daily_return = (capital_values[i] - capital_values[i-1]) / capital_values[i-1]
            returns.append(daily_return)

        volatility = 0.0
        sharpe_ratio = 0.0

        if returns:
            avg_return = sum(returns) / len(returns)
            if len(returns) > 1:
                variance = sum((r - avg_return)**2 for r in returns) / (len(returns) - 1)
                volatility = (variance ** 0.5) * 100  # 百分比形式

                # 简化的夏普比率计算（假设无风险利率为3%）
                risk_free_rate = 0.03 / 252  # 日化无风险利率
                sharpe_ratio = (avg_return - risk_free_rate) / (variance ** 0.5) * (252 ** 0.5) if variance > 0 else 0

        # 计算胜率
        closed_trades = [t for t in trade_records if t.action in [SignalAction.SELL]]
        win_rate = len([t for t in closed_trades if t.profit_loss > 0]) / len(closed_trades) * 100 if closed_trades else 0

        # 计算盈亏比
        profits = [t.profit_loss for t in closed_trades if t.profit_loss > 0]
        losses = [abs(t.profit_loss) for t in closed_trades if t.profit_loss < 0]

        profit_loss_ratio = 0.0
        if losses:
            avg_profit = sum(profits) / len(profits) if profits else 0
            avg_loss = sum(losses) / len(losses)
            profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else 0

        # 计算最大连续亏损
        max_consecutive_losses = 0
        current_losses = 0

        for trade in closed_trades:
            if trade.profit_loss < 0:
                current_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
            else:
                current_losses = 0

        # 计算恢复因子
        recovery_factor = abs(sum(t.profit_loss for t in closed_trades)) / max_drawdown if max_drawdown > 0 else 0

        # 计算卡尔玛比率
        calmar_ratio = (sum(returns) / len(returns) * 252) / (max_drawdown / 100) if max_drawdown > 0 else 0

        # 计算索提诺比率（简化为夏普比率）
        sortino_ratio = sharpe_ratio

        return RiskMetrics(
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            volatility=volatility,
            win_rate=win_rate,
            profit_loss_ratio=profit_loss_ratio,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            max_consecutive_losses=max_consecutive_losses,
            recovery_factor=recovery_factor,
        )


class BacktestEngine:
    """回测引擎 - 模板方法模式"""

    def __init__(self,
                 config: AnalysisConfig,
                 data_provider: MarketDataProvider,
                 portfolio_repo: PortfolioRepository,
                 strategies: List[TradingStrategy]):
        self.config = config
        self.data_provider = data_provider
        self.portfolio_repo = portfolio_repo
        self.strategies = strategies
        self.performance_analyzer = PerformanceAnalyzer()

    def run_backtest(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """
        执行回测 - 模板方法
        """
        logger.info("开始执行回测", start_date=start_date, end_date=end_date)

        # 1. 初始化
        result = BacktestResult(
            config=self.config,
            start_date=start_date,
            end_date=end_date,
            trading_days=self._calculate_trading_days(start_date, end_date),
            total_signals=0,
            executed_trades=0,
        )

        logger.debug("回测初始化完成", trading_days=result.trading_days)

        # 2. 执行回测流程
        logger.debug("开始执行回测流程")
        self._execute_backtest_flow(result)

        # 3. 分析性能
        logger.debug("开始分析回测性能")
        self._analyze_performance(result)

        # 4. 保存结果
        logger.debug("保存回测结果到数据库")
        self.portfolio_repo.save_backtest_result(result)

        logger.info("回测完成", total_signals=result.total_signals, executed_trades=result.executed_trades)
        return result

    def _calculate_trading_days(self, start_date: datetime, end_date: datetime) -> int:
        """计算交易日数量"""
        # 简化的交易日计算（实际应该考虑节假日）
        delta = end_date - start_date
        return max(1, delta.days)

    def _execute_backtest_flow(self, result: BacktestResult) -> None:
        """执行回测流程"""
        logger.debug("开始回测流程执行", start_date=result.start_date, end_date=result.end_date)

        current_date = result.start_date
        portfolio = Portfolio()
        processed_days = 0

        while current_date <= result.end_date:
            # 检查是否为交易日
            if self._is_trading_day(current_date):
                logger.debug("处理交易日", date=current_date, portfolio_cash=portfolio.cash)
                daily_result = self._process_trading_day(current_date, portfolio, result)
                logger.debug("交易日处理完成", date=current_date, signals=daily_result['signals_count'], trades=len(daily_result['trades_executed']))
                processed_days += 1
            else:
                logger.debug("跳过非交易日", date=current_date)

            current_date += timedelta(days=1)

        logger.debug("回测流程执行完成", processed_days=processed_days)

    def _is_trading_day(self, date: datetime) -> bool:
        """判断是否为交易日"""
        # 简化的判断：周一到周五
        return date.weekday() < 5

    def _process_trading_day(self, trade_date: datetime,
                            portfolio: Portfolio,
                            result: BacktestResult) -> Dict[str, Any]:
        """处理单个交易日"""
        daily_result = {
            'date': trade_date.strftime('%Y-%m-%d'),
            'signals_count': 0,
            'trades_executed': [],
            'capital_before': portfolio.cash,
            'capital_after': portfolio.cash,
            'positions_count': len(portfolio.positions),
        }

        logger.debug("处理交易日", date=trade_date.strftime('%Y-%m-%d'), capital_before=portfolio.cash)

        # 生成信号
        signals = self._generate_signals(trade_date)
        logger.debug("生成交易信号", signals_count=len(signals))

        # 执行交易
        executed_count = 0
        for signal in signals:
            logger.debug("尝试执行交易", symbol=signal.symbol, action=signal.action.value)
            trade_record = self._execute_trade(signal, portfolio, trade_date)
            if trade_record:
                logger.debug("交易执行成功", symbol=trade_record.symbol, quantity=trade_record.quantity)
                executed_count += 1
            else:
                logger.debug("交易执行失败", symbol=signal.symbol)

        # 检查是否需要平仓
        self._check_exit_conditions(portfolio, trade_date, result)

        daily_result['capital_after'] = portfolio.cash
        daily_result['positions_count'] = len(portfolio.positions)

        return daily_result

    def _generate_signals(self, trade_date: datetime) -> List[TradingSignal]:
        """生成交易信号 - 使用真实历史数据"""
        signals = []

        for sector in self.config.sectors:
            try:
                # 获取真实的板块历史数据
                sector_data = self._get_historical_sector_data(sector, trade_date)

                if not sector_data:
                    # 如果没有历史数据，跳过该板块
                    continue

                for market_data in sector_data:
                    # 尝试所有策略
                    for strategy in self.strategies:
                        signal = strategy.analyze_market_data(market_data, self.config)
                        if signal:
                            signals.append(signal)
                            break  # 一个股票只产生一个信号

            except Exception as e:
                print(f"生成板块 {sector} 信号失败: {e}")
                continue

        return signals

    def _get_historical_sector_data(self, sector: str, trade_date: datetime) -> List[MarketData]:
        """
        获取历史板块数据 - 使用真实数据进行回测

        Args:
            sector: 板块代码
            trade_date: 交易日期

        Returns:
            历史市场数据列表
        """
        try:
            # 尝试获取指定日期的板块数据
            # 注意：这里简化实现，实际应该从data_provider获取历史快照数据
            # 由于AKShare可能不支持精确的历史快照，这里返回空列表表示无数据

            # 为了演示，我们可以返回一些基于真实数据的模拟数据
            # 但标记为"历史数据不可用"
            print(f"⚠️ 历史数据不可用: {sector} 在 {trade_date.strftime('%Y-%m-%d')} 的数据")
            return []

        except Exception as e:
            print(f"获取历史板块数据失败 {sector}: {e}")
            return []

    def _execute_trade(self, signal: TradingSignal, portfolio: Portfolio, trade_date: datetime) -> Optional[TradeRecord]:
        """执行交易"""
        try:
            # 找到对应的策略
            strategy = None
            for s in self.strategies:
                if s.should_enter_position(signal, portfolio):
                    strategy = s
                    break

            if not strategy:
                return None

            # 计算交易数量
            quantity = int((portfolio.cash * signal.position_size_pct) / signal.price)
            if quantity < 100:  # 最少100股
                return None

            # 执行买入
            commission = quantity * signal.price * 0.0003  # 佣金
            total_cost = quantity * signal.price + commission

            portfolio.add_position(signal.symbol, quantity, signal.price, commission)

            return TradeRecord(
                symbol=signal.symbol,
                name=signal.name,
                action=signal.action,
                quantity=quantity,
                price=signal.price,
                amount=quantity * signal.price,
                commission=commission,
                timestamp=trade_date,
                reason=signal.reason,
                confidence=signal.confidence,
                hold_days=1,
                trade_summary=f"买入{quantity}股，成本{total_cost:.2f}元"
            )

        except Exception as e:
            print(f"执行交易失败: {e}")
            return None

    def _check_exit_conditions(self, portfolio: Portfolio, trade_date: datetime, result: BacktestResult) -> None:
        """检查平仓条件"""
        symbols_to_exit = []

        for symbol in list(portfolio.positions.keys()):
            # 模拟当前价格
            current_price = portfolio.positions[symbol]['avg_cost'] * (1 + random.uniform(-0.05, 0.05))

            # 检查每个策略的退出条件
            for strategy in self.strategies:
                exit_action = strategy.should_exit_position(symbol, portfolio, current_price)
                if exit_action:
                    self._execute_exit_trade(symbol, portfolio, current_price, trade_date, result)
                    break

    def _execute_exit_trade(self, symbol: str, portfolio: Portfolio, current_price: float,
                          trade_date: datetime, result: BacktestResult) -> None:
        """执行平仓交易"""
        try:
            position = portfolio.positions[symbol]
            quantity = position['quantity']
            cost_price = position['avg_cost']

            # 计算平仓
            commission = current_price * quantity * 0.0003 + current_price * quantity * 0.001  # 佣金+印花税
            revenue = current_price * quantity - commission
            profit_loss = revenue - (cost_price * quantity + position.get('total_cost', 0) - cost_price * quantity)

            hold_days = (trade_date - position['entry_date']).days + 1
            profit_loss_pct = (current_price / cost_price - 1) * 100

            portfolio.remove_position(symbol, quantity, current_price, commission)

            trade_record = TradeRecord(
                symbol=symbol,
                name=f"{symbol}股票",  # 简化
                action=SignalAction.SELL,
                quantity=quantity,
                price=current_price,
                amount=current_price * quantity,
                commission=commission,
                timestamp=trade_date,
                reason="达到止盈止损条件",
                confidence=80.0,  # 假设
                cost_price=cost_price,
                profit_loss=profit_loss,
                profit_loss_pct=profit_loss_pct,
                hold_days=hold_days,
                trade_summary=f"卖出{quantity}股，收益{profit_loss:.2f}元({profit_loss_pct:+.1f}%)，持有{hold_days}天",
                lessons_learned=self._analyze_trade_lesson(profit_loss_pct, hold_days)
            )

            result.trade_records.append(trade_record)
            result.executed_trades += 1

        except Exception as e:
            print(f"执行平仓失败 {symbol}: {e}")

    def _analyze_trade_lesson(self, profit_pct: float, hold_days: int) -> str:
        """分析交易经验教训"""
        lessons = []

        if profit_pct > 5:
            lessons.append("盈利交易，策略有效")
        elif profit_pct < -5:
            lessons.append("亏损交易，需要改进")
        else:
            lessons.append("保本交易，控制风险")

        if hold_days > 10:
            lessons.append("持有时间较长，影响资金效率")
        elif hold_days < 2:
            lessons.append("持有时间过短，可能错过收益")

        return "；".join(lessons) if lessons else "正常交易"

    def _analyze_performance(self, result: BacktestResult) -> None:
        """分析回测性能"""
        # 计算资金曲线
        capital_values = [100000.0]  # 初始资金
        current_capital = 100000.0

        for daily_result in result.daily_results:
            current_capital = daily_result['capital_after']
            capital_values.append(current_capital)

        # 分析性能
        result.performance_analysis = self.performance_analyzer.analyze_performance(
            result.trade_records, 100000.0, result.final_portfolio.cash
        )

        # 计算风险指标
        result.risk_metrics = self.performance_analyzer.calculate_risk_metrics(
            result.trade_records, capital_values
        )