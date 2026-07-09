from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from app.database.connection import Base


class CargoRequest(Base):
    __tablename__ = "cargo_requests"

    request_id = Column(Integer, primary_key=True, autoincrement=True)
    flight_id = Column(Integer, ForeignKey("flights.flight_id"), nullable=False)
    cargo_type = Column(String, default="general")
    weight_kg = Column(Float, nullable=False)
    volume_m3 = Column(Float, nullable=False)
    requires_temperature_control = Column(Boolean, default=False)
    priority_class = Column(String, default="spot")  # contract / spot
    revenue = Column(Float, nullable=False)
    booking_cutoff_hours = Column(Integer, default=24)
    status = Column(String, default="pending")  # pending / accepted / rejected
