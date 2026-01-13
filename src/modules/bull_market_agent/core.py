# 🐂 领域核心模块
"""
领域核心 - 业务规则和接口定义

这是系统的核心业务逻辑层，包含：
- 领域实体和值对象
- 领域服务接口
- 基础设施接口定义
- 业务规则和约束

遵循整洁架构原则，领域层不依赖任何外部框架。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Protocol
from datetime import datetime

# 导入领域对象
from .domain.entities import TradingSignal, Portfolio, TradeRecord
from .domain.value_objects import (
    AnalysisConfig, MarketData, RiskMetrics, BacktestResult,
    SignalAction, RiskLevel
)


# ============================================================================
# 领域服务接口
# ============================================================================

class TradingStrategy(ABC):
    """交易策略接口"""

    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass

    @abstractmethod
    def analyze_market_data(self, market_data: MarketData, config: AnalysisConfig) -> Optional[TradingSignal]:
        """分析市场数据生成交易信号"""
        pass

    @abstractmethod
    def should_enter_position(self, signal: TradingSignal, portfolio: Portfolio) -> bool:
        """判断是否应该开仓"""
        pass

    @abstractmethod
    def should_exit_position(self, symbol: str, portfolio: Portfolio, current_price: float) -> Optional[SignalAction]:
        """判断是否应该平仓"""
        pass


class BullMarketAnalyzerInterface(ABC):
    """牛市分析器领域服务接口"""

    @property
    @abstractmethod
    def config(self) -> AnalysisConfig:
        """获取分析配置"""
        pass

    @abstractmethod
    def scan_market(self) -> List[TradingSignal]:
        """扫描市场生成交易信号"""
        pass

    @abstractmethod
    def run_backtest(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """执行回测分析"""
        pass

    @abstractmethod
    def analyze_single_stock(self, market_data: MarketData) -> Optional[TradingSignal]:
        """分析单个股票"""
        pass

    @abstractmethod
    def calculate_portfolio_value(self, portfolio: Portfolio, price_provider) -> float:
        """计算投资组合价值"""
        pass

    @abstractmethod
    def assess_risk(self, portfolio: Portfolio, signals: List[TradingSignal]) -> RiskMetrics:
        """评估风险指标"""
        pass


# ============================================================================
# 基础设施接口 (依赖倒置)
# ============================================================================

class MarketDataProvider(Protocol):
    """市场数据提供者接口"""

    def get_sector_stocks(self, sector_code: str) -> List[MarketData]:
        """获取板块成分股数据"""
        ...

    def get_stock_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """获取股票历史数据"""
        ...

    def get_market_sentiment(self) -> float:
        """获取市场情绪指标 (0-100)"""
        ...


class PortfolioRepository(Protocol):
    """投资组合仓库接口"""

    def save_portfolio(self, portfolio: Portfolio) -> None:
        """保存投资组合"""
        ...

    def load_portfolio(self) -> Portfolio:
        """加载投资组合"""
        ...

    def save_backtest_result(self, result: BacktestResult) -> None:
        """保存回测结果"""
        ...


class SignalNotifier(Protocol):
    """信号通知器接口"""

    def notify_signal(self, signal: TradingSignal) -> None:
        """通知交易信号"""
        ...

    def notify_backtest_result(self, result: BacktestResult) -> None:
        """通知回测结果"""
        ...


# ============================================================================
# 业务规则和约束
# ============================================================================

class BusinessRules:
    """业务规则定义"""

    # 交易相关
    MIN_TRADE_AMOUNT = 10000  # 最少交易金额1万元
    MAX_POSITION_SIZE = 0.1   # 单股票最大仓位10%
    MIN_CONFIDENCE = 50.0     # 最小置信度50%
    MAX_CONFIDENCE = 100.0    # 最大置信度100%

    # 风险控制
    MAX_DRAWDOWN = 0.15      # 最大回撤15%
    MIN_SHARPE_RATIO = 1.0   # 最小夏普率1.0
    MIN_WIN_RATE = 0.55      # 最小胜率55%

    # 缓存设置
    CACHE_TTL_SHORT = 60     # 短期缓存1分钟
    CACHE_TTL_MEDIUM = 300   # 中期缓存5分钟
    CACHE_TTL_LONG = 1800    # 长期缓存30分钟

    # 并行处理
    DEFAULT_MAX_WORKERS = 8  # 默认最大并行数
    MIN_BATCH_SIZE = 10      # 最少批量大小
    MAX_BATCH_SIZE = 100     # 最大批量大小

    @classmethod
    def validate_signal(cls, signal: TradingSignal) -> bool:
        """验证交易信号"""
        return (cls.MIN_CONFIDENCE <= signal.confidence <= cls.MAX_CONFIDENCE and
                signal.price > 0 and
                len(signal.symbol) > 0)

    @classmethod
    def validate_portfolio_operation(cls, portfolio: Portfolio, amount: float) -> bool:
        """验证投资组合操作"""
        return (amount >= cls.MIN_TRADE_AMOUNT and
                amount <= portfolio.cash * cls.MAX_POSITION_SIZE)

    @classmethod
    def should_apply_risk_control(cls, risk_metrics: RiskMetrics) -> bool:
        """判断是否需要应用风险控制"""
        return (risk_metrics.max_drawdown > cls.MAX_DRAWDOWN or
                risk_metrics.sharpe_ratio < cls.MIN_SHARPE_RATIO or
                risk_metrics.win_rate < cls.MIN_WIN_RATE)


# ============================================================================
# 工厂接口
# ============================================================================

class StrategyFactoryInterface(ABC):
    """策略工厂接口"""

    @abstractmethod
    def create_strategy(self, strategy_name: str) -> TradingStrategy:
        """创建策略实例"""
        pass

    @abstractmethod
    def create_all_strategies(self) -> List[TradingStrategy]:
        """创建所有策略"""
        pass


# ============================================================================
# 便捷导入和导出
# ============================================================================

__all__ = [
    # 领域对象
    'TradingSignal', 'Portfolio', 'TradeRecord',
    'AnalysisConfig', 'MarketData', 'RiskMetrics', 'BacktestResult',
    'SignalAction', 'RiskLevel',

    # 领域服务接口
    'TradingStrategy', 'BullMarketAnalyzerInterface',

    # 基础设施接口
    'MarketDataProvider', 'PortfolioRepository', 'SignalNotifier',

    # 业务规则
    'BusinessRules',

    # 工厂接口
    'StrategyFactoryInterface',
]