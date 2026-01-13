# 🐂 牛市选股模块 - 优雅架构版
"""
牛市选股分析系统 - 基于领域驱动设计的现代化量化交易系统

目录结构：
bull_market_agent/
├── __init__.py          # 模块导出和便捷函数
├── core.py              # 领域核心对象和业务逻辑
├── strategies.py        # 交易策略实现
├── backtesting.py       # 历史回测引擎
├── infrastructure.py    # 基础设施实现
├── elegant_ui.py        # 现代化用户界面
├── domain/              # 领域层子模块
│   ├── __init__.py
│   ├── entities.py      # 实体对象
│   ├── value_objects.py # 值对象
│   └── services.py      # 领域服务
├── application/         # 应用层子模块
│   ├── __init__.py
│   ├── use_cases.py     # 用例编排
│   └── dto.py           # 数据传输对象
└── tests/               # 测试目录
    ├── __init__.py
    ├── unit/            # 单元测试
    ├── integration/     # 集成测试
    └── fixtures/        # 测试数据

架构特点：
- 领域驱动设计 (DDD) - 整洁架构
- 依赖倒置原则 (DIP) - 高层不依赖低层
- 策略模式 (Strategy) - 易扩展新策略
- 模板方法模式 (Template Method) - 回测流程
- 完整的类型注解 - 类型安全
- 高可扩展性和可测试性
"""

from .domain.entities import (
    # 实体对象
    TradingSignal,
    Portfolio,
    TradeRecord,
)

from .domain.value_objects import (
    # 值对象
    AnalysisConfig,
    MarketData,
    RiskMetrics,
    BacktestResult,
    SignalAction,
    RiskLevel,
)

from .domain.services.bull_market_analyzer import (
    # 领域服务
    BullMarketAnalyzer,
)

from .strategies import (
    # 策略类
    TPlusOneStrategy,
    MomentumStrategy,
    VolumeStrategy,
    SentimentStrategy,

    # 工厂
    StrategyFactory,
)

from .backtesting import (
    # 回测组件
    BacktestEngine,
    PerformanceAnalyzer,
)

from .infrastructure import (
    # 数据提供者
    AKShareMarketDataProvider,
)

from .infrastructure.repositories import (
    # 仓库
    SQLitePortfolioRepository,

    # 通知器
    ConsoleSignalNotifier,
    EmailSignalNotifier,
    WebhookSignalNotifier,
)

# UI组件 (可选导入)
try:
    from .elegant_ui import ElegantBullMarketUI, run_elegant_ui
    _ui_available = True
except ImportError:
    _ui_available = False

__all__ = [
    # 核心领域对象
    'BullMarketAnalyzer',
    'AnalysisConfig',
    'MarketData',
    'TradingSignal',
    'Portfolio',
    'RiskMetrics',
    'BacktestResult',
    'TradeRecord',
    'SignalAction',
    'RiskLevel',

    # 策略组件
    'TPlusOneStrategy',
    'MomentumStrategy',
    'VolumeStrategy',
    'SentimentStrategy',
    'StrategyFactory',

    # 回测组件
    'BacktestEngine',
    'PerformanceAnalyzer',

    # 基础设施
    'AKShareMarketDataProvider',
    'SQLitePortfolioRepository',
    'ConsoleSignalNotifier',
    'EmailSignalNotifier',
    'WebhookSignalNotifier',
]

# 条件性导出UI组件
if _ui_available:
    __all__.extend([
        'ElegantBullMarketUI',
        'run_elegant_ui'
    ])

__version__ = "2.1.0"
__author__ = "AI Agents Stock Team"

# 便捷函数
def create_analyzer(
    sectors=None,
    confidence_threshold=80.0,
    enable_parallel=True,
    max_workers=8
):
    """
    便捷的分析器创建函数

    Args:
        sectors: 监控板块列表
        confidence_threshold: 置信度阈值
        enable_parallel: 是否启用并行处理
        max_workers: 最大并行线程数

    Returns:
        配置好的BullMarketAnalyzer实例
    """
    from .domain.value_objects import AnalysisConfig

    config = AnalysisConfig(
        sectors=sectors or ["BK0917"],
        confidence_threshold=confidence_threshold,
        enable_parallel=enable_parallel,
        max_workers=max_workers
    )

    return BullMarketAnalyzer(config=config)

    config = AnalysisConfig(
        sectors=sectors or ["BK0917"],
        confidence_threshold=confidence_threshold,
        enable_parallel=enable_parallel,
        max_workers=max_workers
    )

    return BullMarketAnalyzer(
        config=config,
        data_provider=AKShareMarketDataProvider(),
        portfolio_repo=SQLitePortfolioRepository(),
        notifier=ConsoleSignalNotifier(),
        strategies=StrategyFactory.create_all_strategies()
    )