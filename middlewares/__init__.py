from .auth import AuthMiddleware
from .error_logging import ErrorLoggingMiddleware
from .extra_data import ExtraDataMiddleware
from .menu import MenuMiddleware
from .typing_action import TypingActionMiddleware
from .ad import AdMiddleware

OUTER_MIDDLEWARES = (
	AuthMiddleware, ErrorLoggingMiddleware,
	ExtraDataMiddleware
)
