# 🐂 基础设施层 - 外部服务集成
"""
基础设施层 - 实现领域层定义的接口

包含数据提供者、仓库、通知器等外部服务集成。
"""

from .data_providers import AKShareMarketDataProvider

from .repositories import (
    SQLitePortfolioRepository,
    ConsoleSignalNotifier,
    EmailSignalNotifier,
    WebhookSignalNotifier,
)