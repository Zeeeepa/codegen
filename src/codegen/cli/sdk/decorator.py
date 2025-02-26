from collections.abc import Callable, Sequence
from functools import wraps
from typing import Literal, ParamSpec, TypeVar, get_type_hints

P = ParamSpec("P")
T = TypeVar("T")
WebhookType = Literal["pr", "push", "issue", "release"]
WebhookEvent = Literal["created", "updated", "closed", "reopened", "synchronized"]


class DecoratedFunction:
    """Represents a Python function decorated with a codegen decorator."""

    def __init__(
        self,
        name: str,
        *,
        webhook_config: dict | None = None,
        lint_mode: bool = False,
        lint_user_whitelist: Sequence[str] | None = None,
    ):
        self.name = name
        self.func: Callable | None = None
        self.params_type = None
        self.webhook_config = webhook_config
        self.lint_mode = lint_mode
        self.lint_user_whitelist = list(lint_user_whitelist) if lint_user_whitelist else []

    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        # Get the params type from the function signature
        hints = get_type_hints(func)
        if "params" in hints:
            self.params_type = hints["params"]

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return func(*args, **kwargs)

        # Set the codegen name on the wrapper function
        wrapper.__codegen_name__ = self.name
        self.func = wrapper
        return wrapper


def function(name: str) -> DecoratedFunction:
    """Decorator for codegen functions.

    Args:
        name: The name of the function to be used when deployed

    Example:
        @codegen.function('my-function')
        def run(codebase):
            pass

    """
    return DecoratedFunction(name)
