# 🐂 扫描市场用例
"""
应用层用例 - 扫描市场

用例负责编排领域对象，处理业务流程，不包含业务逻辑。
"""

from typing import List
from datetime import datetime

from ...domain.entities import TradingSignal
from ...domain.services.bull_market_analyzer import BullMarketAnalyzer


class ScanMarketUseCase:
    """
    扫描市场用例

    负责编排市场扫描的完整流程：
    1. 准备扫描参数
    2. 调用领域服务执行扫描
    3. 处理扫描结果
    4. 返回格式化的结果
    """

    def __init__(self, analyzer: BullMarketAnalyzer):
        """
        初始化用例

        Args:
            analyzer: 领域分析器
        """
        self.analyzer = analyzer

    def execute(self) -> List[TradingSignal]:
        """
        执行市场扫描

        Returns:
            交易信号列表
        """
        try:
            # 调用领域服务执行扫描
            signals = self.analyzer.scan_market()

            # 这里可以添加应用层的处理逻辑
            # 例如：信号过滤、排序、格式化等

            return self._process_signals(signals)

        except Exception as e:
            # 应用层异常处理
            print(f"市场扫描用例执行失败: {e}")
            return []

    def execute_with_options(self, sectors: List[str] = None,
                           confidence_threshold: float = None) -> List[TradingSignal]:
        """
        执行市场扫描（带选项）

        Args:
            sectors: 指定扫描板块
            confidence_threshold: 置信度阈值

        Returns:
            交易信号列表
        """
        # 临时修改配置
        original_config = self.analyzer.config

        try:
            if sectors or confidence_threshold is not None:
                # 创建临时配置
                from ...domain.value_objects import AnalysisConfig
                temp_config = AnalysisConfig(
                    sectors=sectors or original_config.sectors,
                    confidence_threshold=confidence_threshold or original_config.confidence_threshold,
                    max_position_size=original_config.max_position_size,
                    enable_parallel=original_config.enable_parallel,
                    max_workers=original_config.max_workers,
                    analysis_timeout=original_config.analysis_timeout,
                    enable_caching=original_config.enable_caching,
                    cache_ttl=original_config.cache_ttl
                )

                # 临时替换配置
                self.analyzer.config = temp_config

            return self.execute()

        finally:
            # 恢复原始配置
            self.analyzer.config = original_config

    def _process_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        处理信号结果

        Args:
            signals: 原始信号列表

        Returns:
            处理后的信号列表
        """
        # 应用层处理逻辑
        # 例如：信号去重、排序、格式化等

        # 按置信度降序排序
        sorted_signals = sorted(signals, key=lambda s: s.confidence, reverse=True)

        # 去重（保留最高置信度的信号）
        unique_signals = {}
        for signal in sorted_signals:
            key = f"{signal.symbol}_{signal.action.value}"
            if key not in unique_signals:
                unique_signals[key] = signal

        return list(unique_signals.values())