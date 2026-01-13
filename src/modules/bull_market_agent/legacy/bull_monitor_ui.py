"""
牛市选股监控UI
独立的监控界面，支持实时监控设置和管理
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .bull_monitor_service import bull_monitor_service
from .bull_monitor_db import bull_monitor_db
from src.core.logger import get_logger

logger = get_logger('bull_monitor_ui')


def display_bull_monitor():
    """牛市选股监控主界面"""
    st.markdown("## 🐂 牛市选股监控")

    st.markdown("""
    独立的实时监控模块，支持5分钟级别扫描牛市选股策略。
    自动检测投资机会并发送通知提醒。
    """)

    # 监控状态概览
    display_monitor_status()

    # 功能标签页
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 监控控制", "⚙️ 配置设置", "📈 扫描历史", "📋 统计分析"
    ])

    with tab1:
        display_monitor_control()

    with tab2:
        display_monitor_config()

    with tab3:
        display_scan_history()

    with tab4:
        display_monitor_statistics()


def display_monitor_status():
    """显示监控状态概览"""
    status = bull_monitor_service.get_status()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        running_status = "🟢 运行中" if status['running'] else "🔴 已停止"
        st.metric("监控状态", running_status)

    with col2:
        st.metric("扫描间隔", f"{status['scan_interval_minutes']}分钟")

    with col3:
        scan_count = status['scan_count']
        st.metric("扫描次数", scan_count)

    with col4:
        is_trading = status['is_trading_time']
        trading_status = "🟢 交易时段" if is_trading else "⚪ 非交易时段"
        st.metric("当前时段", trading_status)

    # 最后扫描时间
    if status['last_scan_time']:
        last_scan = datetime.fromisoformat(status['last_scan_time'])
        st.caption(f"最后扫描: {last_scan.strftime('%H:%M:%S')}")

    # 错误统计
    if status['error_count'] > 0:
        st.warning(f"⚠️ 累计错误: {status['error_count']}次")


def display_monitor_control():
    """监控控制面板"""
    st.markdown("### 🎛️ 监控控制")

    status = bull_monitor_service.get_status()
    config = bull_monitor_db.get_monitor_config()

    col1, col2, col3 = st.columns(3)

    with col1:
        if status['running']:
            if st.button("⏸️ 停止监控", type="secondary", use_container_width=True):
                bull_monitor_service.stop_monitoring()
                st.success("✅ 监控已停止")
                st.rerun()
        else:
            if st.button("▶️ 启动监控", type="primary", use_container_width=True):
                bull_monitor_service.start_monitoring()
                st.success("✅ 监控已启动")
                st.rerun()

    with col2:
        if st.button("🔄 手动扫描", use_container_width=True):
            with st.spinner("正在执行扫描..."):
                signals = bull_monitor_service.manual_scan()

            if signals:
                st.success(f"✅ 扫描完成，发现 {len(signals)} 个投资机会")

                # 显示结果预览
                df = pd.DataFrame([{
                    '股票代码': s.code,
                    '股票名称': s.name,
                    '操作建议': s.action,
                    '置信度': f"{s.confidence:.1f}%",
                    '当前价格': f"¥{s.price:.2f}"
                } for s in signals[:5]])  # 只显示前5个

                st.dataframe(df, use_container_width=True)

                if len(signals) > 5:
                    st.info(f"还有{len(signals)-5}个信号，查看扫描历史了解详情")
            else:
                st.info("📭 当前市场环境下未发现符合条件的投资机会")

    with col3:
        if st.button("🔍 检查状态", use_container_width=True):
            status = bull_monitor_service.get_status()
            st.json(status)

    # 监控配置概览
    st.markdown("#### 📋 当前配置")

    config_cols = st.columns(2)

    with config_cols[0]:
        st.markdown("**监控板块：**")
        sectors = config.get('sectors', [])
        if sectors:
            for sector in sectors:
                st.caption(f"• {sector}")
        else:
            st.caption("未设置")

    with config_cols[1]:
        st.markdown("**关键参数：**")
        st.caption(f"置信度阈值: {config.get('confidence_threshold', 80)}%")
        st.caption(f"最大信号数: {config.get('max_signals', 20)}")
        st.caption(f"仅交易时段: {'是' if config.get('trading_hours_only', True) else '否'}")
        st.caption(f"通知启用: {'是' if config.get('notification_enabled', True) else '否'}")


def display_monitor_config():
    """监控配置设置"""
    st.markdown("### ⚙️ 监控配置")

    # 获取当前配置
    current_config = bull_monitor_db.get_monitor_config()

    with st.form("bull_monitor_config_form"):
        st.markdown("#### 基础设置")

        col1, col2 = st.columns(2)

        with col1:
            confidence_threshold = st.slider(
                "置信度阈值",
                min_value=50,
                max_value=95,
                value=current_config.get('confidence_threshold', 80),
                help="只保存和通知高于此置信度的信号"
            )

            max_signals = st.slider(
                "最大信号数量",
                min_value=5,
                max_value=50,
                value=current_config.get('max_signals', 20),
                help="每次扫描最多保存的信号数量"
            )

        with col2:
            enabled = st.checkbox(
                "启用监控",
                value=current_config.get('enabled', True),
                help="是否启用自动监控功能"
            )

            notification_enabled = st.checkbox(
                "启用通知",
                value=current_config.get('notification_enabled', True),
                help="发现信号时是否发送通知"
            )

            trading_hours_only = st.checkbox(
                "仅交易时段监控",
                value=current_config.get('trading_hours_only', True),
                help="是否只在交易日交易时段进行监控"
            )

        st.markdown("#### 监控板块")

        # 默认板块选项
        default_sectors = {
            'BK0917': '半导体概念',
            'BK0480': '航天航空',
            'BK0916': 'CPO概念',
            'BK1033': '电池',
            'BK0737': '互联网服务',
            'BK0910': '新材料概念',
            'BK0896': '医疗器械',
            'BK0740': '云计算'
        }

        selected_sectors = st.multiselect(
            "选择要监控的板块",
            options=list(default_sectors.keys()),
            default=current_config.get('sectors', ['BK0917', 'BK0480', 'BK0916']),
            format_func=lambda x: f"{x} - {default_sectors.get(x, x)}",
            help="选择您想要监控的热门板块"
        )

        # 保存配置
        if st.form_submit_button("💾 保存配置", type="primary"):
            new_config = {
                'sectors': selected_sectors,
                'confidence_threshold': confidence_threshold,
                'max_signals': max_signals,
                'enabled': enabled,
                'notification_enabled': notification_enabled,
                'trading_hours_only': trading_hours_only
            }

            bull_monitor_db.save_monitor_config(new_config)
            bull_monitor_service.update_config(new_config)

            st.success("✅ 配置已保存")

            # 如果监控正在运行，需要重启
            if bull_monitor_service.running:
                st.info("🔄 检测到配置变更，已自动重启监控服务")
                bull_monitor_service.stop_monitoring()
                bull_monitor_service.start_monitoring()


def display_scan_history():
    """扫描历史记录"""
    st.markdown("### 📈 扫描历史")

    # 获取扫描记录
    recent_scans = bull_monitor_db.get_recent_scans(limit=100)

    if not recent_scans:
        st.info("📭 暂无扫描历史记录")
        return

    # 筛选选项
    col1, col2, col3 = st.columns(3)

    with col1:
        days_filter = st.selectbox(
            "时间范围",
            options=[1, 3, 7, 30, 90],
            index=2,  # 默认7天
            format_func=lambda x: f"最近{x}天"
        )

    with col2:
        min_signals = st.slider("最少信号数", 0, 20, 0)

    with col3:
        sort_by = st.selectbox(
            "排序方式",
            options=["created_at", "signal_count", "scan_time"],
            index=0,
            format_func=lambda x: {
                "created_at": "扫描时间",
                "signal_count": "信号数量",
                "scan_time": "扫描耗时"
            }.get(x, x)
        )

    # 筛选数据
    cutoff_time = datetime.now() - timedelta(days=days_filter)
    filtered_scans = [
        scan for scan in recent_scans
        if scan['created_at'] >= cutoff_time and scan['signal_count'] >= min_signals
    ]

    # 排序
    reverse_sort = sort_by == "created_at"  # 时间倒序，其他正序
    filtered_scans.sort(key=lambda x: x[sort_by], reverse=reverse_sort)

    st.markdown(f"#### 📊 扫描记录 ({len(filtered_scans)}条)")

    # 显示为表格
    if filtered_scans:
        df = pd.DataFrame([{
            '扫描时间': scan['created_at'].strftime('%m-%d %H:%M'),
            '信号数量': scan['signal_count'],
            '扫描耗时': f"{scan['scan_time']:.1f}s",
            '板块数量': len(scan['config'].get('sectors', [])),
            '置信度阈值': scan['config'].get('confidence_threshold', 80)
        } for scan in filtered_scans])

        st.dataframe(df, use_container_width=True)

        # 展开查看详情
        for i, scan in enumerate(filtered_scans):
            with st.expander(f"🔍 扫描详情 - {scan['created_at'].strftime('%m-%d %H:%M:%S')}", expanded=False):
                display_scan_detail(scan)


def display_scan_detail(scan: Dict[str, Any]):
    """显示扫描详情"""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**扫描配置：**")
        config = scan['config']
        st.json({
            'sectors': config.get('sectors', []),
            'confidence_threshold': config.get('confidence_threshold', 80),
            'max_signals': config.get('max_signals', 20)
        })

    with col2:
        st.markdown("**扫描统计：**")
        st.metric("信号数量", scan['signal_count'])
        st.metric("扫描耗时", f"{scan['scan_time']:.2f}秒")

    # 显示信号详情
    signals = scan['signals']
    if signals:
        st.markdown("**信号详情：**")

        signals_df = pd.DataFrame([{
            '股票代码': s['code'],
            '股票名称': s['name'],
            '所属板块': s['sector'],
            '操作建议': s['action'],
            '置信度': f"{s['confidence']:.1f}%",
            '当前价格': f"¥{s['price']:.2f}",
            '分析时间': datetime.fromisoformat(s['timestamp']).strftime('%H:%M:%S')
        } for s in signals])

        st.dataframe(signals_df, use_container_width=True, height=300)

        # 信号分布统计
        action_counts = {}
        for s in signals:
            action = s['action']
            action_counts[action] = action_counts.get(action, 0) + 1

        st.markdown("**信号分布：**")
        for action, count in action_counts.items():
            st.caption(f"{action}: {count}个")


def display_monitor_statistics():
    """监控统计分析"""
    st.markdown("### 📋 监控统计分析")

    # 时间范围选择
    days = st.selectbox(
        "统计时间范围",
        options=[1, 3, 7, 14, 30],
        index=2,  # 默认7天
        format_func=lambda x: f"最近{x}天"
    )

    # 获取统计数据
    stats = bull_monitor_db.get_scan_statistics(days=days)

    if not stats:
        st.warning("⚠️ 暂无统计数据")
        return

    # 关键指标
    st.markdown("#### 🎯 关键指标")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总扫描次数", stats.get('total_scans', 0))

    with col2:
        avg_time = stats.get('avg_scan_time', 0)
        st.metric("平均扫描耗时", f"{avg_time:.1f}秒")

    with col3:
        total_signals = stats.get('total_signals', 0)
        st.metric("累计信号数", total_signals)

    with col4:
        avg_signals = stats.get('avg_signals_per_scan', 0)
        st.metric("平均信号/次", f"{avg_signals:.1f}")

    # 详细统计
    st.markdown("#### 📊 详细统计")

    stat_cols = st.columns(2)

    with stat_cols[0]:
        st.markdown("**扫描效率：**")
        st.metric("高置信度信号", stats.get('high_conf_signals', 0))
        st.metric("信号发现率", f"{stats.get('high_conf_signals', 0)/max(stats.get('total_scans', 1), 1):.1f} 个/次")

    with stat_cols[1]:
        st.markdown("**时间分布：**")
        st.metric("统计周期", f"{days}天")
        if stats.get('total_scans', 0) > 0:
            scan_freq = days * 24 * 60 / stats['total_scans']  # 分钟
            st.metric("平均扫描间隔", f"{scan_freq:.0f}分钟")

    # 数据清理
    st.markdown("#### 🧹 数据管理")

    cleanup_col1, cleanup_col2 = st.columns(2)

    with cleanup_col1:
        if st.button("🗑️ 清理30天前数据", type="secondary"):
            deleted_count = bull_monitor_db.clear_old_scans(days=30)
            st.success(f"✅ 已清理 {deleted_count} 条旧记录")

    with cleanup_col2:
        if st.button("📊 刷新统计", type="secondary"):
            st.rerun()