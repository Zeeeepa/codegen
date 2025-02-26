from dataclasses import dataclass


@dataclass
class DocumentedObject:
    name: str
    module: str
    object: any

    def __lt__(self, other):
        return self.module < other.module

    def signature(self) -> str:
        return f"{self.name}"