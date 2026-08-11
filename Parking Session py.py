import math
from typing import Dict, Any, Optional
from datetime import datetime

class ParkingSession:
    def __init__(self, session_id: str, license_plate: str, spot_id: str, lot_id: str, 
                 check_in_time: str, check_out_time: Optional[str] = None, 
                 parking_fee: float = 0.0, status: str = "ACTIVE"):
        self.session_id = session_id
        self.license_plate = license_plate
        self.spot_id = spot_id
        self.lot_id = lot_id
        self.check_in_time = check_in_time
        self.check_out_time = check_out_time
        self.parking_fee = parking_fee
        self.status = status

    def calculate_fee(self, spot_hourly_rate: float, end_time_iso: str = None) -> float:
        end_dt = datetime.fromisoformat(end_time_iso) if end_time_iso else datetime.now()
        start_dt = datetime.fromisoformat(self.check_in_time)
        
        duration_seconds = max(0, (end_dt - start_dt).total_seconds())
        duration_minutes = duration_seconds / 60.0

        # Grace period: 10 mins or less = free
        if duration_minutes <= 10:
            return 0.0

        total_hours = math.ceil(duration_minutes / 60.0)

        if total_hours <= 24:
            return round(total_hours * spot_hourly_rate, 2)
        else:
            base_fee = 24 * spot_hourly_rate
            overstay_hours = total_hours - 24
            overstay_fee = overstay_hours * (spot_hourly_rate * 1.5)
            return round(base_fee + overstay_fee, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "license_plate": self.license_plate,
            "spot_id": self.spot_id,
            "lot_id": self.lot_id,
            "check_in_time": self.check_in_time,
            "check_out_time": self.check_out_time,
            "parking_fee": self.parking_fee,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParkingSession":
        return cls(
            session_id=data["session_id"],
            license_plate=data["license_plate"],
            spot_id=data["spot_id"],
            lot_id=data["lot_id"],
            check_in_time=data["check_in_time"],
            check_out_time=data.get("check_out_time"),
            parking_fee=data.get("parking_fee", 0.0),
            status=data.get("status", "ACTIVE")
        )