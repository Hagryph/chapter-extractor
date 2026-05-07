from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class ProjectBase(MappedAsDataclass, DeclarativeBase):
    """Declarative base for tables in the per-project DB."""


class RegistryBase(MappedAsDataclass, DeclarativeBase):
    """Declarative base for tables in the app-wide registry DB."""
