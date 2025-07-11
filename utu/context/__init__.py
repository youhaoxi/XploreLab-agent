from .base_context_manager import BaseContextManager, DummyContextManager

CONTEXT_MANAGER_MAP = {
    "dummy": DummyContextManager,
}