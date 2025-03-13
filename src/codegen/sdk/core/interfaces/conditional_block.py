from abc import ABC, abstractmethod
from collections.abc import Sequence

from codegen.sdk.core.statements.statement import Statement
from codegen.shared.decorators.docs import noapidoc


class ConditionalBlock(Statement, ABC):
    """An interface for any code block that might not be executed in the code, e.g if block/else block/try block/catch block ect."""

    @property
    @abstractmethod
    @noapidoc
    def other_possible_blocks(self) -> Sequence["ConditionalBlock"]:
        """Should return all other "branches" that might be executed instead."""

    @property
    @noapidoc
    def end_byte_for_condition_block(self) -> int:
        """Returns the end byte for the specific condition block"""
        return self.end_byte
