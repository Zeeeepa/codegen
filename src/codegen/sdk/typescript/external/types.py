from dataclasses import dataclass


@dataclass
class PackageJsonData:
    dependencies: dict[str, str]
    dev_dependencies: dict[str, str]
    package_data: dict