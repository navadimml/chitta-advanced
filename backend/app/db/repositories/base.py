"""
Base Repository - Generic CRUD Operations.

Provides a foundation for all repositories with:
- Common CRUD operations (create, read, update, delete)
- Soft delete support
- Pagination and filtering
- Type-safe async operations
"""

import uuid
from datetime import datetime, timezone
from typing import TypeVar, Generic, Type, Optional, List, Any, Sequence

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import Base, SoftDeleteMixin

# Type variable for model classes
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic base repository with common CRUD operations.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(User, session)
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session

    # =========================================================================
    # CREATE
    # =========================================================================

    async def create(self, **kwargs) -> ModelType:
        """
        Create a new entity.

        Args:
            **kwargs: Model field values

        Returns:
            Created entity
        """
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def create_many(self, items: List[dict]) -> List[ModelType]:
        """
        Create multiple entities.

        Args:
            items: List of dicts with model field values

        Returns:
            List of created entities
        """
        entities = [self.model(**item) for item in items]
        self.session.add_all(entities)
        await self.session.flush()
        for entity in entities:
            await self.session.refresh(entity)
        return entities

    # =========================================================================
    # READ
    # =========================================================================

    async def get_by_id(
        self,
        id: uuid.UUID,
        *,
        include_deleted: bool = False,
        load_relations: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """
        Get entity by ID.

        Args:
            id: Entity UUID
            include_deleted: Include soft-deleted entities
            load_relations: List of relationship names to eager load

        Returns:
            Entity or None
        """
        stmt = select(self.model).where(self.model.id == id)

        # Handle soft delete
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        # Eager load relations
        if load_relations:
            for relation in load_relations:
                stmt = stmt.options(selectinload(getattr(self.model, relation)))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        include_deleted: bool = False,
        load_relations: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> Sequence[ModelType]:
        """
        Get all entities.

        Args:
            include_deleted: Include soft-deleted entities
            load_relations: List of relationship names to eager load
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of entities
        """
        stmt = select(self.model)

        # Handle soft delete
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        # Eager load relations
        if load_relations:
            for relation in load_relations:
                stmt = stmt.options(selectinload(getattr(self.model, relation)))

        # Pagination
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_field(
        self,
        field_name: str,
        value: Any,
        *,
        include_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        Get single entity by field value.

        Args:
            field_name: Name of the field to filter by
            value: Value to match
            include_deleted: Include soft-deleted entities

        Returns:
            Entity or None
        """
        stmt = select(self.model).where(getattr(self.model, field_name) == value)

        if not include_deleted and hasattr(self.model, 'deleted_at'):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_many_by_field(
        self,
        field_name: str,
        value: Any,
        *,
        include_deleted: bool = False,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> Sequence[ModelType]:
        """
        Get multiple entities by field value.

        Args:
            field_name: Name of the field to filter by
            value: Value to match
            include_deleted: Include soft-deleted entities
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of entities
        """
        stmt = select(self.model).where(getattr(self.model, field_name) == value)

        if not include_deleted and hasattr(self.model, 'deleted_at'):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def exists(
        self,
        id: uuid.UUID,
        *,
        include_deleted: bool = False
    ) -> bool:
        """
        Check if entity exists.

        Args:
            id: Entity UUID
            include_deleted: Include soft-deleted entities

        Returns:
            True if exists
        """
        stmt = select(func.count()).select_from(self.model).where(self.model.id == id)

        if not include_deleted and hasattr(self.model, 'deleted_at'):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def count(
        self,
        *,
        include_deleted: bool = False,
        filters: Optional[dict] = None
    ) -> int:
        """
        Count entities.

        Args:
            include_deleted: Include soft-deleted entities
            filters: Dict of field_name: value to filter by

        Returns:
            Count of entities
        """
        stmt = select(func.count()).select_from(self.model)

        if not include_deleted and hasattr(self.model, 'deleted_at'):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        if filters:
            for field_name, value in filters.items():
                stmt = stmt.where(getattr(self.model, field_name) == value)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    # =========================================================================
    # UPDATE
    # =========================================================================

    async def update(
        self,
        id: uuid.UUID,
        **kwargs
    ) -> Optional[ModelType]:
        """
        Update entity by ID.

        Args:
            id: Entity UUID
            **kwargs: Fields to update

        Returns:
            Updated entity or None if not found
        """
        entity = await self.get_by_id(id)
        if not entity:
            return None

        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update_many(
        self,
        filters: dict,
        **kwargs
    ) -> int:
        """
        Update multiple entities matching filters.

        Args:
            filters: Dict of field_name: value to filter by
            **kwargs: Fields to update

        Returns:
            Number of updated rows
        """
        stmt = update(self.model)

        for field_name, value in filters.items():
            stmt = stmt.where(getattr(self.model, field_name) == value)

        stmt = stmt.values(**kwargs)

        result = await self.session.execute(stmt)
        return result.rowcount

    # =========================================================================
    # DELETE
    # =========================================================================

    async def delete(
        self,
        id: uuid.UUID,
        *,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete entity by ID.

        By default performs soft delete if model supports it.

        Args:
            id: Entity UUID
            hard_delete: Force permanent deletion

        Returns:
            True if deleted
        """
        if hard_delete or not hasattr(self.model, 'deleted_at'):
            # Hard delete
            stmt = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(stmt)
            return result.rowcount > 0
        else:
            # Soft delete
            entity = await self.get_by_id(id)
            if not entity:
                return False
            entity.deleted_at = datetime.now(timezone.utc)
            await self.session.flush()
            return True

    async def delete_many(
        self,
        filters: dict,
        *,
        hard_delete: bool = False
    ) -> int:
        """
        Delete multiple entities matching filters.

        Args:
            filters: Dict of field_name: value to filter by
            hard_delete: Force permanent deletion

        Returns:
            Number of deleted rows
        """
        if hard_delete or not hasattr(self.model, 'deleted_at'):
            stmt = delete(self.model)
            for field_name, value in filters.items():
                stmt = stmt.where(getattr(self.model, field_name) == value)
            result = await self.session.execute(stmt)
            return result.rowcount
        else:
            return await self.update_many(
                filters,
                deleted_at=datetime.now(timezone.utc)
            )

    async def restore(self, id: uuid.UUID) -> Optional[ModelType]:
        """
        Restore soft-deleted entity.

        Args:
            id: Entity UUID

        Returns:
            Restored entity or None
        """
        if not hasattr(self.model, 'deleted_at'):
            return None

        entity = await self.get_by_id(id, include_deleted=True)
        if not entity:
            return None

        entity.deleted_at = None
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
