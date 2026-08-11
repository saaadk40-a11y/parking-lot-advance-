from typing import List, Dict, Any

class ParkingLot:
    def __init__(self, lot_id: str, name: str, location: str, spot_ids: List[str] = None):
        self.lot_id = lot_id
        self.name = name
        self.location = location
        self.spot_ids = spot_ids if spot_ids is not None else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lot_id": self.lot_id,
            "name": self.name,
            "location": self.location,
            "spot_ids": self.spot_ids
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParkingLot":
        return cls(
            lot_id=data["lot_id"],
            name=data["name"],
            location=data["location"],
            spot_ids=data.get("spot_ids", [])
        )