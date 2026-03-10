import json
import functools
from typing import Optional, Any, Callable, Awaitable, TypeVar
from redis.asyncio import Redis
import inspect

from app.config import redis_config
from app.domain.ports import ICacheService

T = TypeVar("T")


class RedisCacheService(ICacheService):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        prefix: str = "eventor:payment-svc:",
        pool_size: int = 20,
    ):
        # Lazy Redis client (connection occurs only when first used)
        self._redis = Redis(
            host=host,
            port=port,
            db=db,
            max_connections=pool_size,
            decode_responses=False,
        )
        self.prefix = prefix

    async def dispose(self):
        await self._redis.shutdown(save=True)

    # -------------------------
    # Internal helpers
    # -------------------------
    def _k(self, key: str) -> str:
        """apply namespace prefix"""
        return f"{self.prefix}{key}"

    # -------------------------
    # Basic cache
    # -------------------------
    async def get(self, key: str) -> Optional[Any]:
        raw = await self._redis.get(self._k(key))
        if raw is None:
            return None
        try:
            return raw.decode()
        except Exception:
            return raw

    async def set(self, key: str, value: Any, ttl: int = 60) -> None:
        if not isinstance(value, (str, bytes, int)):
            value = str(value)
        await self._redis.set(self._k(key), value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self._redis.delete(self._k(key))

    async def clear(self) -> None:
        await self._redis.flushdb()

    # -------------------------
    # JSON helpers
    # -------------------------
    async def get_json(self, key: str) -> Optional[Any]:
        raw = await self._redis.get(self._k(key))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    async def set_json(self, key: str, value: Any, ttl: int = 60) -> None:
        await self._redis.set(self._k(key), json.dumps(value), ex=ttl)

    # -------------------------
    # Distributed lock
    # -------------------------
    async def acquire_lock(self, key: str, ttl: int = 10) -> bool:
        lock_key = self._k(f"lock:{key}")
        # SET key value NX EX ttl
        return await self._redis.set(lock_key, "1", nx=True, ex=ttl) is True

    async def release_lock(self, key: str) -> None:
        await self._redis.delete(self._k(f"lock:{key}"))

    # -------------------------
    # Cache decorator
    # -------------------------
    def cached(self, ttl: int = 60):
        """
        DDD-safe: decorate ONLY application/infrastructure services.
        """

        def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            if not inspect.iscoroutinefunction(fn):
                raise TypeError("@cached can only be applied to async functions")

            @functools.wraps(fn)
            async def wrapper(*args, **kwargs) -> T:
                # Build key based on function name + arguments
                raw_key = f"cache:{fn.__module__}.{fn.__name__}:{args}:{kwargs}"
                key = self._k(raw_key)

                # Try cache
                cached_value = await self.get_json(key)
                if cached_value is not None:
                    return cached_value

                # Compute
                result = await fn(*args, **kwargs)

                # Save result
                await self.set_json(key, result, ttl)

                return result

            return wrapper

        return decorator


_service: RedisCacheService | None = None


def get_RedisCacheService():
    global _service
    if _service is None:
        print("Initialize RedisCacheService")
        _service = RedisCacheService(
            db=redis_config.db,
            host=redis_config.host,
            port=redis_config.port,
        )
    return _service
