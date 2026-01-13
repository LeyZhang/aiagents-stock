"""
牛市选股监控服务
定时扫描牛市选股策略，支持5分钟级别实时监控
"""

import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import schedule
import pandas as pd

from .strategy import BullMarketStrategy, Signal
from .bull_monitor_db import bull_monitor_db
from src.core.logger import get_logger
from src.core.notification_service import notification_service

logger = get_logger('bull_monitor_service')


class BullMarketMonitorService:
    """牛市选股监控服务"""

    def __init__(self, scan_interval_minutes: int = 5):
        """
        初始化监控服务

        Args:
            scan_interval_minutes: 扫描间隔（分钟），默认5分钟
        """
        self.scan_interval_minutes = scan_interval_minutes
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_scan_time: Optional[datetime] = None
        self.scan_count = 0
        self.error_count = 0

        # 默认监控配置
        self.monitor_config = {
            'sectors': ['BK0917', 'BK0480', 'BK0916'],  # 半导体、航天航空、CPO概念
            'confidence_threshold': 80,
            'max_signals': 20,
            'enabled': True,
            'notification_enabled': True,
            'trading_hours_only': True  # 仅交易时段监控
        }

        logger.info(f"🐂 牛市监控服务初始化 - 扫描间隔: {scan_interval_minutes}分钟")

    def start_monitoring(self):
        """启动监控服务"""
        if self.running:
            logger.warning("牛市监控服务已在运行")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

        logger.info("🐂 牛市监控服务已启动")

    def stop_monitoring(self):
        """停止监控服务"""
        if not self.running:
            logger.warning("牛市监控服务未运行")
            return

        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)

        logger.info("🐂 牛市监控服务已停止")

    def _monitor_loop(self):
        """监控循环"""
        logger.info("🐂 牛市监控循环开始")

        while self.running:
            try:
                # 检查是否在交易时段
                if self.monitor_config['trading_hours_only'] and not self._is_trading_time():
                    # 非交易时段，等待到下一个交易日
                    next_trading_time = self._get_next_trading_time()
                    if next_trading_time:
                        wait_seconds = (next_trading_time - datetime.now()).total_seconds()
                        if wait_seconds > 0:
                            logger.info(f"非交易时段，等待 {wait_seconds:.0f} 秒到下一个交易时段")
                            time.sleep(min(wait_seconds, 3600))  # 最多等待1小时
                    else:
                        time.sleep(300)  # 5分钟后重试
                    continue

                # 执行扫描
                self._execute_scan()

                # 等待到下次扫描
                time.sleep(self.scan_interval_minutes * 60)

            except Exception as e:
                self.error_count += 1
                logger.error(f"监控循环异常: {e}", exc_info=True)
                time.sleep(60)  # 出错后等待1分钟重试

        logger.info("🐂 牛市监控循环结束")

    def _execute_scan(self):
        """执行扫描"""
        try:
            start_time = datetime.now()

            # 创建策略实例
            strategy = BullMarketStrategy(
                sectors=self.monitor_config['sectors'],
                confidence_threshold=self.monitor_config['confidence_threshold'],
                debug_mode=False
            )

            # 执行扫描
            signals = strategy.scan()

            # 限制信号数量
            signals = signals[:self.monitor_config['max_signals']]

            elapsed = (datetime.now() - start_time).total_seconds()
            self.scan_count += 1
            self.last_scan_time = start_time

            logger.info(f"🐂 扫描完成: {len(signals)}条信号, 耗时{elapsed:.1f}秒")

            # 保存扫描结果
            if signals:
                self._save_scan_results(signals, elapsed)

                # 发送通知
                if self.monitor_config['notification_enabled']:
                    self._send_notifications(signals)

        except Exception as e:
            self.error_count += 1
            logger.error(f"扫描执行失败: {e}", exc_info=True)

    def _save_scan_results(self, signals: List[Signal], scan_time: float):
        """保存扫描结果"""
        try:
            bull_monitor_db.save_scan_result(signals, scan_time, self.monitor_config)
            logger.debug(f"保存了 {len(signals)} 条信号到数据库")
        except Exception as e:
            logger.error(f"保存扫描结果失败: {e}")

    def _send_notifications(self, signals: List[Signal]):
        """发送通知"""
        try:
            # 筛选高置信度信号
            high_conf_signals = [s for s in signals if s.confidence >= 85]

            if not high_conf_signals:
                return

            # 构建通知消息
            message = self._build_notification_message(high_conf_signals)

            # 创建通知字典（模拟monitor_db中的通知格式）
            notification = {
                'id': 0,  # 临时ID
                'symbol': 'BULL_MONITOR',
                'type': 'bull_monitor',
                'message': message,
                'price': 0.0,
                'sent': False,
                'created_at': datetime.now()
            }

            # 发送通知
            success = notification_service.send_notification(notification)

            if success:
                logger.info(f"发送了 {len(high_conf_signals)} 条信号的通知")
            else:
                logger.warning("通知发送失败")

        except Exception as e:
            logger.error(f"发送通知失败: {e}")

    def _build_notification_message(self, signals: List[Signal]) -> str:
        """构建通知消息"""
        lines = ["🐂 牛市选股监控发现投资机会："]

        for i, signal in enumerate(signals[:5], 1):  # 最多显示5条
            lines.append(f"{i}. {signal.name}({signal.code}) - {signal.action} ({signal.confidence:.0f}%)")

        if len(signals) > 5:
            lines.append(f"...还有{len(signals)-5}个信号")

        lines.append(f"\n扫描时间: {datetime.now().strftime('%H:%M:%S')}")

        return "\n".join(lines)

    def _is_trading_time(self) -> bool:
        """检查是否在交易时段"""
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()  # 0-6, 周一到周日

        # 周一到周五
        if weekday >= 5:
            return False

        # 交易时段：9:30-11:30, 13:00-15:00
        morning_start = datetime.strptime("09:30", "%H:%M").time()
        morning_end = datetime.strptime("11:30", "%H:%M").time()
        afternoon_start = datetime.strptime("13:00", "%H:%M").time()
        afternoon_end = datetime.strptime("15:00", "%H:%M").time()

        return (morning_start <= current_time <= morning_end) or \
               (afternoon_start <= current_time <= afternoon_end)

    def _get_next_trading_time(self) -> Optional[datetime]:
        """获取下一个交易时段开始时间"""
        now = datetime.now()

        # 如果是周末，等待到下周一
        if now.weekday() >= 5:  # 周六或周日
            days_to_monday = 7 - now.weekday()
            next_monday = now + timedelta(days=days_to_monday)
            return datetime.combine(next_monday.date(), datetime.strptime("09:30", "%H:%M").time())

        # 如果是工作日但不在交易时段
        current_time = now.time()
        morning_start = datetime.strptime("09:30", "%H:%M").time()
        afternoon_start = datetime.strptime("13:00", "%H:%M").time()

        if current_time < morning_start:
            # 还没到上午交易时段
            return datetime.combine(now.date(), morning_start)
        elif current_time < afternoon_start:
            # 上午交易时段已过，等待下午
            return datetime.combine(now.date(), afternoon_start)
        else:
            # 下午交易时段已过，等待明天
            tomorrow = now + timedelta(days=1)
            return datetime.combine(tomorrow.date(), morning_start)

    def update_config(self, config: Dict[str, Any]):
        """更新监控配置"""
        self.monitor_config.update(config)
        logger.info(f"牛市监控配置已更新: {config}")

    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            'running': self.running,
            'scan_interval_minutes': self.scan_interval_minutes,
            'last_scan_time': self.last_scan_time.isoformat() if self.last_scan_time else None,
            'scan_count': self.scan_count,
            'error_count': self.error_count,
            'config': self.monitor_config,
            'is_trading_time': self._is_trading_time()
        }

    def manual_scan(self) -> List[Signal]:
        """手动执行一次扫描"""
        logger.info("执行手动扫描")
        start_time = datetime.now()

        try:
            strategy = BullMarketStrategy(
                sectors=self.monitor_config['sectors'],
                confidence_threshold=self.monitor_config['confidence_threshold'],
                debug_mode=False
            )

            signals = strategy.scan()
            signals = signals[:self.monitor_config['max_signals']]

            elapsed = (datetime.now() - start_time).total_seconds()
            self.scan_count += 1
            self.last_scan_time = start_time

            # 保存结果
            if signals:
                self._save_scan_results(signals, elapsed)

            logger.info(f"手动扫描完成: {len(signals)}条信号")
            return signals

        except Exception as e:
            self.error_count += 1
            logger.error(f"手动扫描失败: {e}")
            return []


# 全局监控服务实例
bull_monitor_service = BullMarketMonitorService()