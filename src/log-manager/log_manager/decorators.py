from __future__ import annotations

import functools
import inspect
import typing
from typing import Any, Callable, TypeVar

from .runtime import get_runtime


F = TypeVar("F", bound=Callable[..., Any])


def _apply_resolved_signature(wrapper: Callable[..., Any], original: Callable[..., Any]) -> None:
    """Keep original call signature and resolve postponed annotations for frameworks like FastAPI."""
    original_signature = inspect.signature(original)
    try:
        resolved_hints = typing.get_type_hints(original, include_extras=True)
    except Exception:
        resolved_hints = {}

    resolved_params = [
        param.replace(annotation=resolved_hints.get(param.name, param.annotation))
        for param in original_signature.parameters.values()
    ]
    resolved_return = resolved_hints.get("return", original_signature.return_annotation)

    wrapper.__signature__ = original_signature.replace(
        parameters=resolved_params,
        return_annotation=resolved_return,
    )
    if resolved_hints:
        wrapper.__annotations__ = resolved_hints


def entry_trace(name: str | None = None) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                runtime = get_runtime()
                return await runtime.invoke_async(fn, args, kwargs, is_entry=True, entry_name=name)

            _apply_resolved_signature(async_wrapper, fn)
            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            runtime = get_runtime()
            return runtime.invoke(fn, args, kwargs, is_entry=True, entry_name=name)

        _apply_resolved_signature(wrapper, fn)
        return wrapper  # type: ignore[return-value]

    return decorator


def trace(fn: F | None = None) -> Callable[[F], F] | F:
    def decorator(inner: F) -> F:
        if inspect.iscoroutinefunction(inner):
            @functools.wraps(inner)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                runtime = get_runtime()
                return await runtime.invoke_async(inner, args, kwargs, is_entry=False)

            _apply_resolved_signature(async_wrapper, inner)
            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(inner)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            runtime = get_runtime()
            return runtime.invoke(inner, args, kwargs, is_entry=False)

        _apply_resolved_signature(wrapper, inner)
        return wrapper  # type: ignore[return-value]

    if fn is not None:
        return decorator(fn)
    return decorator
