"""
日志读取器 - 优雅实现
简化查询逻辑 + 清晰接口
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
from collections import Counter

from src.core.logger import get_logger

logger = get_logger('log_reader')


class LogReader:
    """日志读取器 - 优雅实现"""

    def __init__(self, log_dir: str = 'logs/bull_market'):
        self.log_dir = Path(log_dir)
        logger.debug(f"日志目录: {self.log_dir}")

    def read_latest_logs(self, hours: int = 24) -> List[Dict]:
        """
        优雅读取最近N小时日志

        Returns:
            日志条目列表
        """
        entries = []

        try:
            debug_files = sorted(self.log_dir.glob('debug_*.jsonl'), reverse=True)

            if not debug_files:
                logger.warning("未找到debug日志文件")
                return entries

            latest_file = debug_files[0]
            cutoff_time = datetime.now().timestamp() - hours * 3600

            with open(latest_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        timestamp = datetime.strptime(entry['timestamp'], '%H:%M:%S').timestamp()

                        if timestamp >= cutoff_time:
                            entries.append(entry)
                    except:
                        continue

            logger.debug(f"读取到{len(entries)}条日志（最近{hours}小时）")

        except Exception as e:
            logger.error(f"读取日志失败: {e}", exc_info=True)

        return entries

    def analyze_errors(self, hours: int = 24) -> Dict:
        """优雅分析错误"""
        entries = self.read_latest_logs(hours)
        errors = [e for e in entries if e.get('level') == 'ERROR']

        if not errors:
            return {'total': 0, 'by_type': {}, 'by_module': {}}

        error_types = Counter([e.get('error_type', 'Unknown') for e in errors])
        error_modules = Counter([e.get('module', 'Unknown') for e in errors])

        return {
            'total': len(errors),
            'by_type': dict(error_types),
            'by_module': dict(error_modules),
            'latest_errors': errors[-5:] if len(errors) > 5 else errors
        }

    def analyze_performance(self, hours: int = 24) -> Dict:
        """优雅分析性能"""
        entries = self.read_latest_logs(hours)
        scan_times = [e.get('scan_time') for e in entries if 'scan_time' in e]

        if not scan_times:
            return {}

        return {
            'avg_scan_time': sum(scan_times) / len(scan_times),
            'max_scan_time': max(scan_times),
            'min_scan_time': min(scan_times),
            'total_scans': len(scan_times)
        }

    def analyze_signals(self, hours: int = 24) -> Dict:
        """优雅分析信号"""
        entries = self.read_latest_logs(hours)
        signals = []

        for e in entries:
            if 'signal_code' in e:
                signals.append({
                    'code': e.get('signal_code'),
                    'name': e.get('signal_name'),
                    'action': e.get('action'),
                    'confidence': e.get('confidence'),
                    'timestamp': e.get('timestamp')
                })

        if not signals:
            return {}

        # 简化统计
        total = len(signals)
        actions = [s['action'] for s in signals]

        return {
            'total': total,
            'avg_confidence': sum(s['confidence'] for s in signals) / total if total > 0 else 0,
            'actions': {a: actions.count(a) for a in set(actions)} if actions else {}
        }

    def generate_debug_report(self, hours: int = 24) -> str:
        """
        优雅生成诊断报告

        Returns:
            格式化的报告字符串
        """
        report = []
        report.append("="*80)
        report.append(f"🔍 自我诊断报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"    时间范围: 最近{hours}小时")
        report.append("="*80)

        # 1. 错误分析
        error_analysis = self.analyze_errors(hours)
        report.append(f"\n【1️⃣ 错误分析】")
        report.append(f"    总错误数: {error_analysis['total']}")

        if error_analysis['total'] > 0:
            if error_analysis.get('by_type'):
                report.append(f"\n    按类型:")
                for error_type, count in error_analysis['by_type'].items():
                    report.append(f"        - {error_type}: {count}次")

            if error_analysis.get('by_module'):
                report.append(f"\n    按模块:")
                for module, count in error_analysis['by_module'].items():
                    report.append(f"        - {module}: {count}次")

            if error_analysis.get('latest_errors'):
                report.append(f"\n    最近错误:")
                for err in error_analysis['latest_errors']:
                    report.append(f"        - {err.get('module', 'Unknown')}: {err.get('message', 'Unknown')}")

        # 2. 性能分析
        perf_analysis = self.analyze_performance(hours)
        if perf_analysis:
            report.append(f"\n【2️⃣ 性能分析】")
            report.append(f"    扫描次数: {perf_analysis.get('total_scans', 0)}")
            report.append(f"    平均耗时: {perf_analysis.get('avg_scan_time', 0):.2f}秒")
            report.append(f"    最大耗时: {perf_analysis.get('max_scan_time', 0):.2f}秒")
            report.append(f"    最小耗时: {perf_analysis.get('min_scan_time', 0):.2f}秒")

        # 3. 信号分析
        signal_analysis = self.analyze_signals(hours)
        if signal_analysis:
            report.append(f"\n【3️⃣ 信号分析】")
            report.append(f"    总信号数: {signal_analysis.get('total', 0)}")

            if 'avg_confidence' in signal_analysis:
                report.append(f"    平均置信度: {signal_analysis['avg_confidence']:.2f}")

            if 'actions' in signal_analysis:
                report.append(f"\n    按操作类型:")
                for action, count in signal_analysis['actions'].items():
                    report.append(f"        - {action}: {count}次")

        # 4. 问题诊断
        report.append(f"\n【4️⃣ 问题诊断】")
        issues = self._diagnose_issues(error_analysis, perf_analysis, signal_analysis)

        for i, issue in enumerate(issues, 1):
            report.append(f"    问题{i}: {issue}")

        report.append("\n" + "="*80)

        return "\n".join(report)

    def _diagnose_issues(self, error_analysis: Dict, perf_analysis: Dict,
                         signal_analysis: Dict) -> List[str]:
        """优雅诊断问题"""
        issues = []

        # 简化诊断规则
        if error_analysis.get('total', 0) > 10:
            issues.append(f"❌ 错误过多（{error_analysis['total']}个/24小时），检查数据源稳定性")

        if perf_analysis and perf_analysis.get('avg_scan_time', 0) > 60:
            issues.append(f"⚠️ 扫描耗时过长（平均{perf_analysis['avg_scan_time']:.1f}秒），考虑优化筛选逻辑")

        if signal_analysis and signal_analysis.get('total', 0) == 0:
            issues.append(f"📭 24小时内无信号，检查筛选条件是否过严")

        return issues
