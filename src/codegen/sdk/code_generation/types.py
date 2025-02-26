from dataclasses import dataclass


@dataclass
class ContextMock:
    config_file = "/Users/jesusmeza/Documents/codegen-sdk/pyproject.toml"

    def get_parameter_source(self, param_name):
        if hasattr(self, param_name):
            return getattr(self, param_name)
        return None