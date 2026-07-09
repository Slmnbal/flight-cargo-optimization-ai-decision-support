"""
Tüm modelleri burada import ediyoruz ki, hangi dosya çalıştırılırsa çalıştırılsın
(seed_data.py, main.py, testler...) SQLAlchemy'nin Base.metadata'sı tüm tabloları
tanısın. Bu import olmadan, yeni eklenen bir model bazı giriş noktalarında
"no such table" hatasına yol açabilir (tam da az önce yaşadığımız gibi).
"""
from app.models.airport import Airport
from app.models.aircraft_type import AircraftType
from app.models.route import Route
from app.models.flight import Flight
from app.models.cargo_request import CargoRequest
from app.models.optimization_result import OptimizationResult

__all__ = [
    "Airport",
    "AircraftType",
    "Route",
    "Flight",
    "CargoRequest",
    "OptimizationResult",
]
