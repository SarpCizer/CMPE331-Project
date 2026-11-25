from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class CoreBase(DeclarativeBase):
    pass


class PurchaseConfirmation(CoreBase):
    __tablename__ = 'purchase_confirmations'
    owner_id: Mapped[str] = mapped_column(ForeignKey('accounts.id', ondelete='CASCADE'), primary_key=True)
    item_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    payload_hash: Mapped[str] = mapped_column(String(64))
    inventory_id: Mapped[str] = mapped_column(String(128))


class CookingConfirmation(CoreBase):
    __tablename__ = 'cooking_confirmations'
    owner_id: Mapped[str] = mapped_column(ForeignKey('accounts.id', ondelete='CASCADE'), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recipe_id: Mapped[str] = mapped_column(String(128))
    payload_hash: Mapped[str] = mapped_column(String(64))


class Account(CoreBase):
    __tablename__ = 'accounts'
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Preferences(CoreBase):
    __tablename__ = 'account_preferences'
    owner_id: Mapped[str] = mapped_column(ForeignKey('accounts.id', ondelete='CASCADE'), primary_key=True)
    dietary_rows: Mapped[list['DietaryPreference']] = relationship(
        cascade='all, delete-orphan', order_by='DietaryPreference.position')
    allergen_rows: Mapped[list['AllergenExclusion']] = relationship(
        cascade='all, delete-orphan', order_by='AllergenExclusion.position')

    @property
    def dietary(self):
        return [row.display_value for row in self.dietary_rows]

    @dietary.setter
    def dietary(self, values):
        self.dietary_rows = [DietaryPreference(position=index,display_value=value,
            value_key=value.strip().casefold()) for index,value in enumerate(values)]

    @property
    def allergens(self):
        return [row.display_value for row in self.allergen_rows]

    @allergens.setter
    def allergens(self, values):
        self.allergen_rows = [AllergenExclusion(position=index,display_value=value,
            value_key=value.strip().casefold()) for index,value in enumerate(values)]


class DietaryPreference(CoreBase):
    __tablename__ = 'dietary_preferences'
    owner_id: Mapped[str] = mapped_column(ForeignKey('account_preferences.owner_id',ondelete='CASCADE'),primary_key=True)
    position: Mapped[int] = mapped_column(Integer,primary_key=True)
    display_value: Mapped[str] = mapped_column(String(128))
    value_key: Mapped[str] = mapped_column(String(384))


class AllergenExclusion(CoreBase):
    __tablename__ = 'allergen_exclusions'
    owner_id: Mapped[str] = mapped_column(ForeignKey('account_preferences.owner_id',ondelete='CASCADE'),primary_key=True)
    position: Mapped[int] = mapped_column(Integer,primary_key=True)
    display_value: Mapped[str] = mapped_column(String(128))
    value_key: Mapped[str] = mapped_column(String(384))


class InventoryEntry(CoreBase):
    __tablename__ = 'inventory_entries'
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('accounts.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(256))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(8), nullable=True)
