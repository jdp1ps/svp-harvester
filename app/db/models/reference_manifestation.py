from typing import List

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship

from app.db.session import Base
from app.utilities.url_utilities import is_web_url


class ReferenceManifestation(Base):
    """
    Model for persistence of reference manifestations
    """

    __tablename__ = "reference_manifestations"

    id: Mapped[int] = mapped_column(primary_key=True)
    page: Mapped[str] = mapped_column(nullable=False)
    download_url: Mapped[str] = mapped_column(nullable=True)
    additional_files: Mapped[List[str]] = mapped_column(
        ARRAY(String), nullable=True, default=[]
    )
    reference: Mapped["app.db.models.reference.Reference"] = relationship(
        "app.db.models.reference.Reference",
        back_populates="manifestations",
        lazy="raise",
    )
    reference_id: Mapped[int] = mapped_column(ForeignKey("references.id"), index=True)

    def _validate_url(self, key, url) -> str:
        """
        Validate that the given URL is valid and starts with http or https.

        :param key: key
        :param url: url to validate
        :return: url if valid
        """
        if url and not is_web_url(url):
            raise ValueError(f"{key.capitalize()} URL {url} is not a valid URL")
        return url

    @validates("page")
    def _validate_page(self, key, page) -> str:
        """
        Validate that the page URL is valid.

        :param key:
        :param page:
        :return:
        """
        return self._validate_url(key, page)

    @validates("download_url")
    def _validate_download_url(self, key, download_url) -> str:
        """
        Validate that the download URL is valid.

        :param key:
        :param download_url:
        :return:
        """
        return self._validate_url(key, download_url)

    @validates("additional_files")
    def _validate_additional_files(self, key, additional_files) -> List[str]:
        """
        Validate that the additional files URLs are valid.

        :param key:
        :param additional_files:
        :return:
        """
        return [self._validate_url(key, url) for url in additional_files]
