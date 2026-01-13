"""
数据库 - 优雅解耦
复用core.database的连接管理模式
"""

from peewee import Model, CharField, DateTimeField, FloatField, IntegerField, TextField, SqliteDatabase
from datetime import datetime
import os

db_path = os.path.join("data", "db", "bull_market.db")
db = SqliteDatabase(db_path)
from src.core.logger import get_logger

logger = get_logger('bull_db')


class BullSignal(Model):
    """交易信号记录"""

    class Meta:
        database = db
        table_name = 'bull_signals'

    code = CharField(max_length=10, index=True)
    name = CharField(max_length=50)
    sector = CharField(max_length=50)
    action = CharField(max_length=20)  # 加仓/减仓/空仓
    confidence = FloatField()
    price = FloatField()
    reason = TextField()
    created_at = DateTimeField(default=datetime.now, index=True)

    @classmethod
    def get_recent(cls, days: int = 7, sector: str = None) -> list:
        """获取最近N天的信号"""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        query = cls.select().where(cls.created_at >= cutoff)

        if sector:
            query = query.where(cls.sector == sector)

        return list(query.order_by(cls.created_at.desc()))

    @classmethod
    def get_statistics(cls, days: int = 30) -> dict:
        """获取统计信息"""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        total = cls.select().where(cls.created_at >= cutoff).count()

        # 简化：假设"加仓"为盈利
        wins = cls.select().where(
            (cls.created_at >= cutoff) &
            (cls.action == '加仓')
        ).count()

        return {
            'total': total,
            'wins': wins,
            'losses': total - wins,
            'win_rate': (wins / total * 100) if total > 0 else 0.0
        }


class BullBacktest(Model):
    """回测记录"""

    class Meta:
        database = db
        table_name = 'bull_backtests'

    start_date = DateTimeField()
    end_date = DateTimeField()
    win_rate = FloatField()
    total_trades = IntegerField()
    total_signals = IntegerField()
    config_json = TextField()  # 策略配置
    created_at = DateTimeField(default=datetime.now, index=True)

    @classmethod
    def get_recent(cls, limit: int = 10) -> list:
        """获取最近的回测记录"""
        return list(cls.select().order_by(cls.created_at.desc()).limit(limit))


# 初始化表
def init_db():
    """优雅初始化数据库表"""
    try:
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        db.connect()
        db.create_tables([BullSignal, BullBacktest], safe=True)
        db.close()
        logger.info("✅ 牛市策略数据库表初始化完成")
    except Exception as e:
        logger.warning(f"数据库表已存在或初始化失败: {e}")
