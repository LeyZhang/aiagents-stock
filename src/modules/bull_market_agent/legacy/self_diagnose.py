"""
自我诊断 - 优雅实现
保留核心功能，简化调用链
"""

from .log_reader import LogReader
from .log_writer import LogWriter
from src.core.logger import get_logger

logger = get_logger('self_diagnose')


def run_self_diagnosis(hours: int = 24) -> str:
    """
    优雅自我诊断

    Args:
        hours: 分析最近N小时

    Returns:
        诊断报告
    """
    log_writer = LogWriter()
    log_reader = LogReader()

    logger.info(f"🔍 开始自我诊断（最近{hours}小时）")

    try:
        # 优雅生成报告
        report = log_reader.generate_debug_report(hours)

        logger.info(f"✅ 诊断报告生成完成: {len(report.splitlines())}行")

        return report

    except Exception as e:
        error_msg = f"自我诊断失败: {e}"
        logger.error(error_msg, exc_info=True)
        return f"❌ {error_msg}"


def diagnose_signal_quality(signals: list) -> list:
    """
    诊断信号质量
    """
    issues = []

    if not signals:
        issues.append("无信号生成")
        return issues

    # 简化诊断
    confidences = [s.confidence for s in signals]
    avg_conf = sum(confidences) / len(confidences)

    if avg_conf < 70:
        issues.append(f"平均置信度过低（{avg_conf:.1f}%）")

    if max(confidences) - min(confidences) > 30:
        issues.append(f"置信度波动过大")

    return issues
