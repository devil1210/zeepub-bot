from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text

from models.base import Base


class StoredMessage(Base):
    __tablename__ = "stored_messages"
    slug = Column(String(64), primary_key=True)
    source_chat_id = Column(BigInteger, nullable=False)
    source_message_id = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    text_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PluginSettings(Base):
    __tablename__ = "custom_messages_settings"
    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=True)


class GlobalVariable(Base):
    __tablename__ = "global_variables"
    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=True)
