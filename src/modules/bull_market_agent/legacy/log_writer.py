"""
日志写入器 - 优雅实现
简化日志格式 + 统一接口
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from src.core.logger import get_logger

logger = get_logger('log_writer')


class LogWriter:
    """日志写入器 - 优雅实现"""

    def __init__(self, log_dir: str = 'logs/bull_market'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 按日期分组日志
        today = datetime.now().strftime('%Y-%m-%d')
        self.log_file = self.log_dir / f'strategy_{today}.log'
        self.debug_file = self.log_dir / f'debug_{today}.jsonl'

        logger.debug(f"日志目录: {self.log_dir}")

    def write(self, level: str, module: str, message: str, **kwargs):
        """
        优雅写入日志

        Args:
            level: INFO/DEBUG/ERROR
            module: 模块名称
            message: 日志消息
            **kwargs: 额外字段
        """
        timestamp = datetime.now().strftime('%H:%M:%S')

        # 文本日志（人类可读）
        log_line = f"{timestamp} | {level:8s} | {module:20s} | {message}\n"

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            logger.error(f"写入日志文件失败: {e}", exc_info=True)

    def write_scan_result(self, signals: list, scan_time: float):
        """优雅写入扫描结果"""
        self.write('INFO', 'SCANNER',
                 f"扫描完成: {len(signals)}条信号, 耗时{scan_time:.2f}秒")

        # 写入详细信号（简化）
        for i, signal in enumerate(signals, 1):
            self.write('DEBUG', 'SCANNER',
                     f"信号#{i}: {signal.name} ({signal.code}) - {signal.action}")

    def write_backtest_result(self, result: Dict):
        """优雅写入回测结果"""
        self.write('INFO', 'BACKTEST',
                 f"回测完成: 胜率{result.get('win_rate', 0):.2f}%, 交易{result.get('total_trades', 0)}笔")

    def write_error(self, module: str, error: Exception, context: Dict = None):
        """优雅写入错误"""
        self.write('ERROR', module,
                 f"异常: {type(error).__name__}: {str(error)}")
