# 🐂 数据提供者 - 市场数据获取
"""
数据提供者层 - 实现市场数据获取接口

包含各种数据源的适配器，统一数据格式。
"""

import akshare as ak
from typing import List, Dict, Optional, Any
from datetime import datetime

from src.core.logger import get_logger

from ..core import MarketDataProvider
from ..domain.value_objects import MarketData

logger = get_logger('bull_market_agent.data_providers')


class AKShareMarketDataProvider(MarketDataProvider):
    """AKShare市场数据提供者"""

    def __init__(self):
        self._cache = {}
        self._cache_timestamps = {}

    def get_sector_stocks(self, sector_code: str) -> List[MarketData]:
        """
        获取板块成分股数据
        使用AKShare获取实时数据
        """
        logger.info("开始获取板块成分股数据", sector_code=sector_code)

        try:
            # 检查缓存
            cache_key = f"sector_{sector_code}"
            if self._is_cache_valid(cache_key, ttl=300):  # 5分钟缓存
                cached_data = self._cache[cache_key]
                logger.debug("使用缓存数据", cache_key=cache_key, cached_items=len(cached_data))
                return cached_data

            logger.debug("缓存未命中，开始从API获取数据", cache_key=cache_key)

            # 获取板块数据
            df = ak.stock_board_concept_cons_em(symbol=sector_code)
            logger.debug("API返回数据行数", dataframe_rows=len(df))

            market_data_list = []
            for _, row in df.iterrows():
                # 构造MarketData对象
                market_data = MarketData(
                    symbol=row['代码'],
                    name=row['名称'],
                    price=float(row.get('最新价', 0)),
                    change_pct=float(row.get('涨跌幅', 0)),
                    volume=int(row.get('成交量', 0)),
                    amount=float(row.get('成交额', 0)),
                    sector=sector_code,
                    timestamp=datetime.now(),
                    additional_data={
                        'avg_volume': row.get('量比', 1) * 100000,  # 估算平均成交量
                        'market_cap': row.get('总市值', 0),
                        'pe_ratio': row.get('市盈率-动态', 0),
                    }
                )
                market_data_list.append(market_data)

            # 更新缓存
            self._cache[cache_key] = market_data_list
            self._cache_timestamps[cache_key] = datetime.now().timestamp()

            logger.info("成功获取板块数据", sector_code=sector_code, market_data_list=len(market_data_list))
            return market_data_list

        except Exception as e:
            logger.error("获取板块数据失败", sector_code=sector_code, error=str(e))
            return []

    def get_stock_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取股票历史数据
        """
        try:
            cache_key = f"history_{symbol}_{days}"
            if self._is_cache_valid(cache_key, ttl=1800):  # 30分钟缓存
                return self._cache[cache_key]

            # 获取历史数据
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date="20240101")
            recent_data = df.tail(days)

            history_list = []
            for _, row in recent_data.iterrows():
                history_list.append({
                    'date': row['日期'],
                    'open': float(row['开盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'close': float(row['收盘']),
                    'volume': int(row['成交量']),
                    'amount': float(row['成交额']),
                    'change_pct': float(row['涨跌幅']),
                })

            # 更新缓存
            self._cache[cache_key] = history_list
            self._cache_timestamps[cache_key] = datetime.now().timestamp()

            return history_list

        except Exception as e:
            print(f"获取历史数据失败 {symbol}: {e}")
            return []

    def get_market_sentiment(self) -> float:
        """
        获取市场情绪指标
        返回0-100之间的情绪分数
        """
        try:
            cache_key = "market_sentiment"
            if self._is_cache_valid(cache_key, ttl=60):  # 1分钟缓存
                return self._cache[cache_key]

            # 获取市场整体数据
            market_data = ak.stock_zh_a_spot_em()

            # 计算情绪指标
            total_stocks = len(market_data)
            rising_stocks = len(market_data[market_data['涨跌幅'] > 0])
            falling_stocks = len(market_data[market_data['涨跌幅'] < 0])

            # 涨停股比例
            limit_up_stocks = len(market_data[market_data['涨跌幅'] >= 9.8])
            limit_up_ratio = limit_up_stocks / total_stocks if total_stocks > 0 else 0

            # 计算综合情绪分数
            sentiment_score = 50.0  # 基准分

            # 上涨家数占比
            rising_ratio = rising_stocks / total_stocks if total_stocks > 0 else 0
            sentiment_score += (rising_ratio - 0.5) * 40

            # 涨停股过多表示情绪过热
            if limit_up_ratio > 0.05:
                sentiment_score -= 20
            elif limit_up_ratio > 0.02:
                sentiment_score += 10

            # 确保分数在0-100范围内
            sentiment_score = max(0, min(100, sentiment_score))

            # 更新缓存
            self._cache[cache_key] = sentiment_score
            self._cache_timestamps[cache_key] = datetime.now().timestamp()

            return sentiment_score

        except Exception as e:
            print(f"获取市场情绪失败: {e}")
            return 50.0  # 返回中性情绪

    def _is_cache_valid(self, cache_key: str, ttl: int) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache_timestamps:
            return False

        elapsed = datetime.now().timestamp() - self._cache_timestamps[cache_key]
        return elapsed < ttl