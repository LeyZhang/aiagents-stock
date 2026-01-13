"""
牛市选股监控数据库
管理监控配置、扫描结果和历史记录
"""

from peewee import Model, CharField, DateTimeField, FloatField, IntegerField, TextField, BooleanField, SqliteDatabase
from datetime import datetime
import os
import json
from typing import List, Dict, Any

from src.core.logger import get_logger
from .strategy import Signal

logger = get_logger('bull_monitor_db')


class BullMonitorDatabase:
    """牛市选股监控数据库"""

    def __init__(self, db_path: str = "data/db/bull_monitor.db"):
        self.db_path = db_path
        self.db = SqliteDatabase(db_path)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        try:
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

            # 设置模型的数据库连接
            BullMonitorScan._meta.database = self.db
            BullMonitorConfig._meta.database = self.db

            self.db.connect()
            self.db.create_tables([BullMonitorScan, BullMonitorConfig], safe=True)
            self.db.close()
            logger.info("✅ 牛市监控数据库表初始化完成")
        except Exception as e:
            logger.warning(f"牛市监控数据库表已存在或初始化失败: {e}")

    def save_scan_result(self, signals: List[Signal], scan_time: float, config: Dict[str, Any]):
        """保存扫描结果"""
        try:
            with self.db.atomic():
                # 创建扫描记录
                scan = BullMonitorScan.create(
                    scan_time=scan_time,
                    signal_count=len(signals),
                    config_json=json.dumps(config, ensure_ascii=False),
                    signals_json=json.dumps([{
                        'code': s.code,
                        'name': s.name,
                        'sector': s.sector,
                        'action': s.action,
                        'confidence': s.confidence,
                        'price': s.price,
                        'reason': s.reason,
                        'timestamp': s.timestamp.isoformat()
                    } for s in signals], ensure_ascii=False)
                )

            logger.debug(f"保存扫描结果: {len(signals)}条信号")
            return scan.id

        except Exception as e:
            logger.error(f"保存扫描结果失败: {e}")
            return None

    def get_recent_scans(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的扫描记录"""
        try:
            scans = BullMonitorScan.select().order_by(BullMonitorScan.created_at.desc()).limit(limit)

            results = []
            for scan in scans:
                results.append({
                    'id': scan.id,
                    'created_at': scan.created_at,
                    'scan_time': scan.scan_time,
                    'signal_count': scan.signal_count,
                    'config': json.loads(scan.config_json) if scan.config_json else {},
                    'signals': json.loads(scan.signals_json) if scan.signals_json else []
                })

            return results

        except Exception as e:
            logger.error(f"获取扫描记录失败: {e}")
            return []

    def get_scan_statistics(self, days: int = 7) -> Dict[str, Any]:
        """获取扫描统计信息"""
        try:
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=days)

            # 总扫描次数
            total_scans = BullMonitorScan.select().where(BullMonitorScan.created_at >= cutoff).count()

            # 平均扫描时间
            scans = BullMonitorScan.select().where(BullMonitorScan.created_at >= cutoff)
            avg_scan_time = sum(s.scan_time for s in scans) / len(scans) if scans else 0

            # 信号总数
            total_signals = sum(s.signal_count for s in scans)

            # 高置信度信号数
            high_conf_signals = 0
            for scan in scans:
                signals = json.loads(scan.signals_json) if scan.signals_json else []
                high_conf_signals += len([s for s in signals if s.get('confidence', 0) >= 85])

            return {
                'total_scans': total_scans,
                'avg_scan_time': avg_scan_time,
                'total_signals': total_signals,
                'high_conf_signals': high_conf_signals,
                'avg_signals_per_scan': total_signals / total_scans if total_scans > 0 else 0,
                'period_days': days
            }

        except Exception as e:
            logger.error(f"获取扫描统计失败: {e}")
            return {}

    def save_monitor_config(self, config: Dict[str, Any]):
        """保存监控配置"""
        try:
            # 先删除旧配置
            BullMonitorConfig.delete().execute()

            # 保存新配置
            BullMonitorConfig.create(
                config_key='monitor_config',
                config_value=json.dumps(config, ensure_ascii=False)
            )

            logger.info("监控配置已保存")

        except Exception as e:
            logger.error(f"保存监控配置失败: {e}")

    def get_monitor_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        try:
            config_record = BullMonitorConfig.get_or_none(config_key='monitor_config')
            if config_record:
                return json.loads(config_record.config_value)
            else:
                # 返回默认配置
                return {
                    'sectors': ['BK0917', 'BK0480', 'BK0916'],
                    'confidence_threshold': 80,
                    'max_signals': 20,
                    'enabled': True,
                    'notification_enabled': True,
                    'trading_hours_only': True
                }

        except Exception as e:
            logger.error(f"获取监控配置失败: {e}")
            return {}

    def clear_old_scans(self, days: int = 30):
        """清理旧的扫描记录"""
        try:
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=days)

            deleted_count = BullMonitorScan.delete().where(BullMonitorScan.created_at < cutoff).execute()
            logger.info(f"清理了 {deleted_count} 条旧扫描记录")

            return deleted_count

        except Exception as e:
            logger.error(f"清理扫描记录失败: {e}")
            return 0


class BullMonitorScan(Model):
    """扫描记录表"""

    class Meta:
        database = None  # 将在运行时设置
        table_name = 'bull_monitor_scans'

    scan_time = FloatField()  # 扫描耗时（秒）
    signal_count = IntegerField()  # 信号数量
    config_json = TextField(null=True)  # 扫描配置
    signals_json = TextField(null=True)  # 信号详情
    created_at = DateTimeField(default=datetime.now, index=True)


class BullMonitorConfig(Model):
    """监控配置表"""

    class Meta:
        database = None  # 将在运行时设置
        table_name = 'bull_monitor_config'

    config_key = CharField(unique=True)
    config_value = TextField()
    updated_at = DateTimeField(default=datetime.now)


# 全局数据库实例
bull_monitor_db = BullMonitorDatabase()