from __future__ import annotations

# Force-load SQLAlchemy ORM internals at import time. These submodules use
# decorator-based registration (e.g. ``@strategy_for(instrument=True, deferred=False)``)
# which only runs when the module is *imported*, not when the bytecode is
# present. Nuitka's tree-shaking and PyInstaller's tree-shaking can both leave
# them unreachable from our import graph, causing
# ``LoaderStrategyException: Can't find strategy ...`` at the first ORM query.
# References:
#   https://github.com/Nuitka/Nuitka/issues/2262
#   https://github.com/sqlalchemy/sqlalchemy/discussions/10372
import sqlalchemy.dialects.sqlite  # noqa: F401
import sqlalchemy.orm.dependency  # noqa: F401
import sqlalchemy.orm.dynamic  # noqa: F401
import sqlalchemy.orm.strategies  # noqa: F401
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, configure_mappers


class ProjectBase(MappedAsDataclass, DeclarativeBase):
    """Declarative base for tables in the per-project DB."""


class RegistryBase(MappedAsDataclass, DeclarativeBase):
    """Declarative base for tables in the app-wide registry DB."""


def configure_all_mappers() -> None:
    """Eager-configure SQLAlchemy mappers at startup.

    Forces every ColumnProperty / RelationshipProperty to bind its loader
    strategy *now* instead of lazily at first query. Without this, the
    Nuitka-compiled binary on Python 3.14 fails the strategy lookup with
    ``LoaderStrategyException`` because decorator-based registrations
    inside ``sqlalchemy.orm.strategies`` happen too late in the import
    sequence under the compiled bootstrap.
    """
    # Importing the table modules ensures every mapped class is known to the
    # registry before configure_mappers() walks them.
    from chapter_extractor.services.db import (  # noqa: F401
        tables_project,
        tables_registry,
    )
    configure_mappers()
