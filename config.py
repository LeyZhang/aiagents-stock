import os
from dotenv import load_dotenv

# 加载环境变量（override=True 强制覆盖已存在的环境变量）
load_dotenv(override=True)

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

# Gemini API配置
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")

# API提供商选择：deepseek 或 gemini
API_PROVIDER = os.getenv("API_PROVIDER", "deepseek")

# 其他配置
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")

# 股票数据源配置
DEFAULT_PERIOD = "1y"  # 默认获取1年数据
DEFAULT_INTERVAL = "1d"  # 默认日线数据

# MiniQMT量化交易配置
MINIQMT_CONFIG = {
    'enabled': os.getenv("MINIQMT_ENABLED", "false").lower() == "true",
    'account_id': os.getenv("MINIQMT_ACCOUNT_ID", ""),
    'host': os.getenv("MINIQMT_HOST", "127.0.0.1"),
    'port': int(os.getenv("MINIQMT_PORT", "58610")),
}

# TDX股票数据API配置项目地址github.com/oficcejo/tdx-api
TDX_CONFIG = {
    'enabled': os.getenv("TDX_ENABLED", "false").lower() == "true",
    'base_url': os.getenv("TDX_BASE_URL", "http://192.168.1.222:8181"),
}

# 牛市选股策略加速配置
BULL_MARKET_CONFIG = {
    'batch_size': int(os.getenv("BULL_MARKET_BATCH_SIZE", "30")),  # 批处理大小，默认30
    'analysis_timeout': int(os.getenv("BULL_MARKET_TIMEOUT", "15")),  # 单股票分析超时(秒)，并行模式下更严格
    'max_memory_mb': int(os.getenv("BULL_MARKET_MAX_MEMORY", "1024")),  # 最大内存使用(MB)
    'enable_parallel': os.getenv("BULL_MARKET_PARALLEL", "true").lower() == "true",  # 启用并行处理
    'max_workers': int(os.getenv("BULL_MARKET_WORKERS", "8")),  # 最大并行线程数
    'cache_ttl': int(os.getenv("BULL_MARKET_CACHE_TTL", "300")),  # 缓存有效期(秒)
}