from typing import Dict, Any, Optional

class ChargingSession:
    def __init__(self, charging_session_id: str, parking_session_id: str, start_time: str,
                 start_meter: float, end_time: Optional[str] = None, 
                 end_meter: Optional[float] = None, energy_cost: float = 0.0, status: str = "ACTIVE"):
        self.charging_session_id = charging_session_id
        self.parking_session_id = parking_session_id
        self.start_time = start_time
        self.start_meter = float(start_meter)
        self.end_time = end_time
        self.end_meter = float(end_meter) if end_meter is not None else None
        self.energy_cost = energy_cost
        self.status = status

    def calculate_cost(self, end_meter_reading: float, spot_kwh_rate: float) -> float:
        if end_meter_reading < self.start_meter:
            raise ValueError("End meter reading cannot be lower than start meter reading.")
        kwh_consumed = end_meter_reading - self.start_meter
        return round(kwh_consumed * spot_kwh_rate, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "charging_session_id": self.charging_session_id,
            "parking_session_id": self.parking_session_id,
            "start_time": self.start_time,
            "start_meter": self.start_meter,
            "end_time": self.end_time,
            "end_meter": self.end_meter,
            "energy_cost": self.energy_cost,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChargingSession":
        return cls(
            charging_session_id=data["charging_session_id"],
            parking_session_id=data["parking_session_id"],
            start_time=data["start_time"],
            start_meter=data["start_meter"],
            end_time=data.get("end_time"),
            end_meter=data.get("end_meter"),
            energy_cost=data.get("energy_cost", 0.0),
            status=data.get("status", "ACTIVE")
        )