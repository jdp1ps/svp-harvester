from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class HarvestingError(Base):
    """
    Model for persistence of harvesting errors
    """

    __tablename__ = "harvesting_errors"

    id: Mapped[int] = mapped_column(primary_key=True)

    harvesting_id: Mapped[int] = mapped_column(ForeignKey("harvestings.id"), index=True)

    name: Mapped[str] = mapped_column(nullable=False)

    message: Mapped[str] = mapped_column(nullable=False)
