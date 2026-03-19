"""
自定义异常定义模块
"""


class InvestmentError(Exception):
    """投资研究系统基础异常"""
    
    def __init__(self, message: str = "投资研究系统错误", code: str = None):
        self.message = message
        self.code = code or "INVESTMENT_ERROR"
        super().__init__(self.message)
    
    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class DataError(InvestmentError):
    """数据相关错误"""
    
    def __init__(self, message: str = "数据错误", code: str = "DATA_ERROR"):
        super().__init__(message, code)


class DataSourceError(DataError):
    """数据源错误"""
    
    def __init__(self, source: str = None, message: str = None):
        self.source = source
        msg = message or f"数据源错误: {source}"
        super().__init__(msg, "DATA_SOURCE_ERROR")


class DataFetchError(DataError):
    """数据获取错误"""
    
    def __init__(self, code: str = None, message: str = None):
        self.code = code
        msg = message or f"获取股票 {code} 数据失败"
        super().__init__(msg, "DATA_FETCH_ERROR")


class DataValidationError(DataError):
    """数据验证错误"""
    
    def __init__(self, field: str = None, message: str = None):
        self.field = field
        msg = message or f"数据验证失败: {field}"
        super().__init__(msg, "DATA_VALIDATION_ERROR")


class ValidationError(InvestmentError):
    """验证错误"""
    
    def __init__(self, message: str = "验证失败", code: str = "VALIDATION_ERROR"):
        super().__init__(message, code)


class ParameterError(ValidationError):
    """参数错误"""
    
    def __init__(self, param: str = None, message: str = None):
        self.param = param
        msg = message or f"参数错误: {param}"
        super().__init__(msg, "PARAMETER_ERROR")


class BacktestError(InvestmentError):
    """回测错误"""
    
    def __init__(self, message: str = "回测失败", code: str = "BACKTEST_ERROR"):
        super().__init__(message, code)


class StrategyError(BacktestError):
    """策略错误"""
    
    def __init__(self, strategy: str = None, message: str = None):
        self.strategy = strategy
        msg = message or f"策略错误: {strategy}"
        super().__init__(msg, "STRATEGY_ERROR")


class ExecutionError(BacktestError):
    """执行错误"""
    
    def __init__(self, trade_id: str = None, message: str = None):
        self.trade_id = trade_id
        msg = message or f"交易执行错误: {trade_id}"
        super().__init__(msg, "EXECUTION_ERROR")


class ScreeningError(InvestmentError):
    """筛选错误"""
    
    def __init__(self, message: str = "筛选失败", code: str = "SCREENING_ERROR"):
        super().__init__(message, code)


class FactorError(ScreeningError):
    """因子错误"""
    
    def __init__(self, factor: str = None, message: str = None):
        self.factor = factor
        msg = message or f"因子计算错误: {factor}"
        super().__init__(msg, "FACTOR_ERROR")


class FilterError(ScreeningError):
    """过滤器错误"""
    
    def __init__(self, filter_name: str = None, message: str = None):
        self.filter_name = filter_name
        msg = message or f"过滤器错误: {filter_name}"
        super().__init__(msg, "FILTER_ERROR")


class TechnicalError(InvestmentError):
    """技术分析错误"""
    
    def __init__(self, message: str = "技术分析错误", code: str = "TECHNICAL_ERROR"):
        super().__init__(message, code)


class IndicatorError(TechnicalError):
    """指标计算错误"""
    
    def __init__(self, indicator: str = None, message: str = None):
        self.indicator = indicator
        msg = message or f"指标计算错误: {indicator}"
        super().__init__(msg, "INDICATOR_ERROR")


class PatternError(TechnicalError):
    """形态识别错误"""
    
    def __init__(self, pattern: str = None, message: str = None):
        self.pattern = pattern
        msg = message or f"形态识别错误: {pattern}"
        super().__init__(msg, "PATTERN_ERROR")


class ConnectionError(InvestmentError):
    """连接错误"""
    
    def __init__(self, message: str = "连接错误", code: str = "CONNECTION_ERROR"):
        super().__init__(message, code)


class TimeoutError(ConnectionError):
    """超时错误"""
    
    def __init__(self, timeout: float = None, message: str = None):
        self.timeout = timeout
        msg = message or f"请求超时: {timeout}秒"
        super().__init__(msg, "TIMEOUT_ERROR")


class AuthenticationError(ConnectionError):
    """认证错误"""
    
    def __init__(self, service: str = None, message: str = None):
        self.service = service
        msg = message or f"认证失败: {service}"
        super().__init__(msg, "AUTHENTICATION_ERROR")


class RateLimitError(ConnectionError):
    """速率限制错误"""
    
    def __init__(self, limit: int = None, reset_time: float = None, message: str = None):
        self.limit = limit
        self.reset_time = reset_time
        msg = message or f"请求频率超限: {limit}/分钟"
        super().__init__(msg, "RATE_LIMIT_ERROR")


def handle_exception(func):
    """
    异常处理装饰器
    
    捕获函数执行中的异常并统一处理
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InvestmentError as e:
            # 已知错误，直接抛出
            raise e
        except Exception as e:
            # 未知错误，包装为InvestmentError
            raise InvestmentError(
                message=f"执行错误: {str(e)}",
                code="EXECUTION_ERROR"
            ) from e
    
    return wrapper


def safe_execute(func, *args, default=None, **kwargs):
    """
    安全执行函数
    
    Args:
        func: 要执行的函数
        args: 位置参数
        default: 失败时的默认值
        kwargs: 关键字参数
        
    Returns:
        函数结果或默认值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"执行失败: {e}")
        return default
