from dataclasses import dataclass

from codegen.sdk.core.detached_symbols.function_call import FunctionCall


@dataclass
class FunctionCallDefinition:
    """Represents a function call and its definitions.

    This class encapsulates information about a function call and the possible
    callable entities that define it.

    Attributes:
        call (FunctionCall): The function call object representing the invocation.
        callables (List[Union[Function, Class, ExternalModule]]): A list of callable
            entities that define the function being called.
    """

    call: FunctionCall
    callables: list["Function | Class | ExternalModule"]
