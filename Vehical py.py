from typing import Dict, Any
from datetime import datetime

class Vehicle:
    TYPES = ["CAR", "MOTORCYCLE", "EV_CAR"]

    def __init__(self, license_plate: str, owner_name: str, vehicle_type: str, registered_at: str = None):
        if vehicle_type not in self.TYPES:
            raise ValueError(f"Invalid vehicle type: {vehicle_type}")
        self.license_plate = license_plate.upper().strip()
        self.owner_name = owner_name
        self.vehicle_type = vehicle_type
        self.registered_at = registered_at or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "license_plate": self.license_plate,
            "owner_name": self.owner_name,
            "vehicle_type": self.vehicle_type,
            "registered_at": self.registered_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Vehicle":
        return cls(
            license_plate=data["license_plate"],
            owner_name=data["owner_name"],
            vehicle_type=data["vehicle_type"],
            registered_at=data.get("registered_at")
        )