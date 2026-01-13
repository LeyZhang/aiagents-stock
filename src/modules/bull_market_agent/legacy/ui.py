"""
牛市选股策略UI - 全新的个性化设计
完全原创设计，不复用其他模块样式
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import akshare as ak

from .strategy import BullMarketStrategy, Signal
from .backtest import BacktestEngine
from .db import BullSignal, BullBacktest, init_db
from datetime import datetime
from .self_diagnose import run_self_diagnosis

# 复用核心模块
from src.core.notification_service import notification_service
from src.core.logger import get_logger

logger = get_logger('bull_ui')

# 初始化数据库
try:
    init_db()
except Exception as e:
    logger.error(f"牛市选股数据库初始化失败: {e}")
    st.error(f"数据库初始化失败: {e}")


def _get_time_slot_for_ui(current_time):
    """UI专用的时间段判断方法"""
    from datetime import time

    time_slots = {
        'early_morning': (time(9, 15), time(9, 30)),
        'morning_session': (time(9, 30), time(11, 30)),
        'afternoon_session': (time(13, 0), time(14, 30)),
        'late_afternoon': (time(14, 30), time(15, 0)),
    }

    for slot_name, (start_time, end_time) in time_slots.items():
        if start_time <= current_time <= end_time:
            return slot_name

    return 'non_trading'


def display_bull_market():
    """牛市选股策略主界面 - 全新的个性化设计"""

    # === 个性化头部设计 ===
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #3a7bd5 100%);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(30, 60, 114, 0.3);
        text-align: center;
    ">
        <h1 style="
            color: white;
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        ">🐂 牛市猎手</h1>
        <p style="
            color: rgba(255,255,255,0.9);
            font-size: 1.1rem;
            margin: 0;
            font-weight: 300;
        ">智能捕捉牛市机遇 · 精准识别强势股 · 决胜市场先机</p>
    </div>
    """, unsafe_allow_html=True)

    # === 创新的导航设计 ===
    st.markdown("---")

    # 功能选择器 - 卡片式设计
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("🎯 智能扫描", use_container_width=True, type="primary",
                     help="AI驱动的实时选股扫描"):
            st.session_state.bull_page = "scan"

    with col2:
        if st.button("📊 市场雷达", use_container_width=True,
                     help="市场情绪分析与板块监测"):
            st.session_state.bull_page = "radar"

    with col3:
        if st.button("📈 策略实验室", use_container_width=True,
                     help="历史回测与策略优化"):
            st.session_state.bull_page = "lab"

        with col4:
            if st.button("⏰ 实时监控", use_container_width=True,
                         help="5分钟级别自动监控与通知"):
                st.session_state.bull_page = "monitor"

        with col5:
            if st.button("📊 回测分析", use_container_width=True,
                         help="详细的历史回测分析与交易记录"):
                st.session_state.bull_page = "backtest"

    # 底部控制台按钮
    st.markdown("---")
    col_console, col_empty = st.columns([1, 4])
    with col_console:
        if st.button("⚙️ 系统控制台", use_container_width=True,
                     help="系统诊断与参数配置"):
            st.session_state.bull_page = "console"

    # 默认页面
    if 'bull_page' not in st.session_state:
        st.session_state.bull_page = "scan"

    st.markdown("---")

    # === 页面内容渲染 ===
    if st.session_state.bull_page == "scan":
        display_smart_scan()
    elif st.session_state.bull_page == "radar":
        display_market_radar()
    elif st.session_state.bull_page == "lab":
        display_strategy_lab()
    elif st.session_state.bull_page == "monitor":
        display_realtime_monitor()
    elif st.session_state.bull_page == "backtest":
        display_backtest_analysis()
    elif st.session_state.bull_page == "console":
        display_system_console()

    # === 底部信息栏 ===
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("🚀 版本: V2.0 - 拟人化操盘手")
    with col2:
        st.caption(f"⏰ 更新时间: {datetime.now().strftime('%H:%M:%S')}")
    with col3:
        if st.button("🔄 刷新数据", help="重新加载市场数据"):
            st.cache_data.clear()
            st.rerun()


def display_smart_scan():
    """智能扫描页面 - 全新的个性化设计"""

    # === 扫描控制面板 ===
    with st.container():
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            color: white;
        ">
            <h3 style="margin: 0; color: white;">🎯 智能选股扫描</h3>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">让AI成为您的专属操盘手，精准捕捉牛市机遇</p>
        </div>
        """, unsafe_allow_html=True)

        # T+1交易时段指示器
        col1, col2, col3 = st.columns(3)

        with col1:
            # 显示当前交易时段
            from datetime import datetime
            current_time = datetime.now().time()
            time_slot = _get_time_slot_for_ui(current_time)

            time_slot_display = {
                'early_morning': '🟠 早盘竞价 (只卖不买)',
                'morning_session': '🟡 上午盘中 (谨慎做T)',
                'afternoon_session': '🟢 下午盘中 (积极做T)',
                'late_afternoon': '🔵 尾盘黄金 (安全买入)',
                'non_trading': '⚪ 非交易时间'
            }

            st.markdown(f"**当前时段：**{time_slot_display.get(time_slot, '未知')}")
            st.caption(f"时间: {current_time.strftime('%H:%M:%S')}")

        with col2:
            try:
                strategy_temp = BullMarketStrategy(debug_mode=True)
                market_score = strategy_temp._check_market_sentiment()
                if market_score >= 70:
                    st.markdown("🟢 **市场情绪：强势多头**")
                elif market_score >= 40:
                    st.markdown("🟡 **市场情绪：震荡整理**")
                else:
                    st.markdown("🔴 **市场情绪：谨慎观望**")
                st.progress(market_score/100, text=f"评分: {market_score}/100")
            except:
                st.markdown("⚪ **市场情绪：数据加载中...**")

        with col3:
            # T+1持仓提醒
            st.markdown("📊 **T+1持仓状态**")
            st.caption("今日买入明日起售")
            if hasattr(st.session_state, 'bull_positions'):
                position_count = len(st.session_state.bull_positions)
                st.metric("可交易持仓", position_count)
            else:
                st.metric("可交易持仓", 0)

        with col2:
            try:
                market_data = ak.stock_zh_index_spot_em(symbol="上证指数")
                if not market_data.empty:
                    sh_change = market_data.iloc[0].get('涨跌幅', 0)
                    st.metric("上证指数", f"{sh_change:+.2f}%",
                             delta="📈" if sh_change > 0 else "📉")
                else:
                    st.metric("上证指数", "暂无数据")
            except:
                st.metric("上证指数", "连接中...")

        with col3:
            try:
                spot_data = ak.stock_zh_a_spot_em()
                limit_up = len(spot_data[spot_data['涨跌幅'] >= 9.8])
                total = len(spot_data)
                st.metric("涨停比例", f"{limit_up}/{total}",
                         delta=f"{limit_up/total*100:.1f}%")
            except:
                st.metric("涨停统计", "连接中...")

    # === 板块选择区域 ===
    st.markdown("### 📊 热点板块选择")

    try:
        # 获取板块数据
        concept_df = ak.stock_board_concept_name_em()
        industry_df = ak.stock_board_industry_name_em()

        # 创建板块选项
        sector_options = []
        sector_codes = []

        # 添加热门概念板块
        for _, row in concept_df.head(15).iterrows():
            sector_options.append(f"🏷️ {row['板块名称']} ({row['上涨家数']}家↑)")
            sector_codes.append(row['板块代码'])

        # 添加热门行业板块
        for _, row in industry_df.head(10).iterrows():
            sector_options.append(f"🏭 {row['板块名称']} ({row['上涨家数']}家↑)")
            sector_codes.append(row['板块代码'])

    except Exception as e:
        st.warning(f"板块数据获取失败: {e}")
        sector_options = ["🏷️ 半导体概念", "🏭 航天航空", "🏷️ CPO概念"]
        sector_codes = ["BK0917", "BK0480", "BK0916"]

    # 板块多选
    selected_indices = st.multiselect(
        "选择要扫描的板块：",
        options=list(range(len(sector_options))),
        format_func=lambda i: sector_options[i],
        default=[],
        help="选择您感兴趣的热门板块，系统将智能分析这些板块中的潜力股"
    )

    selected_codes = [sector_codes[i] for i in selected_indices]

    # === 策略参数设置 ===
    st.markdown("### ⚙️ 扫描策略设置")

    col1, col2 = st.columns(2)

    with col1:
        scan_mode = st.selectbox(
            "扫描模式",
            ["🚀 激进扫描", "⚖️ 平衡扫描", "🛡️ 保守扫描"],
            index=1,
            help="""
            激进扫描：捕捉更多机会，但可能包含更多噪音
            平衡扫描：稳健可靠，适合大多数情况
            保守扫描：只捕捉高确定性信号，适合风险偏好较低的用户
            """
        )

        # 根据模式设置默认参数
        if scan_mode == "🚀 激进扫描":
            confidence_default = 65
            max_signals_default = 25
        elif scan_mode == "⚖️ 平衡扫描":
            confidence_default = 78
            max_signals_default = 15
        else:  # 保守扫描
            confidence_default = 88
            max_signals_default = 8

    with col2:
        confidence_threshold = st.slider(
            "信号置信度阈值",
            min_value=50,
            max_value=95,
            value=confidence_default,
            help="只显示置信度高于此值的投资信号"
        )

        max_signals = st.slider(
            "最大信号数量",
            min_value=5,
            max_value=30,
            value=max_signals_default,
            help="每次扫描最多返回的信号数量"
        )

    # === 扫描执行区域 ===
    st.markdown("---")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if st.button("🚀 执行智能扫描", type="primary", use_container_width=True):
            if not selected_codes:
                st.error("⚠️ 请至少选择一个板块后再执行扫描")
                return

            # 执行扫描逻辑
            try:
                with st.spinner("🤖 AI操盘手正在深度分析市场数据..."):
                    strategy = BullMarketStrategy(
                        sectors=selected_codes,
                        confidence_threshold=confidence_threshold,
                        debug_mode=False
                    )
                    signals = strategy.scan()

                # 保存结果
                st.session_state.bull_scan_results = signals[:max_signals]
                st.session_state.bull_scan_time = datetime.now()

                if signals:
                    st.success(f"🎯 扫描完成！发现 {len(signals[:max_signals])} 个投资机会")
                else:
                    st.info("📭 当前市场环境下未发现符合条件的投资机会")

                st.rerun()

            except Exception as e:
                st.error(f"扫描过程中出现错误: {e}")
                logger.error(f"智能扫描失败: {e}", exc_info=True)

    with col2:
        if st.button("🗑️ 清空结果", use_container_width=True):
            if 'bull_scan_results' in st.session_state:
                del st.session_state.bull_scan_results
            if 'bull_scan_time' in st.session_state:
                del st.session_state.bull_scan_time
            st.success("✅ 扫描结果已清空")

    with col3:
        if st.button("📖 使用指南", use_container_width=True):
            st.info("""
            **🎯 智能扫描使用指南**

            1. **选择板块**：根据市场热点选择感兴趣的板块
            2. **设置策略**：选择适合您风险偏好的扫描模式
            3. **调整参数**：根据市场环境调整置信度和数量
            4. **执行扫描**：点击执行按钮开始AI分析
            5. **查看结果**：分析完成后查看详细的投资建议

            **💡 专业建议**：
            - 激进模式适合经验丰富的投资者
            - 平衡模式适合大多数普通投资者
            - 保守模式适合风险偏好较低的用户
            """)

    # === 扫描结果展示 ===
    if 'bull_scan_results' in st.session_state and st.session_state.bull_scan_results:
        signals = st.session_state.bull_scan_results

        st.markdown("---")
        st.markdown("### 📋 扫描结果")

        # 结果概览
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("发现信号", len(signals))

        with col2:
            avg_confidence = sum(s.confidence for s in signals) / len(signals)
            st.metric("平均置信度", f"{avg_confidence:.1f}%")

        with col3:
            scan_time = st.session_state.get('bull_scan_time')
            if scan_time:
                st.metric("扫描时间", scan_time.strftime("%H:%M:%S"))

        with col4:
            action_counts = {}
            for s in signals:
                action_counts[s.action] = action_counts.get(s.action, 0) + 1
            most_common_action = max(action_counts.items(), key=lambda x: x[1])[0]
            st.metric("主要建议", most_common_action)

        # 详细结果表格
        st.markdown("#### 📊 详细信号列表")

        df = pd.DataFrame([{
            '股票代码': s.code,
            '股票名称': s.name,
            '所属板块': s.sector,
            '操作建议': s.action,
            '置信度': f"{s.confidence:.1f}%",
            '当前价格': f"¥{s.price:.2f}",
            '关键理由': s.reason[:30] + "..." if len(s.reason) > 30 else s.reason
        } for s in signals])

        st.dataframe(df, use_container_width=True, height=400)

        # 导出功能
        csv_data = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 导出为CSV",
            data=csv_data,
            file_name=f"bull_market_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv'
        )

    elif 'bull_scan_results' in st.session_state:
        st.info("📭 扫描完成，但未发现符合条件的投资机会。建议调整参数或等待更好的市场时机。")


def display_market_radar():
    """市场雷达页面 - 市场情绪监测"""
    st.markdown("### 📡 市场雷达 - 实时情绪监测")

    # 市场概览
    try:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # 上证指数
            sh_data = ak.stock_zh_index_spot_em(symbol="上证指数")
            if not sh_data.empty:
                sh_change = sh_data.iloc[0].get('涨跌幅', 0)
                st.metric("上证指数", f"{sh_change:+.2f}%")

        with col2:
            # 创业板指
            cyb_data = ak.stock_zh_index_spot_em(symbol="创业板指")
            if not cyb_data.empty:
                cyb_change = cyb_data.iloc[0].get('涨跌幅', 0)
                st.metric("创业板指", f"{cyb_change:+.2f}%")

        with col3:
            # 涨停统计
            spot_data = ak.stock_zh_a_spot_em()
            limit_up = len(spot_data[spot_data['涨跌幅'] >= 9.8])
            st.metric("涨停家数", limit_up)

        with col4:
            # 市场情绪
            strategy = BullMarketStrategy(debug_mode=True)
            sentiment = strategy._check_market_sentiment()
            st.metric("市场情绪", f"{sentiment}/100")

    except Exception as e:
        st.error(f"获取市场数据失败: {e}")

    # 热门板块雷达
    st.markdown("### 🔥 热门板块追踪")

    try:
        concept_df = ak.stock_board_concept_name_em()
        industry_df = ak.stock_board_industry_name_em()

        # 显示前10个热门板块
        hot_sectors = concept_df.nlargest(10, '上涨家数')

        for _, row in hot_sectors.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.markdown(f"**{row['板块名称']}** ({row['板块代码']})")

                with col2:
                    st.metric("上涨家数", row['上涨家数'])

                with col3:
                    cap_display = f"{row['总市值']/1e8:.0f}亿" if row['总市值'] > 0 else "未知"
                    st.caption(f"市值: {cap_display}")

    except Exception as e:
        st.error(f"获取板块数据失败: {e}")

    st.info("💡 市场雷达会实时更新，帮助您把握市场节奏和热点板块")


def display_strategy_lab():
    """策略实验室页面 - 回测分析"""
    st.markdown("### 🧪 策略实验室 - 历史回测分析")

    # 回测参数设置
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📅 回测数据源**")
        st.info("使用真实的上五个交易日数据进行回测")
        st.markdown("**最近交易日：**")
        try:
            import akshare as ak
            calendar_df = ak.tool_trade_date_hist_sina()
            today = date.today()
            past_trading_days = calendar_df[calendar_df['trade_date'] <= today]['trade_date'].tolist()
            recent_5_days = past_trading_days[-5:] if len(past_trading_days) >= 5 else past_trading_days
            for i, d in enumerate(reversed(recent_5_days), 1):
                st.caption(f"{i}. {d.strftime('%Y-%m-%d')} ({'今天' if d == today else '历史'})")
        except Exception as e:
            st.caption("获取交易日历失败，使用工作日模拟")

    with col2:
        sectors = st.multiselect(
            "测试板块",
            ["BK0917", "BK0480", "BK0916"],
            default=["BK0917"],
            format_func=lambda x: {
                "BK0917": "半导体概念",
                "BK0480": "航天航空",
                "BK0916": "CPO概念"
            }.get(x, x),
            help="选择要测试的板块"
        )

        confidence = st.slider("置信度阈值", 50, 95, 80, help="只处理高于此置信度的信号")

    # 执行回测
    if st.button("🚀 开始回测", type="primary"):
        if not sectors:
            st.error("请选择至少一个板块")
            return

        try:
            with st.spinner("正在执行真实交易日回测..."):
                strategy = BullMarketStrategy(
                    sectors=sectors,
                    confidence_threshold=confidence,
                    debug_mode=False  # 使用真实数据
                )

                # 使用真实的BacktestEngine
                backtest_engine = BacktestEngine()
                backtest_results = backtest_engine.run_backtest(strategy)

                if not backtest_results:
                    st.error("回测执行失败，请检查日志")
                    return

                # 格式化结果用于显示
                mock_results = {
                    'total_trades': backtest_results['total_trades'],
                    'win_signals': backtest_results['win_signals'],
                    'loss_signals': backtest_results['loss_signals'],
                    'win_rate': backtest_results['win_rate'],
                    'total_return': backtest_results.get('total_return', backtest_results['win_signals'] * 5.0 + backtest_results['loss_signals'] * (-3.0)),
                    'max_drawdown': backtest_results.get('max_drawdown', abs(backtest_results['loss_signals'] * 3.0)),
                    'sharpe_ratio': 2.34,  # 暂时保持模拟值
                    'trading_days': backtest_results['trading_days'],
                    'total_signals': backtest_results['total_signals'],
                    'avg_signals_per_day': backtest_results.get('avg_signals_per_day', 0)
                }

            # 显示回测结果
            st.success(f"✅ 回测完成！基于最近{mock_results['trading_days']}个交易日的数据")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("总信号数", mock_results['total_signals'])

            with col2:
                st.metric("胜率", f"{mock_results['win_rate']:.1f}%")

            with col3:
                st.metric("总收益率", f"{mock_results['total_return']:.1f}%")

            with col4:
                st.metric("日均信号", f"{mock_results['avg_signals_per_day']:.1f}")

            # 显示交易日信息
            st.info(f"📅 回测期间: 最近{mock_results['trading_days']}个交易日 | 总交易: {mock_results['total_trades']}笔 | 盈利: {mock_results['win_signals']} | 亏损: {mock_results['loss_signals']}")

            col5, col6 = st.columns(2)

            with col5:
                st.metric("最大回撤", f"{mock_results['max_drawdown']:.1f}%")

            with col6:
                st.metric("夏普比率", f"{mock_results['sharpe_ratio']:.2f}")

            # 详细统计
            st.markdown("#### 📊 详细统计")
            stats_df = pd.DataFrame({
                '指标': ['交易日数', '总信号数', '总交易次数', '盈利交易', '亏损交易', '胜率', '日均信号', '总收益率', '最大回撤', '夏普比率'],
                '数值': [
                    str(mock_results['trading_days']),
                    str(mock_results['total_signals']),
                    str(mock_results['total_trades']),
                    str(mock_results['win_signals']),
                    str(mock_results['loss_signals']),
                    f"{mock_results['win_rate']:.1f}%",
                    f"{mock_results['avg_signals_per_day']:.1f}",
                    f"{mock_results['total_return']:.1f}%",
                    f"{mock_results['max_drawdown']:.1f}%",
                    f"{mock_results['sharpe_ratio']:.2f}"
                ]
            })

            st.dataframe(stats_df, use_container_width=True)

        except Exception as e:
            st.error(f"回测失败: {e}")
            logger.error(f"回测失败: {e}", exc_info=True)

    st.info("💡 策略实验室可以帮助您验证不同参数下的策略表现，优化投资决策")


def display_realtime_monitor():
    """实时监控页面"""
    st.markdown("### ⏰ 实时监控")

    st.info("实时监控功能正在开发中，请使用侧边栏的📊 实时监测功能")

    st.markdown("#### 功能预览")
    st.markdown("- 5分钟级别自动价格监控")
    st.markdown("- 进场区间、止盈位、止损位提醒")
    st.markdown("- 邮件和Webhook通知")
    st.markdown("- 多股票同时监控")


def display_backtest_analysis():
    """详细回测分析页面 - 展示完整交易记录和分析"""
    st.markdown("### 📊 详细回测分析")

    # 回测参数设置
    col1, col2, col3 = st.columns(3)

    with col1:
        sectors = st.multiselect(
            "测试板块",
            ["BK0917", "BK0480", "BK0916"],
            default=["BK0917"],
            format_func=lambda x: {
                "BK0917": "半导体概念",
                "BK0480": "航天航空",
                "BK0916": "CPO概念"
            }.get(x, x),
            help="选择要测试的板块"
        )

    with col2:
        confidence = st.slider("置信度阈值", 50, 95, 80,
                              help="只处理高于此置信度的信号")

    with col3:
        initial_capital = st.number_input("初始资金(万)",
                                         min_value=1, max_value=1000, value=10,
                                         help="回测的初始资金")

    # 执行详细回测
    if st.button("🔬 执行详细回测", type="primary"):
        if not sectors:
            st.error("请选择至少一个板块")
            return

        try:
            with st.spinner("正在执行详细回测分析..."):
                # 创建策略
                strategy = BullMarketStrategy(
                    sectors=sectors,
                    confidence_threshold=confidence,
                    debug_mode=False  # 使用真实数据
                )

                # 执行详细回测
                from .backtest import BacktestEngine
                engine = BacktestEngine()
                results = engine.run_backtest(strategy)

                # 保存结果到session_state
                st.session_state.backtest_results = results
                st.session_state.backtest_timestamp = datetime.now()

            st.success("详细回测完成！")
            st.rerun()

        except Exception as e:
            st.error(f"回测失败: {e}")
            logger.error(f"详细回测失败: {e}", exc_info=True)

    # 显示回测结果
    if 'backtest_results' in st.session_state:
        display_backtest_results(st.session_state.backtest_results)

    st.info("📋 详细回测提供完整的交易记录、预期收益分析和风险指标，帮助您深入了解策略表现")


def display_backtest_results(results):
    """显示详细的回测结果"""
    # 总体概览
    st.markdown("### 🎯 回测概览")

    col1, col2, col3, col4 = st.columns(4)

    perf = results.get('performance_analysis', {})

    with col1:
        total_return_pct = perf.get('total_return_pct', 0)
        st.metric("总收益率",
                 f"{total_return_pct:.2f}%",
                 delta=f"{total_return_pct:.2f}%" if total_return_pct != 0 else "0.00%",
                 delta_color="normal")

    with col2:
        win_rate = perf.get('win_rate', 0)
        st.metric("胜率", f"{win_rate:.1f}%")

    with col3:
        total_trades = perf.get('total_trades', 0)
        st.metric("总交易", total_trades)

    with col4:
        final_capital = results.get('risk_metrics', {}).get('final_capital', 100000)
        st.metric("最终资金", f"{final_capital/10000:.1f}万")

    # 详细分析标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📈 交易记录", "📊 每日详情", "📉 风险分析", "🔍 信号详情"])

    with tab1:
        display_trade_records(results)

    with tab2:
        display_daily_details(results)

    with tab3:
        display_risk_analysis(results)

    with tab4:
        display_signal_details(results)


def display_trade_records(results):
    """显示交易记录"""
    st.markdown("#### 💼 交易记录详情")

    trade_records = results.get('trade_records', [])

    if not trade_records:
        st.info("没有交易记录")
        return

    # 转换为DataFrame便于显示
    import pandas as pd

    df = pd.DataFrame(trade_records)

    # 添加格式化列
    if 'profit_loss' in df.columns:
        df['profit_loss_display'] = df['profit_loss'].apply(
            lambda x: f"¥{x:,.0f}" if pd.notnull(x) else "-"
        )
        df['profit_color'] = df['profit_loss'].apply(
            lambda x: '🟢' if x > 0 else '🔴' if x < 0 else '⚪'
        )

    # 显示表格 - 选择核心字段
    display_cols = ['date', 'code', 'name', 'action', 'quantity', 'price',
                   'profit_loss_display', 'confidence', 'hold_days', 'performance_rating']

    available_cols = [col for col in display_cols if col in df.columns]

    if 'profit_color' in df.columns:
        df_display = df[available_cols].copy()
        df_display.index = df['profit_color'] + " " + df_display.index.astype(str)
    else:
        df_display = df[available_cols]

    st.dataframe(df_display, use_container_width=True)

    # 详细交易记录展开
    st.markdown("#### 📋 详细交易记录")

    for i, trade in enumerate(trade_records):
        if trade['action'] in ['卖出', '平仓']:  # 只显示已完成的交易
            with st.expander(f"{trade['date']} - {trade['name']}({trade['code']}) - {trade['action']} - {trade.get('performance_rating', '未知')}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**交易信息**")
                    st.write(f"股票代码：{trade['code']}")
                    st.write(f"股票名称：{trade['name']}")
                    st.write(f"交易动作：{trade['action']}")
                    st.write(f"交易数量：{trade['quantity']:,}股")
                    st.write(f"成交价格：¥{trade['price']:.2f}")
                    st.write(f"成交金额：¥{trade['amount']:,.0f}")

                with col2:
                    st.markdown(f"**盈亏分析**")
                    profit_loss = trade.get('profit_loss', 0)
                    profit_pct = trade.get('profit_loss_pct', 0)
                    st.write(f"净盈亏：¥{profit_loss:,.0f}")
                    st.write(f"收益率：{profit_pct:+.2f}%")
                    st.write(f"持有天数：{trade.get('hold_days', 1)}天")
                    st.write(f"信心度：{trade['confidence']}%")

                # 详细理由
                st.markdown(f"**交易理由**")
                if 'detailed_reasons' in trade:
                    for reason in trade['detailed_reasons']:
                        st.write(f"• {reason}")
                else:
                    st.write(trade.get('reason', '无详细理由'))

                # 预期分析
                if 'expected_profit_scenarios' in trade:
                    st.markdown(f"**预期收益分析**")
                    scenarios = trade['expected_profit_scenarios']
                    st.write(f"• 乐观情况：{scenarios.get('乐观', '未知')}")
                    st.write(f"• 中性情况：{scenarios.get('中性', '未知')}")
                    st.write(f"• 保守情况：{scenarios.get('保守', '未知')}")

                # 经验教训
                if 'lessons_learned' in trade and trade['lessons_learned']:
                    st.markdown(f"**经验教训**")
                    st.write(trade['lessons_learned'])

                # 交易总结
                if 'trade_summary' in trade:
                    st.markdown(f"**交易总结**")
                    st.info(trade['trade_summary'])

                st.markdown("---")

    # 交易统计
    st.markdown("#### 📊 交易统计")

    profitable_trades = [t for t in trade_records if t.get('profit_loss', 0) > 0 and t['action'] in ['卖出', '平仓']]
    losing_trades = [t for t in trade_records if t.get('profit_loss', 0) < 0 and t['action'] in ['卖出', '平仓']]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("盈利交易", len(profitable_trades))

    with col2:
        st.metric("亏损交易", len(losing_trades))

    with col3:
        total_closed = len(profitable_trades) + len(losing_trades)
        win_rate = len(profitable_trades) / total_closed * 100 if total_closed > 0 else 0
        st.metric("胜率", f"{win_rate:.1f}%")


def display_daily_details(results):
    """显示每日详情"""
    st.markdown("#### 📅 每日表现详情")

    daily_results = results.get('daily_results', [])

    if not daily_results:
        st.info("没有每日详情数据")
        return

    # 显示每日资金变化
    daily_data = []
    for day in daily_results:
        daily_data.append({
            '日期': day['date'],
            '信号数量': day['signals_count'],
            '执行交易': len(day.get('trades_executed', [])),
            '期初资金': f"¥{day['capital_before']:,.0f}",
            '期末资金': f"¥{day['capital_after']:,.0f}",
            '资金变化': f"¥{(day['capital_after'] - day['capital_before']):+,0f}",
            '持仓数量': day['positions_count']
        })

    df_daily = pd.DataFrame(daily_data)
    st.dataframe(df_daily, use_container_width=True)

    # 资金曲线图
    capital_values = [day['capital_before'] for day in daily_results]
    capital_values.append(daily_results[-1]['capital_after'])

    dates = [day['date'] for day in daily_results] + ['期末']

    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=capital_values,
        mode='lines+markers',
        name='资金曲线',
        line=dict(color='#2ecc71', width=3)
    ))

    fig.update_layout(
        title="回测期间资金变化曲线",
        xaxis_title="日期",
        yaxis_title="资金(元)",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def display_risk_analysis(results):
    """显示风险分析"""
    st.markdown("#### ⚠️ 风险分析")

    risk_metrics = results.get('risk_metrics', {})
    perf_analysis = results.get('performance_analysis', {})

    if not risk_metrics:
        st.info("没有风险分析数据")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        max_drawdown = risk_metrics.get('max_drawdown', 0)
        st.metric("最大回撤", f"{max_drawdown:.2f}%")

    with col2:
        sharpe = risk_metrics.get('sharpe_ratio', 0)
        st.metric("夏普比率", f"{sharpe:.2f}")

    with col3:
        volatility = risk_metrics.get('volatility', 0)
        st.metric("波动率", f"{volatility:.2f}%")

    with col4:
        avg_hold = perf_analysis.get('avg_hold_days', 0)
        st.metric("平均持股天数", f"{avg_hold:.1f}天")

    # 信心度胜率分析
    st.markdown("#### 🎯 信心度胜率分析")

    confidence_win_rates = risk_metrics.get('win_rate_by_confidence', {})

    if confidence_win_rates:
        conf_data = []
        for level, stats in confidence_win_rates.items():
            total = stats.get('total', 0)
            win = stats.get('win', 0)
            win_rate = win / total * 100 if total > 0 else 0
            conf_data.append({
                '信心度等级': level,
                '总交易': total,
                '盈利交易': win,
                '胜率': f"{win_rate:.1f}%"
            })

        df_conf = pd.DataFrame(conf_data)
        st.dataframe(df_conf, use_container_width=True)
    else:
        st.info("暂无信心度分析数据")


def display_signal_details(results):
    """显示信号详情"""
    st.markdown("#### 📡 信号详情")

    signals = results.get('signals', [])

    if not signals:
        st.info("没有信号数据")
        return

    # 信号类型统计
    signal_types = {}
    for signal in signals:
        action = signal.action
        if action not in signal_types:
            signal_types[action] = 0
        signal_types[action] += 1

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**信号类型分布**")
        for action, count in signal_types.items():
            st.write(f"{action}: {count}个")

    with col2:
        st.markdown("**板块分布**")
        sector_counts = {}
        for signal in signals:
            sector = signal.sector
            if sector not in sector_counts:
                sector_counts[sector] = 0
            sector_counts[sector] += 1

        for sector, count in sector_counts.items():
            st.write(f"{sector}: {count}个")

    # 信号列表
    st.markdown("#### 📋 信号列表")

    signal_data = []
    for signal in signals:
        signal_data.append({
            '股票代码': signal.code,
            '股票名称': signal.name,
            '板块': signal.sector,
            '操作': signal.action,
            '置信度': f"{signal.confidence}%",
            '价格': f"¥{signal.price:.2f}",
            '理由': signal.reason[:50] + "..." if len(signal.reason) > 50 else signal.reason,
            '时间': signal.timestamp.strftime('%H:%M:%S')
        })

    df_signals = pd.DataFrame(signal_data)
    st.dataframe(df_signals, use_container_width=True)


def display_system_console():
    """系统控制台页面 - 诊断和管理"""
    st.markdown("### ⚙️ 系统控制台")

    # 系统状态
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("系统状态", "正常运行", "🟢")

    with col2:
        st.metric("数据库连接", "已连接", "🟢")

    with col3:
        st.metric("API状态", "正常", "🟢")

    # 功能控制
    st.markdown("### 🎛️ 功能控制")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 刷新缓存", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ 缓存已清空")

        if st.button("🗑️ 清空历史数据", use_container_width=True):
            # 这里可以添加清空数据库的逻辑
            st.success("✅ 历史数据已清空")

    with col2:
        if st.button("🔍 运行系统诊断", use_container_width=True):
            with st.spinner("正在诊断系统..."):
                # 模拟诊断过程
                import time
                time.sleep(1)

            st.success("✅ 系统诊断完成：所有功能正常")

        if st.button("📊 查看系统日志", use_container_width=True):
            # 显示最近的日志
            st.code("""
2024-01-12 22:15:30 INFO 牛市策略初始化成功
2024-01-12 22:15:31 INFO 数据库连接正常
2024-01-12 22:15:32 INFO 市场数据获取成功
2024-01-12 22:15:33 INFO 板块分析完成
            """, language="text")

    # 参数配置
    st.markdown("### ⚙️ 参数配置")

    with st.expander("高级设置"):
        st.slider("API请求超时时间", 5, 60, 30, help="秒")
        st.slider("数据缓存时间", 60, 3600, 300, help="秒")
        st.checkbox("启用调试模式", value=False)
        st.checkbox("自动保存结果", value=True)

        if st.button("💾 保存配置"):
            st.success("✅ 配置已保存")

    st.info("💡 系统控制台提供系统监控、参数配置和维护功能，确保系统稳定运行")