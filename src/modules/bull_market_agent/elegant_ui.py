# 🐂 牛市选股优雅UI
# 基于新架构的现代化界面

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List

# 导入新架构
from .core import (
    BullMarketAnalyzer, AnalysisConfig, TradingSignal,
    BacktestResult, SignalAction, RiskLevel
)
from .strategies import StrategyFactory
from .infrastructure import (
    AKShareMarketDataProvider,
    SQLitePortfolioRepository,
    ConsoleSignalNotifier
)


class ElegantBullMarketUI:
    """优雅的牛市选股UI"""

    def __init__(self):
        self._setup_page()
        self._init_analyzer()

    def _setup_page(self):
        """设置页面样式"""
        st.set_page_config(
            page_title="🐂 牛市猎手 - 优雅版",
            page_icon="🐂",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # 优雅的CSS样式
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .main-header h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .main-header p {
            color: rgba(255,255,255,0.9);
            font-size: 1.1rem;
            margin: 0;
        }
        .feature-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 20px;
            color: white;
            text-align: center;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        </style>
        """, unsafe_allow_html=True)

    def _init_analyzer(self):
        """初始化分析器"""
        if 'analyzer' not in st.session_state:
            config = AnalysisConfig(
                sectors=["BK0917"],
                confidence_threshold=80.0,
                enable_parallel=True,
                max_workers=4
            )

            strategies = StrategyFactory.create_all_strategies()

            data_provider = AKShareMarketDataProvider()
            portfolio_repo = SQLitePortfolioRepository()
            notifier = ConsoleSignalNotifier()

            st.session_state.analyzer = BullMarketAnalyzer(
                config=config,
                data_provider=data_provider,
                portfolio_repo=portfolio_repo,
                notifier=notifier,
                strategies=strategies
            )

    def render(self):
        """渲染主界面"""
        # 头部
        st.markdown("""
        <div class="main-header">
            <h1>🐂 牛市猎手</h1>
            <p>优雅架构 · 智能分析 · 精准捕猎</p>
        </div>
        """, unsafe_allow_html=True)

        # 导航
        self._render_navigation()

        # 页面内容
        self._render_page_content()

    def _render_navigation(self):
        """渲染导航"""
        st.markdown("### 🎯 功能导航")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🎯 智能扫描", use_container_width=True, type="primary"):
                st.session_state.page = "scan"

        with col2:
            if st.button("📊 回测分析", use_container_width=True):
                st.session_state.page = "backtest"

        with col3:
            if st.button("📈 策略配置", use_container_width=True):
                st.session_state.page = "config"

        with col4:
            if st.button("ℹ️ 关于", use_container_width=True):
                st.session_state.page = "about"

        # 默认页面
        if 'page' not in st.session_state:
            st.session_state.page = "scan"

    def _render_page_content(self):
        """渲染页面内容"""
        page = st.session_state.page

        if page == "scan":
            self._render_scan_page()
        elif page == "backtest":
            self._render_backtest_page()
        elif page == "config":
            self._render_config_page()
        elif page == "about":
            self._render_about_page()

    def _render_scan_page(self):
        """渲染扫描页面"""
        st.markdown("### 🎯 智能市场扫描")

        # 配置参数
        col1, col2, col3 = st.columns(3)

        with col1:
            sectors = st.multiselect(
                "选择板块",
                ["BK0917", "BK0480", "BK0916"],
                default=["BK0917"],
                format_func=lambda x: {
                    "BK0917": "半导体概念",
                    "BK0480": "航天航空",
                    "BK0916": "CPO概念"
                }.get(x, x)
            )

        with col2:
            confidence = st.slider("置信度阈值", 50, 95, 80)

        with col3:
            enable_parallel = st.checkbox("启用并行处理", value=True)

        # 执行扫描
        if st.button("🚀 开始扫描", type="primary"):
            if not sectors:
                st.error("请至少选择一个板块")
                return

            try:
                with st.spinner("正在智能扫描市场..."):
                    # 更新配置
                    analyzer = st.session_state.analyzer
                    analyzer.config.sectors = sectors
                    analyzer.config.confidence_threshold = confidence
                    analyzer.config.enable_parallel = enable_parallel

                    # 执行扫描
                    signals = analyzer.scan_market()

                    # 保存结果
                    st.session_state.scan_results = signals
                    st.session_state.scan_timestamp = datetime.now()

                st.success(f"扫描完成！发现 {len(signals)} 个交易机会")

                # 显示结果
                self._display_scan_results(signals)

            except Exception as e:
                st.error(f"扫描失败: {e}")

        # 显示历史结果
        if 'scan_results' in st.session_state:
            self._display_scan_results(st.session_state.scan_results)

    def _display_scan_results(self, signals: List[TradingSignal]):
        """显示扫描结果"""
        if not signals:
            st.info("未发现符合条件的交易信号")
            return

        # 统计信息
        col1, col2, col3, col4 = st.columns(4)

        buy_signals = [s for s in signals if s.action == SignalAction.BUY]
        sell_signals = [s for s in signals if s.action == SignalAction.SELL]
        hold_signals = [s for s in signals if s.action == SignalAction.HOLD]

        with col1:
            st.metric("买入信号", len(buy_signals))
        with col2:
            st.metric("卖出信号", len(sell_signals))
        with col3:
            st.metric("持有信号", len(hold_signals))
        with col4:
            avg_confidence = sum(s.confidence for s in signals) / len(signals)
            st.metric("平均置信度", f"{avg_confidence:.1f}%")

        # 信号列表
        st.markdown("### 📋 交易信号详情")

        for signal in signals:
            with st.expander(f"{signal.name}({signal.symbol}) - {signal.action.value} - 置信度:{signal.confidence}%"):

                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**股票信息**")
                    st.write(f"代码: {signal.symbol}")
                    st.write(f"名称: {signal.name}")
                    st.write(f"板块: {signal.sector}")
                    st.write(f"价格: ¥{signal.price:.2f}")

                with col2:
                    st.write(f"**信号分析**")
                    st.write(f"操作: {signal.action.value}")
                    st.write(f"置信度: {signal.confidence}%")
                    st.write(f"风险等级: {signal.risk_level.value}")
                    st.write(f"仓位占比: {signal.position_size_pct}")

                st.write(f"**信号理由**: {signal.reason}")

                if signal.detailed_reasons:
                    st.write("**详细分析**:")
                    for reason in signal.detailed_reasons:
                        st.write(f"• {reason}")

                if signal.expected_profit_scenarios:
                    st.write("**预期收益**:")
                    scenarios = signal.expected_profit_scenarios
                    st.write(f"• 乐观: {scenarios.get('乐观', '未知')}")
                    st.write(f"• 中性: {scenarios.get('中性', '未知')}")
                    st.write(f"• 保守: {scenarios.get('保守', '未知')}")

    def _render_backtest_page(self):
        """渲染回测页面"""
        st.markdown("### 📊 详细回测分析")

        # 回测参数
        col1, col2, col3 = st.columns(3)

        with col1:
            start_date = st.date_input(
                "开始日期",
                value=datetime.now().date() - timedelta(days=30)
            )

        with col2:
            end_date = st.date_input(
                "结束日期",
                value=datetime.now().date()
            )

        with col3:
            initial_capital = st.number_input(
                "初始资金(万)",
                min_value=1, max_value=1000,
                value=10
            )

        # 执行回测
        if st.button("🔬 执行详细回测", type="primary"):
            try:
                with st.spinner("正在执行详细回测分析..."):
                    analyzer = st.session_state.analyzer

                    # 执行回测
                    start_dt = datetime.combine(start_date, datetime.min.time())
                    end_dt = datetime.combine(end_date, datetime.min.time())

                    backtest_result = analyzer.run_backtest(start_dt, end_dt)

                    # 保存结果
                    st.session_state.backtest_result = backtest_result
                    st.session_state.backtest_timestamp = datetime.now()

                st.success("回测完成！查看详细分析结果")

                # 显示结果
                self._display_backtest_results(backtest_result)

            except Exception as e:
                st.error(f"回测失败: {e}")

        # 显示历史结果
        if 'backtest_result' in st.session_state:
            self._display_backtest_results(st.session_state.backtest_result)

    def _display_backtest_results(self, result: BacktestResult):
        """显示回测结果"""
        # 总体概览
        st.markdown("### 🎯 回测概览")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("总收益率", f"{result.total_return_pct:.2f}%",
                     delta=f"{result.total_return_pct:.2f}%")

        with col2:
            st.metric("胜率", f"{result.risk_metrics.win_rate:.1f}%")

        with col3:
            st.metric("最大回撤", f"{result.risk_metrics.max_drawdown:.2f}%")

        with col4:
            st.metric("夏普比率", f"{result.risk_metrics.sharpe_ratio:.2f}")

        # 详细分析标签页
        tab1, tab2, tab3 = st.tabs(["📈 交易记录", "📊 每日详情", "⚠️ 风险分析"])

        with tab1:
            self._display_trade_records(result)

        with tab2:
            self._display_daily_details(result)

        with tab3:
            self._display_risk_analysis(result)

    def _display_trade_records(self, result: BacktestResult):
        """显示交易记录"""
        st.markdown("#### 💼 交易记录详情")

        trade_records = result.trade_records

        if not trade_records:
            st.info("没有交易记录")
            return

        # 转换为DataFrame便于显示
        df = pd.DataFrame([{
            '日期': tr.timestamp.strftime('%Y-%m-%d'),
            '股票': f"{tr.name}({tr.symbol})",
            '操作': tr.action.value,
            '数量': tr.quantity,
            '价格': f"¥{tr.price:.2f}",
            '金额': f"¥{tr.amount:,.0f}",
            '盈亏': f"¥{tr.profit_loss:,.0f}" if tr.profit_loss else "-",
            '收益率': f"{tr.profit_loss_pct:+.1f}%" if tr.profit_loss_pct else "-",
            '置信度': f"{tr.confidence}%",
            '持有天数': tr.hold_days
        } for tr in trade_records])

        st.dataframe(df, use_container_width=True)

        # 交易统计
        profitable_trades = [t for t in trade_records if t.profit_loss and t.profit_loss > 0]
        losing_trades = [t for t in trade_records if t.profit_loss and t.profit_loss < 0]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("盈利交易", len(profitable_trades))

        with col2:
            st.metric("亏损交易", len(losing_trades))

        with col3:
            total_return = sum(t.profit_loss for t in trade_records if t.profit_loss)
            st.metric("总盈亏", f"¥{total_return:,.0f}")

    def _display_daily_details(self, result: BacktestResult):
        """显示每日详情"""
        st.markdown("#### 📅 每日表现详情")

        daily_results = result.daily_results

        if not daily_results:
            st.info("没有每日详情数据")
            return

        # 资金曲线图
        capital_values = [100000.0]  # 初始资金
        dates = ['初始']

        for day in daily_results:
            capital_values.append(day['capital_after'])
            dates.append(day['date'])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=capital_values,
            mode='lines+markers',
            name='资金曲线',
            line=dict(color='#667eea', width=3)
        ))

        fig.update_layout(
            title="回测期间资金变化曲线",
            xaxis_title="日期",
            yaxis_title="资金(元)",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # 每日统计表格
        daily_data = []
        for day in daily_results:
            daily_data.append({
                '日期': day['date'],
                '信号数量': day['signals_count'],
                '执行交易': day['trades_executed'],
                '期初资金': f"¥{day['capital_before']:,.0f}",
                '期末资金': f"¥{day['capital_after']:,.0f}",
                '资金变化': f"¥{(day['capital_after'] - day['capital_before']):+,0f}",
                '持仓数量': day['positions_count']
            })

        df_daily = pd.DataFrame(daily_data)
        st.dataframe(df_daily, use_container_width=True)

    def _display_risk_analysis(self, result: BacktestResult):
        """显示风险分析"""
        st.markdown("#### ⚠️ 风险分析")

        risk = result.risk_metrics
        perf = result.performance_analysis

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("最大回撤", f"{risk.max_drawdown:.2f}%")
        with col2:
            st.metric("夏普比率", f"{risk.sharpe_ratio:.2f}")
        with col3:
            st.metric("波动率", f"{risk.volatility:.2f}%")
        with col4:
            st.metric("平均持股天数", f"{perf.get('avg_hold_days', 0):.1f}天")

        # 性能指标
        st.markdown("#### 📊 性能指标")

        perf_data = {
            '指标': ['总收益率', '年化收益率', '胜率', '盈亏比', '卡尔玛比率', '索提诺比率'],
            '数值': [
                f"{perf.get('total_return_pct', 0):.2f}%",
                f"{result.annualized_return:.2f}%" if hasattr(result, 'annualized_return') else "0.00%",
                f"{risk.win_rate:.1f}%",
                f"{risk.profit_loss_ratio:.2f}",
                f"{risk.calmar_ratio:.2f}",
                f"{risk.sortino_ratio:.2f}"
            ]
        }

        df_perf = pd.DataFrame(perf_data)
        st.dataframe(df_perf, use_container_width=True)

    def _render_config_page(self):
        """渲染配置页面"""
        st.markdown("### ⚙️ 策略配置")

        st.info("配置功能正在开发中，请使用环境变量进行配置")

        # 显示当前配置
        analyzer = st.session_state.analyzer
        config = analyzer.config

        st.markdown("#### 当前配置")

        config_data = {
            '参数': ['监控板块', '置信度阈值', '最大仓位', '启用并行', '最大线程数', '分析超时'],
            '值': [
                ', '.join(config.sectors),
                f"{config.confidence_threshold}%",
                f"{config.max_position_size * 100:.0f}%",
                '是' if config.enable_parallel else '否',
                str(config.max_workers),
                f"{config.analysis_timeout}秒"
            ]
        }

        df_config = pd.DataFrame(config_data)
        st.dataframe(df_config, use_container_width=True)

    def _render_about_page(self):
        """渲染关于页面"""
        st.markdown("### ℹ️ 关于牛市猎手")

        st.markdown("""
        #### 🏗️ 优雅架构
        基于领域驱动设计（DDD）和SOLID原则构建的现代化量化交易系统。

        #### 🎯 核心特性
        - ✅ **多策略并行**：T+1时空折叠、动量、成交量、情绪等多策略融合
        - ✅ **智能缓存**：多层次缓存系统，提升响应速度
        - ✅ **风险控制**：完善的仓位管理和风险指标体系
        - ✅ **详细回测**：完整的交易记录和人工验证功能

        #### 📊 技术栈
        - **架构模式**：整洁架构、依赖倒置
        - **设计模式**：策略模式、工厂模式、模板方法
        - **数据源**：AKShare实时数据
        - **存储**：SQLite本地数据库
        - **界面**：Streamlit现代化UI

        #### 🎨 代码审美
        - 优雅的类型注解
        - 完整的文档字符串
        - 清晰的包结构
        - 高度可扩展性
        """)

        st.markdown("---")
        st.markdown("**🚀 让量化交易变得优雅而简单**")


# 工厂函数
def create_elegant_ui() -> ElegantBullMarketUI:
    """创建优雅的UI实例"""
    return ElegantBullMarketUI()


# 便捷启动函数
def run_elegant_ui():
    """启动优雅UI"""
    ui = create_elegant_ui()
    ui.render()


if __name__ == "__main__":
    run_elegant_ui()