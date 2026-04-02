from sqlalchemy import BigInteger, Boolean, Column, String

from models.base import Base


class GroupSettings(Base):
    __tablename__ = "group_settings"
    chat_id = Column(BigInteger, primary_key=True)
    is_authorized = Column(Boolean, default=False)
    welcome_msg_slug = Column(String(64), nullable=True)
