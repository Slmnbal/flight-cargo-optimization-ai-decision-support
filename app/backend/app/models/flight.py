from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database.connection import Base


class Flight(Base):
    __tablename__ = "flights"

    flight_id = Column(Integer, primary_key=True, autoincrement=True)
    flight_number = Column(String, nullable=False, index=True)
    route_id = Column(Integer, ForeignKey("routes.route_id"), nullable=False)
    aircraft_type = Column(String, ForeignKey("aircraft_types.aircraft_type"), nullable=False)
    aircraft_registration = Column(String, nullable=True)
    departure_scheduled = Column(DateTime, nullable=False, index=True)
    arrival_scheduled = Column(DateTime, nullable=False)
    status = Column(String, default="scheduled")
