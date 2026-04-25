# db/base.py
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, DateTime, func
import uuid


class Base(DeclarativeBase):
    pass


def gen_uuid() -> str:
    """Generate UUID for primary keys"""
    return str(uuid.uuid4())