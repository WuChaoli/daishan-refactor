"""intent_service 包导出"""

from rag_stream.services.intent_service.base_intent_service import (
    BaseIntentService,
    IntentResult,
    QueryResult,
)

__all__ = [
    "BaseIntentService",
    "IntentService",
    "IntentResult",
    "QueryResult",
]


def __getattr__(name: str):
    if name == "IntentService":
        from rag_stream.services.intent_service.intent_service import IntentService

        return IntentService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
