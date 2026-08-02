"""Context for object instantiation: shared cache and forced source picks."""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

# Instantiated puzzle cache (cache-key → value) while generating a sample.
_instance_cache: ContextVar[dict[str, Any] | None] = ContextVar(
    "instance_cache", default=None
)
# When set, the next object with a matching ``source`` list must use this key.
_forced_source_key: ContextVar[str | None] = ContextVar(
    "forced_source_key", default=None
)

@contextmanager
def use_instance_cache(cache: dict[str, Any]):
    token = _instance_cache.set(cache)
    try:
        yield
    finally:
        _instance_cache.reset(token)

@contextmanager
def force_source_key(key: str | None):
    token = _forced_source_key.set(key)
    try:
        yield
    finally:
        _forced_source_key.reset(token)

def get_instance_cache() -> dict[str, Any]:
    cache = _instance_cache.get()
    if cache is None:
        raise RuntimeError("object instantiation requires an active instance cache")
    return cache

def get_forced_source_key() -> str | None:
    return _forced_source_key.get()
