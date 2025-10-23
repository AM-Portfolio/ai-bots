"""
Centralized logging utility for AI Dev Agent
Provides structured logging with context, timing, and LLM interaction tracking
"""
import logging
import sys
import json
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from functools import wraps
from contextvars import ContextVar

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter that adds context and structure to log messages"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add context from ContextVars
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        
        # Add timestamp
        record.timestamp = datetime.utcnow().isoformat()
        
        # Format the base message
        message = super().format(record)
        
        # Add structured data if available
        if hasattr(record, 'structured_data'):
            structured_data = getattr(record, 'structured_data', None)
            if structured_data:
                structured = json.dumps(structured_data, ensure_ascii=False)
                message = f"{message} {structured}"
        
        return message


class AppLogger:
    """Centralized logger with structured logging capabilities"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with custom formatter"""
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = StructuredFormatter(
                '%(timestamp)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional structured data"""
        self._log(logging.INFO, message, kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional structured data"""
        self._log(logging.ERROR, message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional structured data"""
        self._log(logging.WARNING, message, kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional structured data"""
        self._log(logging.DEBUG, message, kwargs)
    
    def _log(self, level: int, message: str, extra_data: Dict[str, Any]):
        """Internal logging method with structured data support"""
        extra = {}
        if extra_data:
            extra['structured_data'] = extra_data
        self.logger.log(level, message, extra=extra)
    
    def log_method_call(self, method_name: str, args: tuple = (), kwargs: Optional[dict] = None, duration_ms: Optional[float] = None):
        """Log a method call with parameters and duration"""
        parts = [f"Method: {method_name}", f"args_count={len(args)}"]
        if kwargs:
            parts.append(f"kwargs_keys={list(kwargs.keys())}")
        if duration_ms is not None:
            parts.append(f"duration_ms={float(round(duration_ms, 2))}")
        
        self.info(" ".join(parts))
    
    def log_llm_request(self, provider: str, model: str, prompt: str, temperature: Optional[float] = None):
        """Log LLM request with details"""
        preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        parts = [f"🤖 LLM Request to {provider}", f"model={model}", f"prompt_length={len(prompt)}", f"preview='{preview}'"]
        if temperature is not None:
            parts.append(f"temperature={temperature}")
        
        self.info(" ".join(parts))
    
    def log_llm_response(self, provider: str, response: Optional[str], duration_ms: float, tokens: Optional[int] = None, error: Optional[str] = None):
        """Log LLM response with metrics"""
        if error:
            self.error(
                f"❌ LLM Error from {provider} - error={error} duration_ms={float(round(duration_ms, 2))}"
            )
        else:
            preview = response[:100] + "..." if response and len(response) > 100 else response
            parts = [f"✅ LLM Response from {provider}", f"response_length={len(response) if response else 0}", f"preview='{preview}'", f"duration_ms={float(round(duration_ms, 2))}"]
            if tokens is not None:
                parts.append(f"tokens={tokens}")
            
            self.info(" ".join(parts))
    
    def log_api_request(self, method: str, path: str, status_code: Optional[int] = None, duration_ms: Optional[float] = None):
        """Log API request with metrics"""
        status_emoji = "✅" if status_code and status_code < 400 else "❌"
        parts = [f"{status_emoji} API {method} {path}"]
        if status_code is not None:
            parts.append(f"status={status_code}")
        if duration_ms is not None:
            parts.append(f"duration_ms={float(round(duration_ms, 2))}")
        
        self.info(" ".join(parts))
    
    def log_github_operation(self, operation: str, repo: str, details: Optional[Dict[str, Any]] = None):
        """Log GitHub operation with details"""
        parts = [f"📦 GitHub: {operation} - {repo}"]
        if details:
            detail_str = " ".join([f"{k}={v}" for k, v in details.items()])
            parts.append(detail_str)
        self.info(" ".join(parts))
    
    def log_database_operation(self, operation: str, table: str, duration_ms: Optional[float] = None):
        """Log database operation with timing"""
        data: Dict[str, Any] = {'operation': operation, 'table': table}
        if duration_ms is not None:
            data['duration_ms'] = float(round(duration_ms, 2))
        self.info(f"🗄️ Database: {operation} on {table}", **data)


def get_logger(name: str) -> AppLogger:
    """Get or create a logger instance"""
    return AppLogger(name)


def log_method(logger: Optional[AppLogger] = None):
    """Decorator to automatically log method entry, exit, and duration"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            start_time = time.time()
            method_name = f"{func.__module__}.{func.__name__}"
            
            logger.debug(f"→ Entering {method_name}")
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.log_method_call(method_name, args, kwargs, duration_ms)
                logger.debug(f"← Exiting {method_name} (success)")
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"← Exiting {method_name} (error)",
                    error=str(e),
                    duration_ms=round(duration_ms, 2)
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            start_time = time.time()
            method_name = f"{func.__module__}.{func.__name__}"
            
            logger.debug(f"→ Entering {method_name}")
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.log_method_call(method_name, args, kwargs, duration_ms)
                logger.debug(f"← Exiting {method_name} (success)")
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"← Exiting {method_name} (error)",
                    error=str(e),
                    duration_ms=round(duration_ms, 2)
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def set_request_context(request_id: Optional[str] = None, user_id: Optional[str] = None):
    """Set request context for logging"""
    if request_id:
        request_id_var.set(request_id)
    else:
        request_id_var.set(str(uuid.uuid4()))
    
    if user_id:
        user_id_var.set(user_id)


def clear_request_context():
    """Clear request context"""
    request_id_var.set(None)
    user_id_var.set(None)


# Create a default logger for immediate use
default_logger = get_logger("ai_dev_agent")
