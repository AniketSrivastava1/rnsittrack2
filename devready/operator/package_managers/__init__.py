# Import submodules so adapters self-register into the registry at import time
from devready.operator.package_managers import nodejs, python, other  # noqa: F401
from devready.operator.package_managers.adapter import registry

__all__ = ["registry", "nodejs", "python", "other"]
