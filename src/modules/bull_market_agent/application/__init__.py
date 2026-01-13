# 🐂 应用层子模块
"""
应用层 - 用例编排和数据传输对象

应用层负责编排领域对象，处理业务流程，但不包含业务逻辑。
"""

from typing import List, Optional
from datetime import datetime

from ..core import (
    BullMarketAnalyzer,
    TradingSignal,
    BacktestResult,
    AnalysisConfig,
)
from ..infrastructure import (
    AKShareMarketDataProvider,
    SQLitePortfolioRepository,
    ConsoleSignalNotifier,
)
from ..strategies import StrategyFactory


class ScanMarketUseCase:
    """扫描市场用例"""

    def __init__(self, analyzer: BullMarketAnalyzer):
        self.analyzer = analyzer

    def execute(self) -> List[TradingSignal]:
        """
        执行市场扫描

        Returns:
            交易信号列表
        """
        return self.analyzer.scan_market()


class RunBacktestUseCase:
    """执行回测用例"""

    def __init__(self, analyzer: BullMarketAnalyzer):
        self.analyzer = analyzer

    def execute(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """
        执行回测

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            回测结果
        """
        return self.analyzer.run_backtest(start_date, end_date)


class BullMarketApplication:
    """牛市选股应用服务"""

    def __init__(self, config: AnalysisConfig):
        # 依赖注入
        self.config = config
        self.data_provider = AKShareMarketDataProvider()
        self.portfolio_repo = SQLitePortfolioRepository()
        self.notifier = ConsoleSignalNotifier()
        self.strategies = StrategyFactory.create_all_strategies()

        # 创建分析器
        self.analyzer = BullMarketAnalyzer(
            config=config,
            data_provider=self.data_provider,
            portfolio_repo=self.portfolio_repo,
            notifier=self.notifier,
            strategies=self.strategies
        )

        # 初始化用例
        self.scan_market_use_case = ScanMarketUseCase(self.analyzer)
        self.run_backtest_use_case = RunBacktestUseCase(self.analyzer)

    def scan_market(self) -> List[TradingSignal]:
        """扫描市场"""
        return self.scan_market_use_case.execute()

    def run_backtest(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """执行回测"""
        return self.run_backtest_use_case.execute(start_date, end_date)


# 数据传输对象 (DTO)
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ScanMarketRequest:
    """扫描市场请求"""
    sectors: Optional[List[str]] = None
    confidence_threshold: Optional[float] = None


@dataclass
class ScanMarketResponse:
    """扫描市场响应"""
    signals: List[TradingSignal]
    scan_time: datetime
    total_signals: int
    valid_signals: int


@dataclass
class BacktestRequest:
    """回测请求"""
    start_date: datetime
    end_date: datetime
    initial_capital: float = 100000.0


@dataclass
class BacktestResponse:
    """回测响应"""
    result: BacktestResult
    execution_time: float
    summary: Dict[str, Any]


__all__ = [
    'ScanMarketUseCase',
    'RunBacktestUseCase',
    'BullMarketApplication',
    'ScanMarketRequest',
    'ScanMarketResponse',
    'BacktestRequest',
    'BacktestResponse',
]