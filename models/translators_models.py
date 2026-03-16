from sqlalchemy import BigInteger, Column, String
from sqlalchemy.orm import relationship
from .base import Base


class TranslatorsGroup(Base):
    """
    V4 Translators Group Entity.
    """

    __tablename__ = "translators_groups"
    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    siglas = Column(String(50), nullable=False, unique=True)
