"""Utilities for lazy initialization and timeout handling"""
import asyncio
import functools
import time
from typing import Any, Callable, Optional, TypeVar, Union
from concurrent.futures import TimeoutError as FuturesTimeoutError
import threading

T = TypeVar('T')


def with_timeout(timeout: float = 5.0):
    """Decorator to add timeout to synchronous functions"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout)
            
            if thread.is_alive():
                raise TimeoutError(f"{func.__name__} timed out after {timeout} seconds")
            
            if exception[0]:
                raise exception[0]
                
            return result[0]
        
        return wrapper
    return decorator


async def async_with_timeout(coro, timeout: float = 5.0):
    """Add timeout to async operations"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation timed out after {timeout} seconds")


class LazyConnection:
    """Base class for lazy connection management"""
    
    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout
        self._connection = None
        self._initialized = False
        self._initialization_error = None
    
    def _connect(self):
        """Override this method to implement actual connection logic"""
        raise NotImplementedError
    
    @property
    def connection(self):
        """Get connection, initializing if necessary"""
        if not self._initialized:
            try:
                with_timeout(self.timeout)(self._connect)()
                self._initialized = True
            except Exception as e:
                self._initialization_error = e
                raise ConnectionError(f"Failed to initialize {self.name}: {str(e)}")
        
        if self._initialization_error:
            raise self._initialization_error
            
        return self._connection
    
    def is_connected(self) -> bool:
        """Check if connection is established"""
        return self._initialized and self._connection is not None
    
    def reset(self):
        """Reset connection state"""
        self._connection = None
        self._initialized = False
        self._initialization_error = None


class LazyChromaDB(LazyConnection):
    """Lazy ChromaDB connection with timeout"""
    
    def __init__(self, config: dict, timeout: float = 5.0):
        super().__init__("ChromaDB", timeout)
        self.config = config
    
    def _connect(self):
        import chromadb
        from chromadb.config import Settings
        
        if self.config.get("type") == "http":
            self._connection = chromadb.HttpClient(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 8000),
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self._connection = chromadb.PersistentClient(
                path=self.config.get("persist_path", "./knowledge/chromadb"),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )


class LazyOpenAI(LazyConnection):
    """Lazy OpenAI connection with timeout"""
    
    def __init__(self, timeout: float = 5.0):
        super().__init__("OpenAI", timeout)
        self.llm = None
        self.embeddings = None
    
    def _connect(self):
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-4")
        self.embeddings = OpenAIEmbeddings()
        self._connection = True  # Mark as connected


def debug_print(message: str, debug: bool = False):
    """Print debug messages if debug mode is enabled"""
    if debug:
        print(f"[DEBUG] {time.strftime('%H:%M:%S')} - {message}")