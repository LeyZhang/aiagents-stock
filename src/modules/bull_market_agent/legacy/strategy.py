"""
策略核心 - 优雅解耦版
复用AKShare + 优雅日志 + 解耦接口
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import asyncio
import concurrent.futures
import threading
from functools import lru_cache
import time
from concurrent.futures import ThreadPoolExecutor

from src.core.logger import get_logger
from src.core.config_manager import config_manager

logger = get_logger('bull_strategy')

# 缓存存储
_cache_store = {}
_cache_lock = threading.Lock()

def cached_api_call(cache_key: str, ttl: int = 300):
    """API调用缓存装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with _cache_lock:
                if cache_key in _cache_store:
                    cached_data, timestamp = _cache_store[cache_key]
                    if time.time() - timestamp < ttl:
                        logger.debug(f"缓存命中: {cache_key}")
                        return cached_data

            result = func(*args, **kwargs)

            with _cache_lock:
                _cache_store[cache_key] = (result, time.time())

            return result
        return wrapper
    return decorator


@dataclass
class Signal:
    """交易信号数据类"""
    code: str              # 股票代码
    name: str              # 股票名称
    sector: str            # 板块
    action: str            # 加仓/减仓/空仓
    confidence: float       # 置信度 0-100
    price: float           # 当前价格
    reason: str            # 理由
    timestamp: datetime


class BullMarketStrategy:
    """牛市选股策略 - T+1时空折叠策略"""

    # T+1交易时间分割
    TIME_SLOTS = {
        'early_morning': ('09:15', '09:30'),  # 早盘竞价：只卖不买
        'morning_session': ('09:30', '11:30'),  # 上午：持仓做T，谨慎开仓
        'afternoon_session': ('13:00', '14:30'),  # 下午：持仓做T，禁止开新仓
        'late_afternoon': ('14:30', '15:00'),  # 尾盘：黄金买入时段
    }

    # T+1核心配置
    DEFAULT_SECTORS = ['BK0917', 'BK0480', 'BK0916']  # 板块代码
    DEFAULT_INTERVAL = 10  # 分钟
    DEFAULT_CONFIDENCE_THRESHOLD = 80
    T_PLUS_ONE_MODE = True  # 启用T+1优化模式
    DEFAULT_BATCH_SIZE = 30  # 默认批处理大小，避免内存溢出

    # 加速配置
    MAX_WORKERS = 8  # 最大并行线程数
    CACHE_TTL = 300  # 缓存有效期（秒）
    BULK_API_SIZE = 10  # 批量API调用大小

    def __init__(self,
                 sectors: Optional[List[str]] = None,  # 可以是板块名称或板块代码
                 interval_minutes: Optional[int] = None,
                 confidence_threshold: Optional[float] = None,
                 debug_mode: bool = False,
                 backtest_date: Optional[datetime] = None,
                 t_plus_one_mode: Optional[bool] = None,
                 batch_size: Optional[int] = None,
                 enable_parallel: bool = True,  # 启用并行处理
                 max_workers: Optional[int] = None,  # 最大并行线程数
                 analysis_timeout: Optional[int] = None):  # 单股票分析超时
        """
        优雅初始化 - 支持配置覆盖

        Args:
            sectors: 监控板块列表
            interval_minutes: 扫描间隔（分钟）
            confidence_threshold: 置信度阈值
            debug_mode: 调试模式（使用历史数据）
            backtest_date: 回测日期（None=实时模式）
        """
        # 配置参数（优雅降级）
        self.sectors = sectors or self.DEFAULT_SECTORS
        self.interval_minutes = interval_minutes or self.DEFAULT_INTERVAL
        self.confidence_threshold = confidence_threshold or self.DEFAULT_CONFIDENCE_THRESHOLD
        self.debug_mode = debug_mode
        self.backtest_date = backtest_date
        self.current_date = backtest_date or datetime.now()
        self.t_plus_one_mode = t_plus_one_mode if t_plus_one_mode is not None else self.T_PLUS_ONE_MODE
        self.batch_size = batch_size or self.DEFAULT_BATCH_SIZE

        # 加速配置
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers or self.MAX_WORKERS
        self.analysis_timeout = analysis_timeout or 15  # 默认15秒超时

        # T+1持仓状态（模拟持仓管理）
        self.positions = {}  # 模拟持仓：{stock_code: {'shares': N, 'cost': price, 'date': datetime}}
        self.available_to_sell = {}  # 可售股数：T+1限制

        logger.info("🐂 牛市策略初始化")
        logger.info(f"    模式: {'调试/回测' if debug_mode else '实时'}")
        logger.info(f"    日期: {self.current_date.strftime('%Y-%m-%d') if backtest_date else '实时'}")
        logger.info(f"    T+1模式: {'启用' if self.t_plus_one_mode else '禁用'}")
        logger.info(f"    监控板块: {self.sectors}")
        logger.info(f"    扫描间隔: {self.interval_minutes}分钟")
        logger.info(f"    置信度阈值: {self.confidence_threshold}%")
        logger.info(f"    扫描间隔: {self.interval_minutes}分钟")
        logger.info(f"    置信度阈值: {self.confidence_threshold}%")

    def scan(self) -> List[Signal]:
        """
        智能扫描 - 根据配置选择串行/并行处理

        Returns:
            信号列表
        """
        logger.info(f"🔍 开始扫描... (并行模式: {self.enable_parallel})")
        start_time = datetime.now()

        try:
            if self.enable_parallel:
                signals = self._execute_scan_parallel()
            else:
                signals = self._execute_scan()

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ 扫描完成: {len(signals)}条信号, 耗时{elapsed:.1f}秒")

            return signals

        except Exception as e:
            logger.error(f"❌ 扫描失败: {type(e).__name__}: {e}", exc_info=True)
            return []

    def _execute_scan(self) -> List[Signal]:
        """执行扫描逻辑（串行模式）"""
        signals = []

        # 串行扫描各板块
        for sector in self.sectors:
            try:
                sector_signals = self._scan_sector(sector)
                signals.extend(sector_signals)
            except Exception as e:
                logger.error(f"板块 {sector} 扫描失败: {e}", exc_info=True)
                continue

        return signals

    def _execute_scan_parallel(self) -> List[Signal]:
        """并行执行扫描逻辑（多线程加速）"""
        signals = []

        # 并行扫描各板块（使用线程池）
        with ThreadPoolExecutor(max_workers=min(len(self.sectors), 4)) as executor:
            futures = {
                executor.submit(self._scan_sector_parallel, sector): sector
                for sector in self.sectors
            }

            for future in concurrent.futures.as_completed(futures):
                sector = futures[future]
                try:
                    sector_signals = future.result()
                    signals.extend(sector_signals)
                except Exception as e:
                    logger.error(f"板块 {sector} 并行扫描失败: {e}", exc_info=True)
                    continue

        return signals

    def _scan_sector(self, sector: str) -> List[Signal]:
        """
        扫描单个板块（优雅降级 + 批处理优化）
        """
        logger.debug(f"扫描板块: {sector}")

        try:
            # 1. 获取数据（优雅降级）
            df = self._get_sector_stocks(sector)
            if df is None or df.empty:
                logger.warning(f"板块 {sector} 无数据")
                return []

            # 2. 批处理分析（控制内存使用）
            signals = []
            batch_size = getattr(self, 'batch_size', self.DEFAULT_BATCH_SIZE)

            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i + batch_size]
                logger.debug(f"  处理批次 {i//batch_size + 1}/{(len(df) + batch_size - 1)//batch_size}")

                for _, row in batch_df.iterrows():
                    try:
                        signal = self._analyze_stock(row, sector)
                        if signal:
                            signals.append(signal)
                    except Exception as e:
                        logger.warning(f"分析股票 {row.get('代码', 'unknown')} 失败: {e}")
                        continue

                # 批次间短暂休息，避免API限流
                import time
                time.sleep(0.1)

            logger.debug(f"  板块 {sector}: 产生 {len(signals)} 条信号")
            return signals

        except Exception as e:
            logger.error(f"板块 {sector} 分析异常: {e}", exc_info=True)
            return []

    def _scan_sector_parallel(self, sector: str) -> List[Signal]:
        """
        并行扫描单个板块（多线程加速）
        """
        logger.debug(f"并行扫描板块: {sector}")

        try:
            # 1. 获取数据（优雅降级）
            df = self._get_sector_stocks(sector)
            if df is None or df.empty:
                logger.warning(f"板块 {sector} 无数据")
                return []

            # 2. 并行分析股票（多线程）
            signals = []
            stock_rows = [(row, sector) for _, row in df.iterrows()]

            # 分批并行处理
            batch_size = getattr(self, 'batch_size', self.DEFAULT_BATCH_SIZE)

            with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                for i in range(0, len(stock_rows), batch_size):
                    batch = stock_rows[i:i + batch_size]
                    logger.debug(f"  并行处理批次 {i//batch_size + 1}/{(len(stock_rows) + batch_size - 1)//batch_size}")

                    # 提交批次任务
                    futures = [
                        executor.submit(self._analyze_stock_safe, row, sector)
                        for row, sector in batch
                    ]

                    # 收集结果
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            signal = future.result()
                            if signal:
                                signals.append(signal)
                        except Exception as e:
                            logger.warning(f"批次分析失败: {e}")
                            continue

                    # 批次间休息，避免API限流
                    time.sleep(0.05)

            logger.debug(f"  板块 {sector}: 并行产生 {len(signals)} 条信号")
            return signals

        except Exception as e:
            logger.error(f"板块 {sector} 并行分析异常: {e}", exc_info=True)
            return []

    @cached_api_call("sector_stocks_{}", ttl=300)  # 5分钟缓存
    def _get_sector_stocks(self, sector: str) -> Optional[pd.DataFrame]:
        """
        获取板块成分股（优雅降级 + 缓存优化）
        """
        if self.debug_mode:
            # 调试模式：优雅模拟
            logger.debug(f"  调试模式: 使用优雅模拟数据")
            return pd.DataFrame([
                {'代码': '688261', '名称': '东微半导', '最新价': 94.99, '涨跌幅': 10.02},
                {'代码': '300487', '名称': '蓝晓科技', '最新价': 70.72, '涨跌幅': 5.68},
            ])

        # 实时模式：优雅调用AKShare
        try:
            # 获取板块列表（也需要缓存）
            sectors_df = self._get_sector_list()

            # 判断输入是板块代码还是板块名称
            sector_code = None
            sector_name = None

            # 如果输入是BK开头，认为是板块代码
            if sector.startswith('BK') and len(sector) == 6:
                sector_code = sector
                # 查找对应的板块名称
                sector_row = sectors_df[sectors_df['板块代码'] == sector_code]
                if len(sector_row) > 0:
                    sector_name = sector_row.iloc[0]['板块名称']
            else:
                # 处理板块名称映射（用户输入 -> 实际板块名称）
                sector_mapping = {
                    '半导体': '半导体概念',
                    '商业航天': '航天航空',
                    'CPO光模块': 'CPO概念'
                }
                actual_sector = sector_mapping.get(sector, sector)
                sector_row = sectors_df[sectors_df['板块名称'] == actual_sector]

                if len(sector_row) > 0:
                    sector_code = sector_row.iloc[0]['板块代码']
                    sector_name = sector_row.iloc[0]['板块名称']

            if not sector_code:
                logger.warning(f"未找到板块: {sector}")
                return None

            logger.info(f"获取板块 {sector} -> {sector_name}({sector_code}) 的成分股")

            # 获取板块成分股
            stocks_df = ak.stock_board_concept_cons_em(symbol=sector_code)
            logger.info(f"成功获取 {len(stocks_df)} 只股票")
            return stocks_df

        except Exception as e:
            logger.error(f"AKShare获取{sector}失败: {e}", exc_info=True)
            return None

    @cached_api_call("sector_list", ttl=600)  # 10分钟缓存板块列表
    def _get_sector_list(self) -> pd.DataFrame:
        """获取板块列表（缓存优化）"""
        return ak.stock_board_concept_name_em()

    @cached_api_call("market_sentiment", ttl=60)  # 1分钟缓存
    def _check_market_sentiment(self) -> float:
        """
        宏观观察员：检查市场情绪评分 (0-100)
        决定能不能出手，出多少仓位
        """
        try:
            # 获取市场数据
            market_data = ak.stock_zh_a_spot_em()
            limit_up_count = len(market_data[market_data['涨跌幅'] >= 9.8])  # 涨停股数
            total_count = len(market_data)
            up_count = len(market_data[market_data['涨跌幅'] > 0])

            # 计算情绪指标
            limit_up_ratio = limit_up_count / total_count if total_count > 0 else 0
            up_down_ratio = up_count / (total_count - up_count) if total_count > up_count else 2.0

            # 基础分数
            score = 50

            # 炸板率过高，说明资金分歧大
            if limit_up_ratio > 0.35:
                score -= 20

            # 整体上涨家数占比
            if up_down_ratio > 1.5:
                score += 15
            elif up_down_ratio < 0.8:
                score -= 15

            # 成交量放大（相对昨日）
            # 这里简化处理，实际应该比较昨日同时段
            avg_volume = market_data['成交量'].mean()
            if avg_volume > 1000000:  # 假设成交活跃
                score += 10

            return max(0, min(100, score))

        except Exception as e:
            logger.warning(f"检查市场情绪失败: {e}")
            return 50  # 默认中性

    @cached_api_call("stock_hist_{}", ttl=1800)  # 30分钟缓存历史数据
    def _get_stock_history(self, stock_code: str) -> Optional[pd.DataFrame]:
        """获取股票历史数据（缓存优化）"""
        try:
            hist_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date="20240101")
            return hist_data if len(hist_data) >= 10 else None
        except Exception as e:
            logger.warning(f"获取历史数据失败 {stock_code}: {e}")
            return None

    def _analyze_stock_profile(self, stock_code: str) -> str:
        """
        股性分析师：分析个股性格标签
        返回: '股性活', '跟风狗', '独立逻辑', '未知'
        """
        try:
            # 使用缓存的历史数据
            hist_data = self._get_stock_history(stock_code)
            if hist_data is None:
                return '未知'

            # 分析股性特征
            changes = hist_data['涨跌幅']

            # 计算波动特征
            volatility = changes.std()
            avg_change = changes.mean()

            # 长上影线频率（股性活的标志）
            shadow_count = 0
            for _, row in hist_data.iterrows():
                high = row['最高']
                low = row['最低']
                close = row['收盘']
                open_price = row['开盘']

                # 计算上影线长度
                body_high = max(open_price, close)
                upper_shadow = high - body_high
                body_length = abs(close - open_price)

                if body_length > 0 and upper_shadow > body_length * 0.5:
                    shadow_count += 1

            shadow_ratio = shadow_count / len(hist_data)

            # 判断股性
            if shadow_ratio > 0.3 and volatility > 3.0:
                return '股性活'  # 经常出现长上影线，弹性好
            elif avg_change < 0.5 and volatility < 2.0:
                return '跟风狗'  # 跟随大盘，无独立走势
            elif abs(avg_change) > 1.0 and volatility > 2.5:
                return '独立逻辑'  # 有自己的节奏
            else:
                return '稳健型'  # 相对稳定

        except Exception as e:
            logger.warning(f"分析股性失败 {stock_code}: {e}")
            return '未知'

    def _analyze_ignition_potential(self, row: pd.Series, market_sentiment: float) -> Dict:
        """
        盘口狙击手：分析起爆潜力
        在涨幅<2%时判断是否有起爆潜力
        """
        code = row['代码']
        price = row.get('最新价', 0)
        change_pct = row.get('涨跌幅', 0)
        volume = row.get('成交量', 0)
        vwap = row.get('成交均价', price)  # 成交均价

        result = {
            'signal': 'WAIT',
            'confidence': 0,
            'reason': ''
        }

        try:
            # 1. 均线支撑逻辑：股价运行在均价线上方
            price_above_vwap = price > vwap * 0.995  # 允许0.5%的误差
            if not price_above_vwap:
                return result

            # 2. 成交量放大：相对平均水平
            # 这里简化，实际应该获取历史均量
            volume_sufficient = volume > 50000  # 假设5万手为活跃
            if not volume_sufficient:
                return result

            # 3. 价格异动：即使涨幅不大，但有向上动能
            momentum_score = 0
            if change_pct > 0.5:
                momentum_score += 20
            if change_pct > 1.0:
                momentum_score += 30

            # 4. 市场环境加成
            market_bonus = market_sentiment - 50  # 中性为0

            # 综合评分
            total_score = momentum_score + market_bonus + 30  # 基础分30

            if total_score > 60:
                result['signal'] = 'READY_TO_IGNITE'
                result['confidence'] = min(95, total_score)
                result['reason'] = f'均价支撑+量能配合+市场环境良好 (涨幅{change_pct:.1f}%)'

        except Exception as e:
            logger.warning(f"分析起爆潜力失败 {code}: {e}")

        return result

    def _check_position_management(self, stock_code: str, current_change: float) -> Optional[Dict]:
        """
        动态持仓管家：检查是否需要调整仓位
        去弱留强逻辑
        """
        # 这里简化实现，实际应该连接持仓数据库
        # 返回格式: {'action': '加仓'/'减仓'/'清仓', 'confidence': 80, 'reason': '...'}

        # 示例逻辑：如果涨幅明显弱于预期，建议减仓
        if current_change < -2.0:
            return {
                'action': '减仓',
                'confidence': 75,
                'reason': f'涨幅偏弱 ({current_change:.1f}%)，控制风险'
            }

        # 如果涨幅不错但板块龙头更强，建议换股
        # 这里需要实现板块内比较逻辑

        return None

    def _get_sector_code(self, sector_name: str) -> Optional[str]:
        """根据板块名称获取板块代码"""
        try:
            sectors_df = ak.stock_board_concept_name_em()
            sector_row = sectors_df[sectors_df['板块名称'] == sector_name]
            if len(sector_row) > 0:
                return sector_row.iloc[0]['板块代码']

            # 如果在概念板块找不到，尝试行业板块
            sectors_df = ak.stock_board_industry_name_em()
            sector_row = sectors_df[sectors_df['板块名称'] == sector_name]
            if len(sector_row) > 0:
                return sector_row.iloc[0]['板块代码']

            return None
        except Exception as e:
            logger.error(f"获取板块代码失败 {sector_name}: {e}")
            return None

    def _get_sector_name(self, sector_code: str) -> Optional[str]:
        """根据板块代码获取板块名称"""
        try:
            # 先尝试概念板块
            sectors_df = ak.stock_board_concept_name_em()
            sector_row = sectors_df[sectors_df['板块代码'] == sector_code]
            if len(sector_row) > 0:
                return sector_row.iloc[0]['板块名称']

            # 再尝试行业板块
            sectors_df = ak.stock_board_industry_name_em()
            sector_row = sectors_df[sectors_df['板块代码'] == sector_code]
            if len(sector_row) > 0:
                return sector_row.iloc[0]['板块名称']

            return None
        except Exception as e:
            logger.error(f"获取板块名称失败 {sector_code}: {e}")
            return None

    def _analyze_stock_safe(self, row: pd.Series, sector: str) -> Optional[Signal]:
        """
        线程安全的股票分析（用于并行处理）
        """
        try:
            return self._analyze_stock(row, sector)
        except Exception as e:
            code = row.get('代码', 'unknown')
            logger.warning(f"股票 {code} 分析异常: {e}")
            return None

    def _analyze_stock(self, row: pd.Series, sector: str) -> Optional[Signal]:
        """
        T+1时空折叠策略：基于交易时段的智能分析
        核心逻辑：时间决定策略，T+1限制风险
        """
        code = row['代码']
        name = row['名称']
        price = row.get('最新价', 0)
        change_pct = row.get('涨跌幅', 0)
        volume = row.get('成交量', 0)

        try:
            # 并行模式下简化超时处理（避免signal冲突）
            timeout_seconds = getattr(self, 'analysis_timeout', 15)

            # === 回测模式：跳过时间限制 ===
            if self.backtest_date is not None:
                # 在回测模式下，使用尾盘策略（最宽松的买入条件）
                return self._late_afternoon_strategy(row, sector)

            # === T+1时间维度判断 ===
            current_time = datetime.now().time()
            time_slot = self._get_time_slot(current_time)

            # 根据交易时段执行不同策略
            if time_slot == 'early_morning':
                # 09:15-09:30：收割者模式，只卖不买
                return self._early_morning_strategy(code, name, price, change_pct, sector)

            elif time_slot in ['morning_session', 'afternoon_session']:
                # 09:30-14:30：观察员模式，持仓做T，谨慎开仓
                return self._intraday_trading_strategy(row, sector)

            elif time_slot == 'late_afternoon':
                # 14:30-15:00：狙击手模式，尾盘安全买入
                return self._late_afternoon_strategy(row, sector)

            else:
                # 非交易时间
                return None

        except Exception as e:
            logger.warning(f"股票 {code} 分析异常: {e}")
            return None

    def _get_time_slot(self, current_time) -> str:
        """根据当前时间确定交易时段"""
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

    def _early_morning_strategy(self, code: str, name: str, price: float,
                               change_pct: float, sector: str) -> Optional[Signal]:
        """
        早盘竞价策略：收割者模式
        处理昨日筹码，利用集合竞价和开盘冲高，坚决兑现利润或止损
        """
        # 检查是否有持仓（模拟）
        if code not in self.positions:
            return None  # 无持仓，不操作

        position = self.positions[code]

        # 竞价核按钮逻辑：昨日强势股，今日竞价低开
        if change_pct < -2.0 and position.get('is_strong', False):
            # 检查成交量是否稀疏（主力出货迹象）
            volume_ratio = self._check_volume_ratio(code)
            if volume_ratio < 0.5:  # 成交量萎缩
                return Signal(
                    code=code,
                    name=name,
                    sector=sector,
                    action='清仓止损',
                    confidence=90,
                    price=price,
                    reason='竞价低开+缩量，主力出货迹象，T+1无法纠错，立即清仓',
                    timestamp=datetime.now()
                )

        # 弱转强确认：昨日烂板，今日高开+爆量
        if change_pct > 1.0 and position.get('yesterday_weak', False):
            volume_ratio = self._check_volume_ratio(code)
            if volume_ratio > 1.5:  # 成交量放大
                return Signal(
                    code=code,
                    name=name,
                    sector=sector,
                    action='持有待涨',
                    confidence=80,
                    price=price,
                    reason='弱转强信号，高开+放量，主力意图明确',
                    timestamp=datetime.now()
                )

        return None

    def _intraday_trading_strategy(self, row: pd.Series, sector: str) -> Optional[Signal]:
        """
        盘中策略：趋势守门员模式
        默认状态：死拿（HOLD）- 只要趋势没坏就不操作
        做T是防御性武器，仅在特殊情况使用
        """
        code = row['代码']
        name = row['名称']
        price = row.get('最新价', 0)
        change_pct = row.get('涨跌幅', 0)

        # 只有持有该股票才能考虑操作
        if code not in self.positions:
            return None

        # 检查是否有可售股数（T+1限制）
        available_shares = self.available_to_sell.get(code, 0)
        if available_shares <= 0:
            return None

        # === 核心逻辑：判断趋势状态 ===
        trend_mode = self._check_trend_mode(code)

        if trend_mode == "DIAMOND_HANDS":
            # 主升浪：锁仓模式，禁用一切卖出
            # 除非出现极端情况（如重大利空），否则坚决持有
            logger.info(f"主升浪锁仓模式: {code} - 坚决持有")
            return Signal(
                code=code,
                name=name,
                sector=sector,
                action='坚决持有',
                confidence=95,
                price=price,
                reason='主升浪锁仓模式：缩量加速是持股最舒服的时候，别乱动',
                timestamp=datetime.now()
            )

        elif trend_mode == "ACTIVE_T":
            # 震荡整理：启用做T降低成本
            return self._defensive_t_trading(row, sector)

        elif trend_mode == "DEFENSIVE_SELL":
            # 高位滞涨：考虑减仓或清仓
            if change_pct > 5.0:  # 高位获利了结
                return Signal(
                    code=code,
                    name=name,
                    sector=sector,
                    action='高位减仓',
                    confidence=85,
                    price=price,
                    reason='高位滞涨模式：主力换手，利用高位减仓锁定利润',
                    timestamp=datetime.now()
                )

        # 默认：观望
        return None

    def _check_trend_mode(self, stock_code: str) -> str:
        """
        判断股票趋势状态：死拿还是做T
        返回: "DIAMOND_HANDS" | "ACTIVE_T" | "DEFENSIVE_SELL" | "WATCH"
        """
        try:
            # 获取最近数据（这里简化，实际应该从缓存或API获取）
            # 假设有获取股价和均线数据的方法

            # 模拟趋势判断逻辑
            # 实际实现需要：
            # 1. 获取5日均线和10日均线
            # 2. 计算均线斜率
            # 3. 分析K线形态（阳线占比）
            # 4. 检查成交量特征

            # 简化的判断逻辑（实际需要更复杂的技术分析）
            # 这里返回默认值，实际实现需要接入真实数据

            # 假设大多数情况是震荡，需要做T降低成本
            return "ACTIVE_T"

        except Exception as e:
            logger.warning(f"趋势判断失败 {stock_code}: {e}")
            return "WATCH"  # 无法判断时观望

    def _defensive_t_trading(self, row: pd.Series, sector: str) -> Optional[Signal]:
        """
        防御性做T：仅在被套或高位震荡时使用
        """
        code = row['代码']
        name = row['名称']
        price = row.get('最新价', 0)
        change_pct = row.get('涨跌幅', 0)

        position = self.positions.get(code, {})
        cost_price = position.get('cost', 0)
        current_profit = (price - cost_price) / cost_price * 100

        # 情况1：被套救援 - 亏损>5%，利用日内波动降低成本
        if current_profit < -5.0 and change_pct < -2.0:
            return Signal(
                code=code,
                name=name,
                sector=sector,
                action='被套救援',
                confidence=80,
                price=price,
                reason=f'被套{current_profit:.1f}%，利用日内低点做T降低成本',
                timestamp=datetime.now()
            )

        # 情况2：高位震荡 - 盈利>10%，利用波动锁定利润
        elif current_profit > 10.0 and change_pct > 3.0:
            return Signal(
                code=code,
                name=name,
                sector=sector,
                action='震荡减仓',
                confidence=75,
                price=price,
                reason=f'盈利{current_profit:.1f}%，高位震荡时减仓锁定利润',
                timestamp=datetime.now()
            )

        return None

    def _late_afternoon_strategy(self, row: pd.Series, sector: str) -> Optional[Signal]:
        """
        尾盘策略：黄金30分钟
        大盘走势已定，此时买入只需承担过夜风险，大大降低关灯吃面概率
        """
        code = row['代码']
        name = row['名称']
        price = row.get('最新价', 0)
        change_pct = row.get('涨跌幅', 0)

        # === 宏观观察员：检查大盘环境 ===
        market_sentiment = self._check_market_sentiment()
        if market_sentiment < 40:  # 市场情绪过差，避免买入
            return None

        # === 股性分析师：分析个股性格 ===
        stock_profile = self._analyze_stock_profile(code)
        if stock_profile in ['跟风狗', '未知']:  # 剔除跟风股
            return None

        # === 首阴反包潜伏模式 ===
        # 筛选：上升趋势中的热门股，今日回调（阴线），但尾盘横盘稳定
        if self._is_in_uptrend(code) and change_pct < -2.0:  # 今日阴线回调
            stability_score = self._check_late_stability(code)
            if stability_score > 80:  # 尾盘稳定性高
                return Signal(
                    code=code,
                    name=name,
                    sector=sector,
                    action='尾盘买入',
                    confidence=85,
                    price=price,
                    reason='首阴反包模式：上升趋势+今日回调+尾盘稳定，博弈明日补涨',
                    timestamp=datetime.now()
                )

        # === 抢筹监控模式 ===
        # 筛选：14:50后成交量突然放大，且大单向上扫货
        volume_surge = self._check_volume_surge(code)
        order_flow = self._analyze_order_flow(code)

        if volume_surge and order_flow.get('large_buy_ratio', 0) > 1.5:
            return Signal(
                code=code,
                name=name,
                sector=sector,
                action='尾盘抢筹',
                confidence=90,
                price=price,
                reason='抢筹模式：尾盘放量+大单扫货，主力和散户抢筹过夜',
                timestamp=datetime.now()
            )

        return None

    def _check_volume_ratio(self, code: str) -> float:
        """检查成交量相对比例（简化实现）"""
        # 这里应该比较当前成交量与历史均量
        return 1.0  # 默认正常

    def _check_bottom_divergence(self, code: str) -> bool:
        """检查底背离信号（简化实现）"""
        # 这里应该分析KDJ、RSI等指标的底背离
        return True  # 假设有信号

    def _is_in_uptrend(self, code: str) -> bool:
        """检查是否处于上升趋势（简化实现）"""
        # 这里应该检查5日线、10日线趋势
        return True  # 假设在上升趋势

    def _check_late_stability(self, code: str) -> float:
        """检查尾盘稳定性评分（简化实现）"""
        # 这里应该分析14:00-15:00的波动率
        return 85.0  # 假设稳定性良好

    def _check_volume_surge(self, code: str) -> bool:
        """检查成交量是否突然放大（简化实现）"""
        # 这里应该比较最近几分钟的成交量
        return False  # 假设无明显放量

    def _analyze_order_flow(self, code: str) -> Dict:
        """分析大单流向（简化实现）"""
        # 这里应该分析Level-2数据
        return {'large_buy_ratio': 1.2}  # 假设大单买入略多

        # === 股性分析师：分析个股性格 ===
        stock_profile = self._analyze_stock_profile(code)
        if stock_profile == '跟风狗':  # 坚决剔除跟风股
            return None

        # === 盘口狙击手：寻找起爆点 ===
        # 不再等待3%，只要形态好+主力在，0.5%就可以上
        ignition_potential = self._analyze_ignition_potential(row, market_sentiment)

        if ignition_potential['signal'] == 'READY_TO_IGNITE':
            confidence = ignition_potential['confidence']
            reason = ignition_potential['reason']

            # 根据市场环境调整仓位建议
            action = '轻仓试水' if market_sentiment < 70 else '加仓'

            return Signal(
                code=code,
                name=name,
                sector=sector,
                action=action,
                confidence=confidence,
                price=price,
                reason=reason,
                timestamp=datetime.now()
            )

        # === 动态持仓管家：去弱留强 ===
        # 如果已经在持仓中，检查是否需要调整
        if hasattr(self, '_check_position_management'):
            position_signal = self._check_position_management(code, change_pct)
            if position_signal:
                return Signal(
                    code=code,
                    name=name,
                    sector=sector,
                    action=position_signal['action'],
                    confidence=position_signal['confidence'],
                    price=price,
                    reason=position_signal['reason'],
                    timestamp=datetime.now()
                )

        return None

    def get_config_summary(self) -> Dict:
        """获取配置摘要（优雅展示）"""
        return {
            'sectors': self.sectors,
            'interval_minutes': self.interval_minutes,
            'confidence_threshold': self.confidence_threshold,
            'mode': 'debug' if self.debug_mode else 'realtime',
            'current_date': self.current_date.strftime('%Y-%m-%d %H:%M')
        }
