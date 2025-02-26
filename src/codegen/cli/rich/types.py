from dataclasses import dataclass


@dataclass
class SpinnerConfig:
    """Configuration for a consistent spinner style."""

    text: str
    spinner: str = "dots"
    style: str = "bold"
    spinner_style: str = "blue"