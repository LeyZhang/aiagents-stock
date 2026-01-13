# 🐂 领域层
"""
领域层 - 业务核心，包含实体、值对象和领域服务

遵循领域驱动设计(DDD)原则：
- 实体：具有唯一标识和生命周期的业务对象
- 值对象：通过属性值区分的不可变对象
- 领域服务：协调多个实体完成复杂业务逻辑
"""

from .entities import (
    TradingSignal,
    Portfolio,
    TradeRecord,
)

from .value_objects import (
    AnalysisConfig,
    MarketData,
    RiskMetrics,
    BacktestResult,
    SignalAction,
    RiskLevel,
    TimeSlot,
)

from .services.bull_market_analyzer import (
    BullMarketAnalyzer,
)

__all__ = [
    # 实体
    'TradingSignal',
    'Portfolio',
    'TradeRecord',

    # 值对象
    'AnalysisConfig',
    'MarketData',
    'RiskMetrics',
    'BacktestResult',
    'SignalAction',
    'RiskLevel',
    'TimeSlot',

    # 领域服务
    'BullMarketAnalyzer',
]