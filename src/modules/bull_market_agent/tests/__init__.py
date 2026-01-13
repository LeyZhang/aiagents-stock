# 🐂 测试模块
"""
测试模块 - 单元测试和集成测试

目录结构：
tests/
├── unit/              # 单元测试
│   ├── test_core.py          # 核心对象测试
│   ├── test_strategies.py    # 策略测试
│   └── test_backtesting.py   # 回测测试
├── integration/       # 集成测试
│   ├── test_analyzer.py      # 分析器集成测试
│   └── test_ui.py            # UI集成测试
└── fixtures/          # 测试数据
    ├── sample_data.py         # 示例数据
    └── mock_providers.py      # Mock提供者
"""

import pytest
from typing import List
from ..core import (
    AnalysisConfig,
    MarketData,
    TradingSignal,
    SignalAction
)
from ..strategies import StrategyFactory
from datetime import datetime


# 测试工具函数
def create_test_config() -> AnalysisConfig:
    """创建测试配置"""
    return AnalysisConfig(
        sectors=["BK0917"],
        confidence_threshold=80.0,
        enable_parallel=False,  # 测试时关闭并行
        max_workers=1
    )


def create_sample_market_data() -> List[MarketData]:
    """创建示例市场数据"""
    return [
        MarketData(
            symbol="000001",
            name="平安银行",
            price=10.5,
            change_pct=2.3,
            volume=1000000,
            amount=10500000.0,
            sector="BK0917",
            timestamp=datetime.now()
        ),
        MarketData(
            symbol="000002",
            name="万科A",
            price=15.8,
            change_pct=-1.2,
            volume=800000,
            amount=12640000.0,
            sector="BK0917",
            timestamp=datetime.now()
        )
    ]


def create_sample_signal() -> TradingSignal:
    """创建示例交易信号"""
    return TradingSignal(
        symbol="000001",
        name="平安银行",
        sector="BK0917",
        action=SignalAction.BUY,
        confidence=85.0,
        price=10.5,
        reason="技术面突破，成交量放大",
        timestamp=datetime.now(),
        detailed_reasons=["突破关键阻力位", "成交量明显放大"],
        expected_profit_scenarios={
            "乐观": "¥11.50 (+9.5%)",
            "中性": "¥11.00 (+4.8%)",
            "保守": "¥10.80 (+2.9%)"
        }
    )


__all__ = [
    'create_test_config',
    'create_sample_market_data',
    'create_sample_signal',
]