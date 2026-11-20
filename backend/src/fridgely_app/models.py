from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class CoreBase(DeclarativeBase):
    pass


class Account(CoreBase):
    __tablename__ = 'accounts'
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Preferences(CoreBase):
    __tablename__ = 'account_preferences'
    owner_id: Mapped[str] = mapped_column(ForeignKey('accounts.id', ondelete='CASCADE'), primary_key=True)
    dietary: Mapped[list] = mapped_column(JSON)
    allergens: Mapped[list] = mapped_column(JSON)


class InventoryEntry(CoreBase):
    __tablename__ = 'inventory_entries'
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('accounts.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(256))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
