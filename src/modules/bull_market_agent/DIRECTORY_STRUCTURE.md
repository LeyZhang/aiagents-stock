# 🐂 牛市选股模块目录结构

## 📁 完整目录结构

```
src/modules/bull_market_agent/
├── __init__.py                 # 模块导出和便捷函数
├── core.py                     # 领域核心对象和业务逻辑
├── strategies.py               # 交易策略实现
├── backtesting.py              # 历史回测引擎
├── infrastructure.py           # 基础设施实现
├── elegant_ui.py               # 现代化用户界面
├── domain/                     # 领域层子模块
│   └── __init__.py            # 领域对象导出
├── application/                # 应用层子模块
│   └── __init__.py            # 用例和DTO
├── tests/                      # 测试目录
│   └── __init__.py            # 测试工具函数
└── README.md                   # 模块说明文档
```

## 🏗️ 架构层次说明

### 1. **领域层 (Domain Layer)**
```
core.py + domain/
├── 实体 (Entities): TradingSignal, Portfolio
├── 值对象 (Value Objects): AnalysisConfig, RiskMetrics
├── 领域服务 (Domain Services): BullMarketAnalyzer
└── 业务规则 (Business Rules): 交易逻辑、风险控制
```

### 2. **应用层 (Application Layer)**
```
application/
├── 用例 (Use Cases): ScanMarketUseCase, RunBacktestUseCase
├── 应用服务 (Application Services): BullMarketApplication
└── 数据传输对象 (DTO): *Request, *Response
```

### 3. **基础设施层 (Infrastructure Layer)**
```
infrastructure.py
├── 数据提供者: AKShareMarketDataProvider
├── 仓库实现: SQLitePortfolioRepository
└── 通知器: ConsoleSignalNotifier, EmailSignalNotifier
```

### 4. **表示层 (Presentation Layer)**
```
elegant_ui.py
├── 现代化UI: ElegantBullMarketUI
├── 交互逻辑: 事件处理、状态管理
└── 数据展示: 图表、表格、可视化
```

### 5. **策略层 (Strategy Layer)**
```
strategies.py
├── 策略实现: TPlusOneStrategy, MomentumStrategy, etc.
├── 策略工厂: StrategyFactory
└── 策略接口: TradingStrategy (抽象基类)
```

### 6. **回测层 (Backtesting Layer)**
```
backtesting.py
├── 回测引擎: BacktestEngine (模板方法模式)
├── 性能分析: PerformanceAnalyzer
└── 风险指标: RiskMetrics 计算
```

### 7. **测试层 (Testing Layer)**
```
tests/
├── 单元测试: 测试单个组件
├── 集成测试: 测试组件协作
└── 测试fixtures: Mock对象和测试数据
```

## 🔄 依赖方向

```
表示层 (UI) ──────┐
                    │
应用层 (Use Cases) ◄┼── 依赖接口 (抽象)
                    │
领域层 (Domain) ───┼── 业务逻辑 (具体实现)
                    │
基础设施层 (Infra) ◄┴── 外部服务 (实现接口)
```

## 📦 模块职责

| 模块 | 职责 | 依赖关系 |
|------|------|----------|
| `__init__.py` | 模块导出、便捷函数 | 导出所有公共接口 |
| `core.py` | 领域模型、业务逻辑 | 不依赖其他模块 |
| `strategies.py` | 策略实现 | 依赖core.py |
| `backtesting.py` | 回测逻辑 | 依赖core.py, strategies.py |
| `infrastructure.py` | 外部服务集成 | 依赖core.py |
| `elegant_ui.py` | 用户界面 | 依赖所有业务模块 |
| `domain/` | 领域对象分组 | 重新导出core对象 |
| `application/` | 用例编排 | 编排领域对象 |
| `tests/` | 测试支持 | 提供测试工具 |

## 🎯 设计原则遵循

### SOLID原则
- ✅ **单一职责**: 每个类/模块职责清晰
- ✅ **开闭原则**: 通过接口扩展新功能
- ✅ **里氏替换**: 子类可替换父类
- ✅ **接口隔离**: 客户端只依赖需要的接口
- ✅ **依赖倒置**: 依赖抽象而非具体实现

### 架构模式
- ✅ **领域驱动设计**: 业务逻辑为核心
- ✅ **整洁架构**: 依赖方向向内
- ✅ **策略模式**: 易扩展交易策略
- ✅ **模板方法**: 标准化回测流程
- ✅ **工厂模式**: 策略对象创建

### 代码质量
- ✅ **类型安全**: 完整的类型注解
- ✅ **文档完善**: 详细的docstring
- ✅ **命名规范**: 描述性强、符合Python惯例
- ✅ **错误处理**: 优雅的异常处理和日志
- ✅ **测试友好**: 依赖注入便于测试

## 🚀 使用方式

### 基础用法
```python
from bull_market_agent import create_analyzer

# 便捷创建
analyzer = create_analyzer(
    sectors=["BK0917", "BK0480"],
    confidence_threshold=80.0,
    enable_parallel=True
)

# 扫描市场
signals = analyzer.scan_market()

# 执行回测
result = analyzer.run_backtest(start_date, end_date)
```

### 高级用法
```python
from bull_market_agent import (
    AnalysisConfig,
    BullMarketAnalyzer,
    StrategyFactory,
    AKShareMarketDataProvider,
    SQLitePortfolioRepository
)

# 自定义配置
config = AnalysisConfig(
    sectors=["BK0917"],
    confidence_threshold=85.0,
    enable_parallel=True,
    max_workers=8
)

# 自定义组件
analyzer = BullMarketAnalyzer(
    config=config,
    data_provider=AKShareMarketDataProvider(),
    portfolio_repo=SQLitePortfolioRepository(),
    notifier=ConsoleSignalNotifier(),
    strategies=StrategyFactory.create_all_strategies()
)
```

### UI界面
```python
from bull_market_agent import run_elegant_ui

# 启动现代化界面
run_elegant_ui()
```

## 🧪 测试运行

```bash
# 运行所有测试
python -m pytest src/modules/bull_market_agent/tests/

# 运行特定测试
python -m pytest src/modules/bull_market_agent/tests/unit/test_core.py

# 运行集成测试
python -m pytest src/modules/bull_market_agent/tests/integration/
```

## 📈 扩展指南

### 添加新策略
1. 在 `strategies.py` 中实现新策略类
2. 继承 `BaseStrategy` 或实现 `TradingStrategy` 接口
3. 在 `StrategyFactory.create_strategy()` 中注册
4. 添加相应的测试

### 添加新数据源
1. 实现 `MarketDataProvider` 接口
2. 在 `infrastructure.py` 中添加新提供者类
3. 在应用初始化时注入
4. 更新配置选项

### 添加新通知方式
1. 实现 `SignalNotifier` 接口
2. 在 `infrastructure.py` 中添加新通知器类
3. 配置相关参数
4. 测试通知功能

---

**🎨 这是一个追求代码美学的模块结构设计，既保证了功能的完整性，又体现了优雅的架构理念。**