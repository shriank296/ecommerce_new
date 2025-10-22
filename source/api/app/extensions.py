"""Server extensions.

This is here to stop circular dependencies forming. Please do not import 
packages that will lead to circular deps.
"""

from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator()
