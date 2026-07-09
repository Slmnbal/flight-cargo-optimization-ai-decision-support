from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from app.database.connection import Base


class Route(Base):
    __tablename__ = "routes"

    route_id = Column(Integer, primary_key=True, autoincrement=True)
    origin_airport = Column(String, ForeignKey("airports.airport_code"), nullable=False)
    destination_airport = Column(String, ForeignKey("airports.airport_code"), nullable=False)
    distance_km = Column(Float, nullable=False)
    route_type = Column(String, nullable=False)  # domestic / international
    region = Column(String, nullable=False)
    customs_required = Column(Boolean, default=False)
    restricted_cargo_allowed = Column(Boolean, default=True)
    embargo_active = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
