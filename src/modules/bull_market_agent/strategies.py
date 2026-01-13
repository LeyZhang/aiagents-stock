# 🐂 交易策略模块
# 优雅的策略模式实现

import random
from abc import ABC, abstractmethod
from datetime import datetime, time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from abc import ABC, abstractmethod
from typing import Optional, List

from src.core.logger import get_logger

from .domain.entities import TradingSignal, Portfolio
from .domain.value_objects import MarketData, AnalysisConfig, SignalAction, RiskLevel
from .core import TradingStrategy

logger = get_logger('bull_market_agent.strategies')


class BaseStrategy(TradingStrategy):
    """策略基类"""

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    # Implement abstract methods with default behavior
    def analyze_market_data(self, market_data: MarketData, config: AnalysisConfig) -> Optional[TradingSignal]:
        """默认实现 - 子类需要重写"""
        return None

    def should_enter_position(self, signal: TradingSignal, portfolio: Portfolio) -> bool:
        """默认实现 - 子类需要重写"""
        return False

    def should_exit_position(self, symbol: str, portfolio: Portfolio, current_price: float) -> Optional[SignalAction]:
        """默认实现 - 子类需要重写"""
        return None

    def _get_time_slot(self, current_time: datetime) -> str:
        """获取时间段"""
        time_slots = {
            'early_morning': (time(9, 15), time(9, 30)),
            'morning_session': (time(9, 30), time(11, 30)),
            'afternoon_session': (time(13, 0), time(14, 30)),
            'late_afternoon': (time(14, 30), time(15, 0)),
        }

        current_t = current_time.time()
        for slot_name, (start_time, end_time) in time_slots.items():
            if start_time <= current_t <= end_time:
                return slot_name

        return 'non_trading'

    def _calculate_position_size(self, signal: TradingSignal, config: AnalysisConfig) -> float:
        """计算仓位大小"""
        base_size = config.max_position_size
        confidence_factor = signal.confidence / 100.0
        return base_size * confidence_factor


class TPlusOneStrategy(BaseStrategy):
    """T+1时空折叠策略"""

    def __init__(self):
        super().__init__("T+1时空折叠策略")

    def analyze_market_data(self, market_data: MarketData, config: AnalysisConfig) -> Optional[TradingSignal]:
        """
        T+1时空折叠策略分析
        核心逻辑：时间决定策略，T+1限制风险
        """
        logger.info("开始T+1时空折叠策略分析", symbol=market_data.symbol, price=market_data.price, change_pct=market_data.change_pct)

        current_time = datetime.now()
        time_slot = self._get_time_slot(current_time)
        logger.debug("确定时间段", current_time=current_time, time_slot=time_slot)

        # 非交易时间不产生信号
        if time_slot == 'non_trading':
            logger.debug("非交易时间，跳过分析", symbol=market_data.symbol)
            return None

        # 非交易时间不产生信号
        if time_slot == 'non_trading':
            return None

        # 根据时间段执行不同策略
        logger.debug("根据时间段选择策略", symbol=market_data.symbol, time_slot=time_slot)

        if time_slot == 'early_morning':
            logger.debug("执行早盘竞价策略", symbol=market_data.symbol)
            return self._early_morning_strategy(market_data, config)
        elif time_slot in ['morning_session', 'afternoon_session']:
            logger.debug("执行盘中交易策略", symbol=market_data.symbol)
            return self._intraday_trading_strategy(market_data, config)
        elif time_slot == 'late_afternoon':
            logger.debug("执行尾盘策略", symbol=market_data.symbol)
            return self._late_afternoon_strategy(market_data, config)

        logger.debug("无匹配策略，跳过分析", symbol=market_data.symbol, time_slot=time_slot)
        return None

    def _early_morning_strategy(self, market_data: MarketData, config: AnalysisConfig) -> Optional[TradingSignal]:
        """早盘竞价策略：收割者模式"""
        logger.debug("执行早盘竞价策略检查", symbol=market_data.symbol, change_pct=market_data.change_pct)

        # 这里简化实现，实际应该基于竞价数据
        if market_data.change_pct < -2.0:
            logger.info("触发早盘卖出信号", symbol=market_data.symbol, change_pct=market_data.change_pct)
            return TradingSignal(
                symbol=market_data.symbol,
                name=market_data.name,
                sector=market_data.sector,
                action=SignalAction.SELL,
                confidence=85.0,
                price=market_data.price,
                reason="竞价低开+缩量，主力出货迹象",
                timestamp=datetime.now(),
                detailed_reasons=[
                    "早盘竞价策略：收割者模式，只卖不买",
                    "竞价低开超过2%，可能存在重大利空",
                    "成交量萎缩，主力出货迹象明显"
                ],
                risk_level=RiskLevel.LOW,
                stop_loss_plan="立即执行，无需等待",
                take_profit_plan="不适用",
                market_condition="早盘竞价阶段，风险较高"
            )
        return None

    def _intraday_trading_strategy(self, market_data: MarketData, config: AnalysisConfig) -> Optional[TradingSignal]:
        """盘中策略：趋势守门员模式"""
        # 简化的盘中策略
        if market_data.change_pct > 3.0 and market_data.volume > market_data.additional_data.get('avg_volume', 0) * 1.5:
            return TradingSignal(
                symbol=market_data.symbol,
                name=market_data.name,
                sector=market_data.sector,
                action=SignalAction.HOLD,
                confidence=75.0,
                price=market_data.price,
                reason="盘中放量上涨，保持观望",
                timestamp=datetime.now(),
                detailed_reasons=[
                    "盘中趋势守门员模式",
                    f"涨幅达到{market_data.change_pct:.1f}%，超出正常范围",
                    f"成交量放大{market_data.volume / market_data.additional_data.get('avg_volume', 1):.1f}倍"
                ],
                risk_level=RiskLevel.MEDIUM,
                position_size_pct=self._calculate_position_size(
                    TradingSignal("", "", "", SignalAction.HOLD, 75.0, 0, "", datetime.now()), config
                ),
                stop_loss_plan=f"跌破{market_data.price * 0.97:.2f}元止损",
                take_profit_plan=f"涨幅达到{market_data.price * 1.05:.2f}元考虑减仓",
                market_condition="盘中交易时段，流动性较好"
            )
        return None

    def _late_afternoon_strategy(self, market_data: MarketData, config: AnalysisConfig) -> Optional[TradingSignal]:
        """尾盘策略：黄金30分钟"""
        logger.debug("执行尾盘策略检查", symbol=market_data.symbol, change_pct=market_data.change_pct)

        if market_data.change_pct < -2.0:
            logger.info("触发尾盘买入信号", symbol=market_data.symbol, change_pct=market_data.change_pct)
            return TradingSignal(
                symbol=market_data.symbol,
                name=market_data.name,
                sector=market_data.sector,
                action=SignalAction.BUY,
                confidence=82.0,
                price=market_data.price,
                reason="首阴反包模式，大盘跌它不跌",
                timestamp=datetime.now(),
                detailed_reasons=[
                    "尾盘黄金30分钟策略",
                    f"收盘前跌幅{market_data.change_pct:.1f}%，存在反弹机会",
                    "T+1策略，明天才能卖出，风险相对可控"
                ],
                expected_profit_scenarios={
                    '乐观': f"+{market_data.price * 1.08:.2f}元 (+8%)",
                    '中性': f"+{market_data.price * 1.05:.2f}元 (+5%)",
                    '保守': f"+{market_data.price * 1.02:.2f}元 (+2%)"
                },
                risk_level=RiskLevel.MEDIUM,
                position_size_pct=self._calculate_position_size(
                    TradingSignal("", "", "", SignalAction.BUY, 82.0, 0, "", datetime.now()), config
                ),
                stop_loss_plan=f"跌破{market_data.price * 0.95:.2f}元止损",
                take_profit_plan=f"涨幅达到{market_data.price * 1.10:.2f}元止盈",
                market_condition="尾盘交易时段，适合低风险布局"
            )
        return None

    def should_enter_position(self, signal: TradingSignal, portfolio: Portfolio) -> bool:
        """判断是否应该开仓"""
        if signal.action != SignalAction.BUY:
            return False

        # 检查现金是否足够
        max_position_value = portfolio.cash * signal.position_size_pct
        if max_position_value < signal.price * 100:  # 最少100股
            return False

        # 检查是否已经持仓
        if signal.symbol in portfolio.positions:
            return False

        return True

    def should_exit_position(self, symbol: str, portfolio: Portfolio, current_price: float) -> Optional[SignalAction]:
        """判断是否应该平仓"""
        if symbol not in portfolio.positions:
            return None

        position = portfolio.positions[symbol]
        cost_price = position['avg_cost']
        profit_pct = (current_price / cost_price - 1) * 100

        # 止盈：盈利超过8%
        if profit_pct >= 8.0:
            return SignalAction.SELL

        # 止损：亏损超过5%
        if profit_pct <= -5.0:
            return SignalAction.SELL

        return None


class MomentumStrategy(BaseStrategy):
    """动量策略"""

    def __init__(self):
        super().__init__("动量策略")

    def analyze_market_data(self, market_data: MarketData, config: AnalysisConfig) -> Optional[TradingSignal]:
        """动量策略分析"""
        # 简化的动量策略：涨幅大且成交量放大的股票
        if (market_data.change_pct > 5.0 and
            market_data.volume > market_data.additional_data.get('avg_volume', 0) * 2.0):

            return TradingSignal(
                symbol=market_data.symbol,
                name=market_data.name,
                sector=market_data.sector,
                action=SignalAction.BUY,
                confidence=min(95.0, market_data.change_pct),
                price=market_data.price,
                reason=f"动量爆发：涨幅{market_data.change_pct:.1f}%，量能放大",
                timestamp=datetime.now(),
                detailed_reasons=[
                    f"涨幅达到{market_data.change_pct:.1f}%，明显强于市场",
                    f"成交量放大{market_data.volume / market_data.additional_data.get('avg_volume', 1):.1f}倍",
                    "动量效应明显，存在继续上涨动能"
                ],
                expected_profit_scenarios={
                    '乐观': f"+{market_data.price * 1.15:.2f}元 (+15%)",
                    '中性': f"+{market_data.price * 1.08:.2f}元 (+8%)",
                    '保守': f"+{market_data.price * 1.03:.2f}元 (+3%)"
                },
                risk_level=RiskLevel.HIGH,
                position_size_pct=self._calculate_position_size(
                    TradingSignal("", "", "", SignalAction.BUY, min(95.0, market_data.change_pct), 0, "", datetime.now()), config
                ) * 0.8,  # 动量策略稍微降低仓位
                stop_loss_plan=f"跌破{market_data.price * 0.93:.2f}元立即止损",
                take_profit_plan=f"涨幅达到{market_data.price * 1.12:.2f}元分批止盈",
                market_condition="动量行情，波动较大"
            )
        return None

    def should_enter_position(self, signal: TradingSignal, portfolio: Portfolio) -> bool:
        """动量策略开仓判断"""
        return (signal.action == SignalAction.BUY and
                portfolio.cash >= signal.price * 100 and
                signal.symbol not in portfolio.positions)

    def should_exit_position(self, symbol: str, portfolio: Portfolio, current_price: float) -> Optional[SignalAction]:
        """动量策略平仓判断"""
        if symbol not in portfolio.positions:
            return None

        position = portfolio.positions[symbol]
        cost_price = position['avg_cost']
        profit_pct = (current_price / cost_price - 1) * 100

        # 动量策略：快速止盈止损
        if profit_pct >= 12.0 or profit_pct <= -8.0:
            return SignalAction.SELL

        return None


class VolumeStrategy(BaseStrategy):
    """成交量策略"""

    def __init__(self):
        super().__init__("成交量策略")

    def analyze_market_data(self, market_data: MarketData, config: AnalysisConfig) -> Optional[TradingSignal]:
        """成交量策略分析"""
        # 成交量突然放大
        volume_ratio = market_data.volume / market_data.additional_data.get('avg_volume', 1)

        if volume_ratio > 3.0:
            action = SignalAction.BUY if market_data.change_pct > 0 else SignalAction.SELL

            return TradingSignal(
                symbol=market_data.symbol,
                name=market_data.name,
                sector=market_data.sector,
                action=action,
                confidence=min(90.0, volume_ratio * 10),
                price=market_data.price,
                reason=f"量能异动：成交量放大{volume_ratio:.1f}倍",
                timestamp=datetime.now(),
                detailed_reasons=[
                    f"成交量突然放大{volume_ratio:.1f}倍",
                    f"价格变动{market_data.change_pct:+.1f}%，与量能匹配",
                    "可能存在重大消息或资金异动"
                ],
                risk_level=RiskLevel.HIGH,
                position_size_pct=self._calculate_position_size(
                    TradingSignal("", "", "", action, min(90.0, volume_ratio * 10), 0, "", datetime.now()), config
                ) * 0.7,  # 量能策略保守仓位
                stop_loss_plan=f"跌破{market_data.price * 0.96:.2f}元止损",
                take_profit_plan=f"根据量价配合情况动态调整",
                market_condition="量能异动，需谨慎观察"
            )
        return None

    def should_enter_position(self, signal: TradingSignal, portfolio: Portfolio) -> bool:
        """量能策略开仓判断"""
        return (portfolio.cash >= signal.price * 100 and
                signal.symbol not in portfolio.positions)

    def should_exit_position(self, symbol: str, portfolio: Portfolio, current_price: float) -> Optional[SignalAction]:
        """量能策略平仓判断"""
        if symbol not in portfolio.positions:
            return None

        position = portfolio.positions[symbol]
        cost_price = position['avg_cost']
        profit_pct = (current_price / cost_price - 1) * 100

        # 量能策略：中长期持有
        if profit_pct >= 15.0 or profit_pct <= -10.0:
            return SignalAction.SELL

        return None


class SentimentStrategy(BaseStrategy):
    """情绪策略"""

    def __init__(self):
        super().__init__("情绪策略")

    def analyze_market_data(self, market_data: MarketData, config: AnalysisConfig) -> Optional[TradingSignal]:
        """情绪策略分析"""
        # 基于市场情绪的策略
        # 这里简化实现，实际应该结合市场整体情绪
        sentiment_score = random.uniform(0, 100)  # 模拟情绪分数

        if sentiment_score > 80 and market_data.change_pct > 1.0:
            return TradingSignal(
                symbol=market_data.symbol,
                name=market_data.name,
                sector=market_data.sector,
                action=SignalAction.BUY,
                confidence=sentiment_score * 0.9,
                price=market_data.price,
                reason=f"市场情绪乐观，适合布局",
                timestamp=datetime.now(),
                detailed_reasons=[
                    f"市场情绪分数：{sentiment_score:.1f}",
                    f"个股表现稳健：{market_data.change_pct:+.1f}%",
                    "情绪策略：顺势而为"
                ],
                risk_level=RiskLevel.MEDIUM,
                position_size_pct=self._calculate_position_size(
                    TradingSignal("", "", "", SignalAction.BUY, sentiment_score * 0.9, 0, "", datetime.now()), config
                ),
                stop_loss_plan=f"跌破{market_data.price * 0.98:.2f}元止损",
                take_profit_plan=f"根据市场情绪变化调整",
                market_condition="市场情绪乐观，风险偏好较高"
            )
        return None

    def should_enter_position(self, signal: TradingSignal, portfolio: Portfolio) -> bool:
        """情绪策略开仓判断"""
        return (portfolio.cash >= signal.price * 100 and
                signal.symbol not in portfolio.positions)

    def should_exit_position(self, symbol: str, portfolio: Portfolio, current_price: float) -> Optional[SignalAction]:
        """情绪策略平仓判断"""
        if symbol not in portfolio.positions:
            return None

        # 情绪策略：关注市场情绪变化
        # 这里简化实现
        if random.random() < 0.1:  # 10%概率触发卖出
            return SignalAction.SELL

        return None


# 策略工厂
class StrategyFactory:
    """策略工厂"""

    @staticmethod
    def create_strategy(strategy_name: str) -> TradingStrategy:
        """创建策略实例"""
        strategies = {
            't_plus_one': TPlusOneStrategy,
            'momentum': MomentumStrategy,
            'volume': VolumeStrategy,
            'sentiment': SentimentStrategy,
        }

        strategy_class = strategies.get(strategy_name.lower())
        if not strategy_class:
            raise ValueError(f"未知策略: {strategy_name}")

        return strategy_class()

    @staticmethod
    def create_all_strategies() -> List[TradingStrategy]:
        """创建所有策略"""
        return [
            TPlusOneStrategy(),
            MomentumStrategy(),
            VolumeStrategy(),
            SentimentStrategy(),
        ]