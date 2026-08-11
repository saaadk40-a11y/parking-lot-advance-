from typing import Dict, Any
from exceptions import InvalidRateException

class ParkingSpot:
    TYPES = ["REGULAR", "HANDICAPPED", "EV"]
    STATUSES = ["AVAILABLE", "OCCUPIED", "OUT_OF_SERVICE"]

    def __init__(self, spot_id: str, lot_id: str, spot_type: str, status: str = "AVAILABLE", hourly_rate: float = 5.0, kwh_rate: float = 0.0):
        if spot_type not in self.TYPES:
            raise ValueError(f"Invalid spot type: {spot_type}")
        if status not in self.STATUSES:
            raise ValueError(f"Invalid spot status: {status}")
        if hourly_rate <= 0:
            raise InvalidRateException("Hourly rate must be greater than zero.")
        if spot_type == "EV" and kwh_rate <= 0:
            raise InvalidRateException("kWh rate for EV spot must be greater than zero.")

        self.spot_id = spot_id
        self.lot_id = lot_id
        self.spot_type = spot_type
        self.status = status
        self.hourly_rate = float(hourly_rate)
        self.kwh_rate = float(kwh_rate) if spot_type == "EV" else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spot_id": self.spot_id,
            "lot_id": self.lot_id,
            "spot_type": self.spot_type,
            "status": self.status,
            "hourly_rate": self.hourly_rate,
            "kwh_rate": self.kwh_rate
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParkingSpot":
        return cls(
            spot_id=data["spot_id"],
            lot_id=data["lot_id"],
            spot_type=data["spot_type"],
            status=data.get("status", "AVAILABLE"),
            hourly_rate=data.get("hourly_rate", 5.0),
            kwh_rate=data.get("kwh_rate", 0.0)
        )