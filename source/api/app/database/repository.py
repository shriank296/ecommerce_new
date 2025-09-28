"""
Repositories for interacting with database domain.

The purpose of this module is to define some generics, that can later be used 
widely in the project.

A generic model with a generic type key, that can be passed as argument to a 
BaseRepository class and provide basic methods to interact with a db.

more at https://mypy.readthedocs.io/en/stable/generics.html
"""

from datetime import datetime, timezone
from typing import Any, Generic, Protocol, Sequence, TypeVar

from pydantic import BaseModel
from sqlalchemy import delete, select, update
from sqlalchemy.sql import column
from sqlalchemy.sql.expression import ColumnExpressionArgument, and_

from app.database import RootSession

_Key = TypeVar("_Key", contravariant=True)
Model = TypeVar("Model", covariant=True)
InputDTO = TypeVar("InputDTO", contravariant=True, bound=BaseModel)

Key = TypeVar("Key")


class BaseRepositoryProtocol(Protocol[Model, _Key, InputDTO]):
    """Base protocol any repository has to implement."""

    def get(self, pk: _Key) -> Model | None: ...
    def list(self, *args: ColumnExpressionArgument[bool]) -> Sequence[Model]: ...
    def add(self, input_model: InputDTO) -> Model: ...
    def delete(self, *args: ColumnExpressionArgument[bool]) -> int: ...
    def update(
        self,
        conditions: Sequence[ColumnExpressionArgument[bool]],
        input_values: dict[str, Any],
    ) -> Sequence[Model]: ...


class BaseRepository(Generic[Model, Key, InputDTO]):
    model: type[Model]

    def __init__(self, session: RootSession) -> None:
        self._session = session

    def get(self, pk: Key) -> Model | None:
        """Get a record by the primary key of the table.

        Args:
            pk: Chosen Key to fecth record for.

        Returns:
            Model: Model representation of db row.
        """
        return self._session.get(self.model, pk)

    def list(self, *args: ColumnExpressionArgument[bool]) -> Sequence[Model]:
        """List all matching record that match the filter.

        Args:
            *args: Column filters, all filters are 'AND' claused together, if
            you need to use an 'OR' statement then wrap two clauses with
            `sqlalchemy.or_`.
            Example:
            for sqlalchemy import and_
            arg = and_(M.SomeModel.id == id, M.SomeModel.risk_id == risk_id)

            or

            arg = M.SomeModel.id == id

            stored_data = uow.some_repo.list(arg)

        Returns:
            Sequence of models matching filter.
        """
        stmt = select(self.model).where(*args)
        return self._session.execute(stmt).scalars().all()

    def get_one(self, *args: ColumnExpressionArgument[bool]) -> Model | None:
        """Get one matching record that match the filter.

        Args:
            *args: Column filters, all filters are 'AND' claused together, if
            you need to use an 'OR' statement then wrap two clauses with
            `sqlalchemy.or_`.
            Example:
            for sqlalchemy import and_
            arg = and_(M.SomeModel.id == id, M.SomeModel.risk_id == risk_id)

            or

            arg = M.SomeModel.id == id

            stored_data = uow.some_repo.list(arg)

        Returns:
            One model matching filter.
        """
        stmt = select(self.model).where(*args)
        return self._session.execute(stmt).scalars().first()

    def add(self, input_model: InputDTO, flush: bool = False) -> Model:
        """Add an object to the session.

        TODO: This method breaks encapsulation around the db and requires
        dependent tiers to create DB model objects to feed into the repo. We
        should create a `serialisation_model` type(e.g. Pydantic DTO) and
        have that passed across the boundary.

        Args:
            model: object to add to the session.

        KWargs:
            flush: flush this object to the session to get a full object. This
            can be useful when you want to get a primary key back.

        Returns:
            model: object that was added to the session.
        """
        _model = self.model(**input_model.model_dump())
        self._session.add(_model)
        if flush:
            self._session.flush()

        return _model

    def delete(self, *args: ColumnExpressionArgument[bool]) -> int:
        """Delete records which match the filter.

        Args:
            *args: Column filters, all filters are 'AND' claused together, if
            you need to use an 'OR' statement then wrap two clauses with
            `sqlalchemy.or_`.

        Returns:
            Count of deleted records.
        """
        stmt = delete(self.model).where(*args)
        res = self._session.execute(stmt)
        return res.rowcount

    def update(
        self,
        conditions: Sequence[ColumnExpressionArgument[bool]],
        input_values: dict[str, Any],
    ) -> Sequence[Model]:
        """Update a record in the database.

        Args:
            conditions: Conditions to match the record to update.
            input_values: Values to update the record with.

        Returns:
            Sequence of updated records.
        """

        stmt = (
            update(self.model)
            .where(*conditions)
            .values(input_values)
            .returning(self.model)
        )
        res = self._session.execute(stmt).scalars().all()

        return res


class SoftBaseRepository(BaseRepository, Generic[Model, Key, InputDTO]):

    def get(self, pk: Key) -> Model | None:
        """Get a record by the primary key of the table.

        Args:
            pk: Chosen Key to fecth record for.

        Returns:
            Model: Model representation of db row.
        """

        stmt = select(self.model).where(
            and_(self.model.id == pk, column("deleted_by").is_(None))
        )

        return self._session.execute(stmt).scalars().first()

    def delete(
        self,
        *args: ColumnExpressionArgument[bool],
        deleted_by: str | None = None,
    ) -> int:
        """Delete records which match the filter.

        Args:
            *args: Column filters, all filters are 'AND' claused together, if
            you need to use an 'OR' statement then wrap two clauses with
            `sqlalchemy.or_`.

        Returns:
            Count of deleted records.
        """

        deleted_at = datetime.now(timezone.utc)

        if not deleted_by:
            deleted_by = "Mr Unknown"

        stmt = (
            update(self.model)
            .where(*args)
            .values(deleted_by=deleted_by, deleted_at=deleted_at)
        )
        res = self._session.execute(stmt)
        return res.rowcount

    def list(self, *args: ColumnExpressionArgument[bool]) -> Sequence[Model]:
        return super().list(*args, self.model.deleted_by.is_(None))
