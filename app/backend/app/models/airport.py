from sqlalchemy import Column, String, Boolean
from app.database.connection import Base


class Airport(Base):
    __tablename__ = "airports"

    airport_code = Column(String, primary_key=True)
    airport_name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    timezone = Column(String, nullable=False)
    customs_available = Column(Boolean, default=True)
