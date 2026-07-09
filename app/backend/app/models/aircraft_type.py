from sqlalchemy import Column, String, Float, Boolean
from app.database.connection import Base


class AircraftType(Base):
    __tablename__ = "aircraft_types"

    aircraft_type = Column(String, primary_key=True)
    max_cargo_weight_kg = Column(Float, nullable=False)
    max_cargo_volume_m3 = Column(Float, nullable=False)
    temperature_controlled_capacity_kg = Column(Float, default=0)
    is_freighter = Column(Boolean, default=False)
    dangerous_goods_allowed = Column(Boolean, default=False)
