"""SQLAlchemy base inheritables.

The naming convention is used by alembic when autogenerating migrations.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",  # indexes
            "uq": "uq_%(table_name)s_%(column_0_name)s",  # unique constraints
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",  # check constraints
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # foreign keys
            "pk": "pk_%(table_name)s",  # primary keys
        }
    )
