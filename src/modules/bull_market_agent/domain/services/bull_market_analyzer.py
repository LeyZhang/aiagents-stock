# 🐂 牛市选股分析器 - 领域服务
"""
领域服务 - 协调领域对象的业务逻辑

BullMarketAnalyzer 是领域服务的核心，负责编排各个领域对象完成复杂的业务逻辑。
"""

import concurrent.futures
import time
from typing import List, Optional
from datetime import datetime

from src.core.logger import get_logger

from ..entities import TradingSignal, Portfolio, TradeRecord
from ..value_objects import AnalysisConfig, MarketData, BacktestResult, RiskMetrics

logger = get_logger('bull_market_agent.analyzer')
from datetime import datetime

from ..entities import TradingSignal, Portfolio, TradeRecord
from ..value_objects import AnalysisConfig, MarketData, BacktestResult, RiskMetrics


class BullMarketAnalyzer:
    """
    牛市选股分析器 - 领域服务

    这是系统的核心领域服务，负责：
    1. 协调市场扫描和信号生成
    2. 编排交易策略的执行
    3. 管理投资组合的状态
    4. 计算风险指标和绩效分析

    Attributes:
        config: 分析配置
        use_cases: 应用层用例
        _cache: 内部缓存
        _cache_timestamps: 缓存时间戳
    """

    def __init__(self, config: AnalysisConfig, strategies: Optional[List] = None, data_provider = None, repository = None, notifier = None):
        """
        初始化分析器

        Args:
            config: 分析配置
            strategies: 交易策略列表
            data_provider: 数据提供者
            repository: 仓库
            notifier: 通知器
        """
        self.config = config
        self.strategies = strategies or []
        self.data_provider = data_provider
        self.repository = repository
        self.notifier = notifier

        # 缓存系统
        self._cache = {}
        self._cache_timestamps = {}

    def scan_market(self) -> List[TradingSignal]:
        """
        扫描市场，生成交易信号

        这是领域服务的主要业务方法，协调多个组件完成市场分析：
        1. 获取市场数据
        2. 执行策略分析
        3. 生成交易信号
        4. 应用风险控制

        Returns:
            过滤后的交易信号列表
        """
        logger.info("开始市场扫描", sectors=self.config.sectors, confidence_threshold=self.config.confidence_threshold)

        if not self.data_provider:
            logger.error("错误：数据提供者未配置")
            return []

        signals = []
        for sector in self.config.sectors:
            logger.debug("开始扫描板块", sector=sector)
            try:
                sector_data = self.data_provider.get_sector_stocks(sector)
                logger.debug("获取板块数据完成", sector=sector, stocks_count=len(sector_data))

                for market_data in sector_data:
                    signal = self.analyze_single_stock(market_data)
                    if signal:
                        signals.append(signal)
                        logger.info("生成交易信号", symbol=signal.symbol, action=signal.action.value, confidence=signal.confidence)

            except Exception as e:
                logger.error("扫描板块失败", sector=sector, error=str(e))
                continue

        # 过滤低置信度信号
        filtered_signals = [s for s in signals if s.confidence >= self.config.confidence_threshold]
        logger.debug("信号过滤完成", total_signals=len(signals), filtered_signals=len(filtered_signals), confidence_threshold=self.config.confidence_threshold)

        # 通知信号
        if self.notifier:
            logger.debug("发送信号通知", signals_count=len(filtered_signals))
            for signal in filtered_signals:
                self.notifier.notify_signal(signal)
        else:
            logger.debug("未配置通知器，跳过信号通知")

        logger.info("市场扫描完成", final_signals=len(filtered_signals))
        return filtered_signals

    def run_backtest(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """
        执行回测分析

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            完整的回测结果
        """
        from ...backtesting import BacktestEngine

        if not self.data_provider or not self.repository:
            # 返回空的回测结果
            return BacktestResult(
                config=self.config,
                start_date=start_date,
                end_date=end_date,
                trading_days=0,
                total_signals=0,
                executed_trades=0
            )

        engine = BacktestEngine(
            config=self.config,
            data_provider=self.data_provider,
            portfolio_repo=self.repository,
            strategies=self.strategies
        )

        result = engine.run_backtest(start_date, end_date)

        # 通知回测结果
        if self.notifier:
            self.notifier.notify_backtest_result(result)

        return result

    def analyze_single_stock(self, market_data: MarketData) -> Optional[TradingSignal]:
        """
        分析单个股票

        Args:
            market_data: 市场数据

        Returns:
            交易信号或None
        """
        logger.debug("开始分析单个股票", symbol=market_data.symbol, price=market_data.price, change_pct=market_data.change_pct)

        if not self.strategies:
            logger.debug("无可用策略，跳过分析", symbol=market_data.symbol)
            return None

        # 尝试所有策略
        for strategy in self.strategies:
            logger.debug("使用策略分析", symbol=market_data.symbol, strategy=strategy.name)
            signal = strategy.analyze_market_data(market_data, self.config)
            if signal:
                logger.debug("策略生成信号", symbol=market_data.symbol, strategy=strategy.name, action=signal.action.value)
                return signal

        logger.debug("所有策略均未生成信号", symbol=market_data.symbol)
        return None

    def calculate_portfolio_value(self, portfolio: Portfolio, price_provider) -> float:
        """
        计算投资组合总价值

        Args:
            portfolio: 投资组合
            price_provider: 价格提供函数

        Returns:
            总市值
        """
        return portfolio.get_total_value(price_provider)

    def assess_risk(self, portfolio: Portfolio, signals: List[TradingSignal]) -> RiskMetrics:
        """
        评估风险指标

        Args:
            portfolio: 投资组合
            signals: 交易信号列表

        Returns:
            风险指标
        """
        # 简化的风险评估
        return RiskMetrics(
            max_drawdown=0.05,  # 5%最大回撤
            sharpe_ratio=1.5,   # 1.5夏普比率
            win_rate=0.65,      # 65%胜率
        )

    def _get_cached_data(self, cache_key: str, data_provider, ttl: int = 300):
        """
        获取缓存数据

        Args:
            cache_key: 缓存键
            data_provider: 数据提供函数
            ttl: 缓存有效期(秒)

        Returns:
            缓存或新鲜数据
        """
        if self.config.enable_caching:
            if (cache_key in self._cache and
                datetime.now().timestamp() - self._cache_timestamps.get(cache_key, 0) < ttl):
                return self._cache[cache_key]

        # 获取新数据
        data = data_provider()

        if self.config.enable_caching:
            self._cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now().timestamp()

        return data

    def _analyze_sector_parallel(self, sector_data: List[MarketData]) -> List[TradingSignal]:
        """
        并行分析板块股票

        Args:
            sector_data: 板块股票数据

        Returns:
            交易信号列表
        """
        if not self.config.enable_parallel:
            return self._analyze_sector_sequential(sector_data)

        signals = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = [
                executor.submit(self.analyze_single_stock, market_data)
                for market_data in sector_data
            ]

            for future in concurrent.futures.as_completed(futures):
                try:
                    signal = future.result()
                    if signal:
                        signals.append(signal)
                except Exception as e:
                    print(f"股票分析失败: {e}")
                    continue

        return signals

    def _analyze_sector_sequential(self, sector_data: List[MarketData]) -> List[TradingSignal]:
        """
        顺序分析板块股票

        Args:
            sector_data: 板块股票数据

        Returns:
            交易信号列表
        """
        signals = []
        for market_data in sector_data:
            signal = self.analyze_single_stock(market_data)
            if signal:
                signals.append(signal)
        return signals