# 🐂 领域值对象
"""
值对象 - 不具有唯一标识，仅通过属性值来区分的对象

值对象是不可变的，用于表示概念上的值。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class SignalAction(Enum):
    """信号动作枚举"""
    BUY = "买入"
    SELL = "卖出"
    HOLD = "持有"
    STOP_LOSS = "止损"
    TAKE_PROFIT = "止盈"


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"


@dataclass(frozen=True)
class AnalysisConfig:
    """分析配置值对象"""
    sectors: List[str] = field(default_factory=lambda: ["BK0917"])
    confidence_threshold: float = 80.0
    max_position_size: float = 0.1  # 单股票最大仓位
    enable_parallel: bool = True
    max_workers: int = 8
    analysis_timeout: int = 15
    enable_caching: bool = True
    cache_ttl: int = 300

    def __post_init__(self):
        """配置验证"""
        if not 0 < self.confidence_threshold <= 100:
            raise ValueError("置信度阈值必须在0-100之间")
        if not 0 < self.max_position_size <= 1:
            raise ValueError("最大仓位必须在0-1之间")

    def with_updated_sectors(self, sectors: List[str]) -> 'AnalysisConfig':
        """创建新的配置，更新板块"""
        return AnalysisConfig(
            sectors=sectors,
            confidence_threshold=self.confidence_threshold,
            max_position_size=self.max_position_size,
            enable_parallel=self.enable_parallel,
            max_workers=self.max_workers,
            analysis_timeout=self.analysis_timeout,
            enable_caching=self.enable_caching,
            cache_ttl=self.cache_ttl
        )

    def with_updated_threshold(self, threshold: float) -> 'AnalysisConfig':
        """创建新的配置，更新置信度阈值"""
        return AnalysisConfig(
            sectors=self.sectors,
            confidence_threshold=threshold,
            max_position_size=self.max_position_size,
            enable_parallel=self.enable_parallel,
            max_workers=self.max_workers,
            analysis_timeout=self.analysis_timeout,
            enable_caching=self.enable_caching,
            cache_ttl=self.cache_ttl
        )


@dataclass(frozen=True)
class MarketData:
    """市场数据值对象"""
    symbol: str
    name: str
    price: float
    change_pct: float
    volume: int
    amount: float
    sector: str
    timestamp: datetime
    additional_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def market_cap(self) -> Optional[float]:
        """市值"""
        return self.additional_data.get('market_cap')

    @property
    def pe_ratio(self) -> Optional[float]:
        """市盈率"""
        return self.additional_data.get('pe_ratio')

    @property
    def volume_ratio(self) -> float:
        """量比"""
        avg_volume = self.additional_data.get('avg_volume', 1)
        return self.volume / avg_volume if avg_volume > 0 else 1.0

    def is_high_volume(self) -> bool:
        """是否为高成交量"""
        return self.volume_ratio > 2.0

    def is_uptrend(self) -> bool:
        """是否为上涨趋势"""
        return self.change_pct > 0

    def is_downtrend(self) -> bool:
        """是否为下跌趋势"""
        return self.change_pct < 0


@dataclass(frozen=True)
class RiskMetrics:
    """风险指标值对象"""
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    volatility: float = 0.0
    win_rate: float = 0.0
    profit_loss_ratio: float = 0.0
    calmar_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_consecutive_losses: int = 0
    recovery_factor: float = 0.0

    @property
    def is_acceptable_risk(self) -> bool:
        """风险是否可接受"""
        return (self.max_drawdown <= 0.15 and  # 最大回撤不超过15%
                self.sharpe_ratio >= 1.0 and   # 夏普比率不低于1
                self.win_rate >= 0.55)         # 胜率不低于55%

    @property
    def risk_score(self) -> float:
        """综合风险评分 (0-100，100为最低风险)"""
        score = 100.0

        # 最大回撤惩罚
        if self.max_drawdown > 0.1:
            score -= (self.max_drawdown - 0.1) * 500

        # 夏普比率奖励
        if self.sharpe_ratio > 1.0:
            score += min((self.sharpe_ratio - 1.0) * 20, 20)

        # 胜率奖励
        if self.win_rate > 0.6:
            score += min((self.win_rate - 0.6) * 200, 20)

        return max(0, min(100, score))


@dataclass(frozen=True)
class BacktestResult:
    """回测结果值对象"""
    config: AnalysisConfig
    start_date: datetime
    end_date: datetime
    trading_days: int
    total_signals: int
    executed_trades: int
    trade_records: List[Dict[str, Any]] = field(default_factory=list)
    daily_results: List[Dict[str, Any]] = field(default_factory=list)
    performance_analysis: Dict[str, Any] = field(default_factory=dict)
    risk_metrics: RiskMetrics = field(default_factory=RiskMetrics)
    final_portfolio_value: float = 100000.0

    @property
    def total_return_pct(self) -> float:
        """总收益率"""
        return ((self.final_portfolio_value / 100000.0) - 1) * 100

    @property
    def annualized_return(self) -> float:
        """年化收益率"""
        if self.trading_days == 0:
            return 0.0
        return ((1 + self.total_return_pct / 100) ** (252 / self.trading_days) - 1) * 100

    @property
    def is_profitable(self) -> bool:
        """是否盈利"""
        return self.final_portfolio_value > 100000.0

    @property
    def performance_score(self) -> float:
        """综合表现评分 (0-100)"""
        score = 50.0  # 基准分

        # 收益率奖励/惩罚
        if self.total_return_pct > 20:
            score += 20
        elif self.total_return_pct > 10:
            score += 10
        elif self.total_return_pct < -10:
            score -= 20
        elif self.total_return_pct < 0:
            score -= 10

        # 胜率奖励
        win_rate = self.performance_analysis.get('win_rate', 0)
        if win_rate > 0.7:
            score += 15
        elif win_rate > 0.6:
            score += 10
        elif win_rate < 0.4:
            score -= 15

        # 风险调整
        risk_score = self.risk_metrics.risk_score
        score += (risk_score - 50) * 0.3  # 风险评分权重30%

        return max(0, min(100, score))


@dataclass(frozen=True)
class TimeSlot:
    """时间段值对象"""
    name: str
    start_time: str
    end_time: str

    @classmethod
    def trading_slots(cls) -> List['TimeSlot']:
        """获取交易时间段"""
        return [
            cls("早盘竞价", "09:15", "09:30"),
            cls("上午交易", "09:30", "11:30"),
            cls("下午交易", "13:00", "14:30"),
            cls("尾盘交易", "14:30", "15:00"),
        ]

    def contains(self, time: datetime) -> bool:
        """判断时间是否在此时间段内"""
        start = datetime.strptime(self.start_time, "%H:%M").time()
        end = datetime.strptime(self.end_time, "%H:%M").time()
        current_time = time.time()
        return start <= current_time <= end