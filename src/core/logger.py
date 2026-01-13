"""
日志系统 - 仅控制台输出
支持：增强日志、AOP装饰器、堆栈追踪
"""

import sys
import logging
import datetime
import inspect
import threading
from typing import Any

LOG_LEVEL = logging.DEBUG
CONSOLE_LEVEL = logging.INFO
FILE_LEVEL = logging.DEBUG
LOG_FILE_PATH = "logs/app.log"

_loggers = {}
_lock = threading.Lock()


def _safe_format(value: Any, max_len: int = 300) -> str:
    try:
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            s = value.strip()
            return (s[:max_len] + "...") if len(s) > max_len else (s if s else "empty")
        elif isinstance(value, (list, tuple)):
            return f"[{len(value)} items]"
        elif isinstance(value, dict):
            return f"{{{len(value)} keys}}"
        else:
            s = str(value)
            return (s[:max_len] + "...") if len(s) > max_len else s
    except Exception:
        return "<error>"


class Logger:
    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._name = logger.name

    def _fmt(self, msg: str, **kwargs) -> str:
        if not kwargs:
            return msg
        extras = ", ".join(f"{k}={_safe_format(v)}" for k, v in kwargs.items())
        return f"{msg} | {extras}" if msg else extras

    def debug(self, msg: str, **kwargs):
        self._logger.debug(self._fmt(msg, **kwargs))

    def info(self, msg: str, **kwargs):
        self._logger.info(self._fmt(msg, **kwargs))

    def warning(self, msg: str, **kwargs):
        self._logger.warning(self._fmt(msg, **kwargs))

    def error(self, msg: str, **kwargs):
        self._logger.error(self._fmt(msg, **kwargs))

    def critical(self, msg: str, **kwargs):
        self._logger.critical(self._fmt(msg, **kwargs))

    def exception(self, msg: str, **kwargs):
        self._logger.error(self._fmt(msg, **kwargs), exc_info=True)

    def state(self, name: str, value: Any):
        self._logger.info(f"[STATE] {name} = {_safe_format(value)}")

    def data(self, name: str, data: dict):
        self._logger.info(f"[DATA] {name} = {_safe_format(data)}")

    def timing(self, operation: str, duration: float, **kwargs):
        parts = [f"[TIMING] {operation} = {duration:.3f}s"]
        if kwargs:
            parts.append(", ".join(f"{k}={_safe_format(v)}" for k, v in kwargs.items()))
        self._logger.info(" | ".join(parts))


class ConsoleFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35;1m',
        'RESET': '\033[0m'
    }

    def format(self, record):
        dt = datetime.datetime.fromtimestamp(record.created)
        ms = int(record.msecs)
        time_str = dt.strftime('%H:%M:%S') + f".{ms:03d}"
        level = record.levelname
        color = self.COLORS.get(level, '')
        reset = self.COLORS['RESET']
        name = record.name.split(":")[0]
        line = record.lineno
        msg = record.getMessage()
        return f"{time_str} {color}[{level:5}]{reset} {name}:{line:3} | {msg}"


def _get_logger(name: str) -> logging.Logger:
    if name in _loggers:
        return _loggers[name]

    with _lock:
        if name in _loggers:
            return _loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(LOG_LEVEL)
        logger.propagate = False

        if not logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(CONSOLE_LEVEL)
            console_handler.setFormatter(ConsoleFormatter())
            logger.addHandler(console_handler)

            import os
            log_dir = os.path.dirname(LOG_FILE_PATH)
            if log_dir and log_dir != '.' and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')

            file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
            file_handler.setLevel(FILE_LEVEL)
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        _loggers[name] = logger
        return logger


def get_logger(name: str = None):
    raw_logger = _get_logger(name or "app")
    return Logger(raw_logger)


def log_function_call(include_args: bool = True, include_result: bool = True):
    def decorator(f):
        def wrapper(*args, **kwargs):
            logger = get_logger(f.__module__)
            if include_args:
                sig = inspect.signature(f)
                params = dict(zip(list(sig.parameters.keys())[:len(args)], args))
                params.update(kwargs)
                safe_params = {k: _safe_format(v) for k, v in params.items()}
                logger.debug(f"[CALL] {f.__name__}({safe_params})")
            else:
                logger.debug(f"[CALL] {f.__name__}()")

            start = datetime.datetime.now()
            try:
                result = f(*args, **kwargs)
                dur = (datetime.datetime.now() - start).total_seconds()
                if include_result:
                    logger.debug(f"[RETURN] {f.__name__} => {_safe_format(result)} ({dur:.3f}s)")
                else:
                    logger.debug(f"[RETURN] {f.__name__} ({dur:.3f}s)")
                return result
            except Exception as e:
                dur = (datetime.datetime.now() - start).total_seconds()
                logger.exception(f"[ERROR] {f.__name__}: {e} ({dur:.3f}s)")
                raise

        return wrapper
    return decorator


def log_execution_time(threshold: float = 1.0):
    def decorator(f):
        def wrapper(*args, **kwargs):
            logger = get_logger(f.__module__)
            logger.debug(f"[START] {f.__name__}")
            start = datetime.datetime.now()
            try:
                result = f(*args, **kwargs)
                dur = (datetime.datetime.now() - start).total_seconds()
                if dur >= threshold:
                    logger.warning(f"[SLOW] {f.__name__} = {dur:.3f}s (threshold: {threshold}s)")
                else:
                    logger.debug(f"[END] {f.__name__} = {dur:.3f}s")
                return result
            except Exception as e:
                dur = (datetime.datetime.now() - start).total_seconds()
                logger.exception(f"[ERROR] {f.__name__}: {e} ({dur:.3f}s)")
                raise

        return wrapper
    return decorator


if __name__ == "__main__":
    logger = get_logger("test")

    logger.info("应用启动", version="2.0.0", port=8501)
    logger.warning("配置加载完成", configs=15)
    logger.error("数据库连接失败", host="localhost", port=5432)

    logger.state("active_users", 1234)
    logger.data("market_data", {"index": "沪深300"})
    logger.timing("数据加载", 2.345, rows=50000)

    @log_function_call()
    def test_func(a, b):
        return a + b

    @log_execution_time(0.1)
    def slow_func():
        import time
        time.sleep(0.2)
        return "done"

    test_func(1, 2)
    slow_func()

    try:
        1 / 0
    except:
        logger.exception("计算错误", operation="test")
