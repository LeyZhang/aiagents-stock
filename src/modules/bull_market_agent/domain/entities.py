# 🐂 领域实体对象
"""
领域实体 - 具有唯一标识和生命周期的业务对象

实体是领域模型的核心，包含业务规则和状态。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from .value_objects import SignalAction, RiskLevel


@dataclass
class TradingSignal:
    """交易信号实体"""
    symbol: str
    name: str
    sector: str
    action: SignalAction
    confidence: float
    price: float
    reason: str
    timestamp: datetime
    detailed_reasons: List[str] = field(default_factory=list)
    expected_profit_scenarios: Dict[str, str] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    position_size_pct: float = 0.0
    stop_loss_plan: str = ""
    take_profit_plan: str = ""
    market_condition: str = ""

    def __post_init__(self):
        """实体验证"""
        if not 0 <= self.confidence <= 100:
            raise ValueError("置信度必须在0-100之间")
        if self.price <= 0:
            raise ValueError("价格必须大于0")

    @property
    def is_buy_signal(self) -> bool:
        """是否为买入信号"""
        return self.action == SignalAction.BUY

    @property
    def is_sell_signal(self) -> bool:
        """是否为卖出信号"""
        return self.action in [SignalAction.SELL, SignalAction.STOP_LOSS, SignalAction.TAKE_PROFIT]


@dataclass
class Portfolio:
    """投资组合实体"""
    cash: float = 100000.0
    positions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    total_value: float = 100000.0
    daily_pnl: float = 0.0
    total_pnl: float = 0.0

    def add_position(self, symbol: str, quantity: int, price: float, commission: float):
        """添加持仓"""
        if symbol in self.positions:
            # 追加持仓
            existing = self.positions[symbol]
            total_quantity = existing['quantity'] + quantity
            total_cost = existing['total_cost'] + (quantity * price) + commission
            avg_cost = total_cost / total_quantity
            self.positions[symbol].update({
                'quantity': total_quantity,
                'avg_cost': avg_cost,
                'total_cost': total_cost,
                'last_update': datetime.now()
            })
        else:
            # 新建持仓
            self.positions[symbol] = {
                'quantity': quantity,
                'avg_cost': price,
                'total_cost': quantity * price + commission,
                'entry_date': datetime.now(),
                'last_update': datetime.now()
            }

    def remove_position(self, symbol: str, quantity: int, price: float, commission: float) -> float:
        """移除持仓"""
        if symbol not in self.positions:
            raise ValueError(f"没有找到股票 {symbol} 的持仓")

        position = self.positions[symbol]
        if quantity > position['quantity']:
            raise ValueError(f"卖出数量 {quantity} 超过持仓数量 {position['quantity']}")

        # 计算盈亏
        sell_amount = quantity * price
        cost_basis = quantity * position['avg_cost']
        profit_loss = sell_amount - cost_basis - commission

        # 更新持仓
        position['quantity'] -= quantity
        position['total_cost'] -= cost_basis
        position['last_update'] = datetime.now()

        # 如果持仓为0，删除记录
        if position['quantity'] == 0:
            del self.positions[symbol]

        return profit_loss

    def get_position_value(self, symbol: str, current_price: float) -> float:
        """获取持仓市值"""
        if symbol not in self.positions:
            return 0.0
        return self.positions[symbol]['quantity'] * current_price

    def get_total_value(self, price_provider: callable) -> float:
        """获取总市值"""
        position_value = sum(
            self.get_position_value(symbol, price_provider(symbol))
            for symbol in self.positions.keys()
        )
        return self.cash + position_value

    @property
    def has_positions(self) -> bool:
        """是否有持仓"""
        return len(self.positions) > 0

    @property
    def total_positions_value(self) -> float:
        """持仓总市值"""
        return sum(pos['total_cost'] for pos in self.positions.values())


@dataclass
class TradeRecord:
    """交易记录实体"""
    symbol: str
    name: str
    action: SignalAction
    quantity: int
    price: float
    amount: float
    commission: float
    timestamp: datetime
    reason: str
    confidence: float
    cost_price: Optional[float] = None
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    hold_days: int = 0
    trade_summary: str = ""
    lessons_learned: str = ""

    @property
    def is_profitable(self) -> bool:
        """是否盈利"""
        return self.profit_loss > 0

    @property
    def is_closed_trade(self) -> bool:
        """是否为已平仓交易"""
        return self.action in [SignalAction.SELL, SignalAction.STOP_LOSS, SignalAction.TAKE_PROFIT]