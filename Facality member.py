import os
import json
import uuid
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional

from models.parking_lot import ParkingLot
from models.parking_spot import ParkingSpot
from models.vehicle import Vehicle
from models.parking_session import ParkingSession
from models.charging_session import ChargingSession
from exceptions import (
    DuplicateEntityException, EntityNotFoundException, SpotUnavailableException,
    IncompatibleSpotException, InvalidSessionOperationException, SpotOccupiedException
)

class FacilityManager:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

    def __init__(self):
        os.makedirs(self.DATA_DIR, exist_ok=True)
        self.lots_file = os.path.join(self.DATA_DIR, "lots.json")
        self.spots_file = os.path.join(self.DATA_DIR, "spots.json")
        self.vehicles_file = os.path.join(self.DATA_DIR, "vehicles.json")
        self.parking_sessions_file = os.path.join(self.DATA_DIR, "parking_sessions.json")
        self.charging_sessions_file = os.path.join(self.DATA_DIR, "charging_sessions.json")

        self._ensure_files()

    def _ensure_files(self):
        for fpath in [self.lots_file, self.spots_file, self.vehicles_file, 
                      self.parking_sessions_file, self.charging_sessions_file]:
            if not os.path.exists(fpath):
                self._atomic_write(fpath, [])

    def _atomic_write(self, filepath: str, data: Any):
        dir_name = os.path.dirname(filepath)
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False) as tf:
            json.dump(data, tf, indent=2)
            temp_name = tf.name
        os.replace(temp_name, filepath)

    def _load_data(self, filepath: str) -> List[Dict[str, Any]]:
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    # --- Lots & Spots CRUD ---
    def add_lot(self, lot_id: str, name: str, location: str) -> ParkingLot:
        lots = [ParkingLot.from_dict(d) for d in self._load_data(self.lots_file)]
        if any(l.lot_id == lot_id for l in lots):
            raise DuplicateEntityException(f"Lot with ID '{lot_id}' already exists.")
        
        lot = ParkingLot(lot_id=lot_id, name=name, location=location)
        lots.append(lot)
        self._atomic_write(self.lots_file, [l.to_dict() for l in lots])
        return lot

    def get_all_lots(self) -> List[Dict[str, Any]]:
        lots = [ParkingLot.from_dict(d) for d in self._load_data(self.lots_file)]
        spots = [ParkingSpot.from_dict(d) for d in self._load_data(self.spots_file)]
        
        result = []
        for lot in lots:
            lot_spots = [s for s in spots if s.lot_id == lot.lot_id]
            total_spots = len(lot_spots)
            occupied_spots = sum(1 for s in lot_spots if s.status == "OCCUPIED")
            available_spots = sum(1 for s in lot_spots if s.status == "AVAILABLE")
            out_of_service = sum(1 for s in lot_spots if s.status == "OUT_OF_SERVICE")

            summary = lot.to_dict()
            summary["occupancy_summary"] = {
                "total": total_spots,
                "available": available_spots,
                "occupied": occupied_spots,
                "out_of_service": out_of_service
            }
            result.append(summary)
        return result

    def add_spot(self, lot_id: str, spot_id: str, spot_type: str, hourly_rate: float, kwh_rate: float = 0.0) -> ParkingSpot:
        lots = [ParkingLot.from_dict(d) for d in self._load_data(self.lots_file)]
        lot = next((l for l in lots if l.lot_id == lot_id), None)
        if not lot:
            raise EntityNotFoundException(f"Lot with ID '{lot_id}' not found.")

        spots = [ParkingSpot.from_dict(d) for d in self._load_data(self.spots_file)]
        if any(s.spot_id == spot_id for s in spots):
            raise DuplicateEntityException(f"Spot with ID '{spot_id}' already exists.")

        spot = ParkingSpot(spot_id=spot_id, lot_id=lot_id, spot_type=spot_type, hourly_rate=hourly_rate, kwh_rate=kwh_rate)
        spots.append(spot)
        self._atomic_write(self.spots_file, [s.to_dict() for s in spots])

        if spot_id not in lot.spot_ids:
            lot.spot_ids.append(spot_id)
            self._atomic_write(self.lots_file, [l.to_dict() for l in lots])

        return spot

    def get_spot(self, spot_id: str) -> ParkingSpot:
        spots = [ParkingSpot.from_dict(d) for d in self._load_data(self.spots_file)]
        spot = next((s for s in spots if s.spot_id == spot_id), None)
        if not spot:
            raise EntityNotFoundException(f"Spot '{spot_id}' not found.")
        return spot

    def update_spot(self, spot_id: str, status: Optional[str] = None, hourly_rate: Optional[float] = None, kwh_rate: Optional[float] = None) -> ParkingSpot:
        spots = [ParkingSpot.from_dict(d) for d in self._load_data(self.spots_file)]
        spot = next((s for s in spots if s.spot_id == spot_id), None)
        if not spot:
            raise EntityNotFoundException(f"Spot '{spot_id}' not found.")

        if spot.status == "OCCUPIED" and status == "OUT_OF_SERVICE":
            raise SpotOccupiedException("Cannot mark occupied spot as OUT_OF_SERVICE.")

        if status:
            if status not in ParkingSpot.STATUSES:
                raise ValueError(f"Invalid status: {status}")
            spot.status = status
        if hourly_rate is not None:
            if hourly_rate <= 0:
                raise ValueError("Hourly rate must be > 0")
            spot.hourly_rate = hourly_rate
        if kwh_rate is not None:
            if spot.spot_type == "EV" and kwh_rate <= 0:
                raise ValueError("kWh rate must be > 0 for EV spot")
            spot.kwh_rate = kwh_rate

        self._atomic_write(self.spots_file, [s.to_dict() for s in spots])
        return spot

    def delete_spot(self, spot_id: str):
        spots = [ParkingSpot.from_dict(d) for d in self._load_data(self.spots_file)]
        spot = next((s for s in spots if s.spot_id == spot_id), None)
        if not spot:
            raise EntityNotFoundException(f"Spot '{spot_id}' not found.")

        if spot.status == "OCCUPIED":
            raise SpotOccupiedException(f"Cannot delete spot '{spot_id}' while it is OCCUPIED.")

        spots = [s for s in spots if s.spot_id != spot_id]
        self._atomic_write(self.spots_file, [s.to_dict() for s in spots])

        lots = [ParkingLot.from_dict(d) for d in self._load_data(self.lots_file)]
        for lot in lots:
            if spot_id in lot.spot_ids:
                lot.spot_ids.remove(spot_id)
        self._atomic_write(self.lots_file, [l.to_dict() for l in lots])

    # --- Vehicles ---
    def register_vehicle(self, license_plate: str, owner_name: str, vehicle_type: str) -> Vehicle:
        vehicles = [Vehicle.from_dict(d) for d in self._load_data(self.vehicles_file)]
        plate_clean = license_plate.upper().strip()
        if any(v.license_plate == plate_clean for v in vehicles):
            raise DuplicateEntityException(f"Vehicle with plate '{plate_clean}' is already registered.")

        veh = Vehicle(license_plate=plate_clean, owner_name=owner_name, vehicle_type=vehicle_type)
        vehicles.append(veh)
        self._atomic_write(self.vehicles_file, [v.to_dict() for v in vehicles])
        return veh

    # --- Session Management ---
    def check_in(self, license_plate: str, lot_id: str, spot_id: Optional[str] = None) -> ParkingSession:
        plate = license_plate.upper().strip()
        vehicles = [Vehicle.from_dict(d) for d in self._load_data(self.vehicles_file)]
        vehicle = next((v for v in vehicles if v.license_plate == plate), None)
        if not vehicle:
            raise EntityNotFoundException(f"Vehicle '{plate}' is not registered.")

        p_sessions = [ParkingSession.from_dict(d) for d in self._load_data(self.parking_sessions_file)]
        if any(s.license_plate == plate and s.status == "ACTIVE" for s in p_sessions):
            raise InvalidSessionOperationException(f"Vehicle '{plate}' is already checked in elsewhere.")

        spots = [ParkingSpot.from_dict(d) for d in self._load_data(self.spots_file)]

        target_spot = None
        if spot_id:
            target_spot = next((s for s in spots if s.spot_id == spot_id and s.lot_id == lot_id), None)
            if not target_spot:
                raise EntityNotFoundException(f"Spot '{spot_id}' not found in Lot '{lot_id}'.")
            if target_spot.status != "AVAILABLE":
                raise SpotUnavailableException(f"Spot '{spot_id}' is currently {target_spot.status}.")
        else:
            available_spots = [s for s in spots if s.lot_id == lot_id and s.status == "AVAILABLE"]
            for s in available_spots:
                if self._is_compatible(vehicle.vehicle_type, s.spot_type):
                    target_spot = s
                    break

            if not target_spot:
                raise SpotUnavailableException(f"No available compatible spots in Lot '{lot_id}'.")

        if not self._is_compatible(vehicle.vehicle_type, target_spot.spot_type):
            raise IncompatibleSpotException(f"Vehicle type '{vehicle.vehicle_type}' is incompatible with spot type '{target_spot.spot_type}'.")

        session_id = f"PS-{uuid.uuid4().hex[:8].upper()}"
        session = ParkingSession(
            session_id=session_id,
            license_plate=plate,
            spot_id=target_spot.spot_id,
            lot_id=lot_id,
            check_in_time=datetime.now().isoformat(),
            status="ACTIVE"
        )
        p_sessions.append(session)
        self._atomic_write(self.parking_sessions_file, [s.to_dict() for s in p_sessions])

        target_spot.status = "OCCUPIED"
        self._atomic_write(self.spots_file, [s.to_dict() for s in spots])

        return session

    def check_out(self, session_id: str) -> Dict[str, Any]:
        p_sessions = [ParkingSession.from_dict(d) for d in self._load_data(self.parking_sessions_file)]
        session = next((s for s in p_sessions if s.session_id == session_id), None)
        if not session:
            raise EntityNotFoundException(f"Parking session '{session_id}' not found.")
        if session.status == "COMPLETED":
            raise InvalidSessionOperationException("Session is already completed.")

        c_sessions = [ChargingSession.from_dict(d) for d in self._load_data(self.charging_sessions_file)]
        active_cs = next((cs for cs in c_sessions if cs.parking_session_id == session_id and cs.status == "ACTIVE"), None)
        if active_cs:
            raise InvalidSessionOperationException("Cannot checkout vehicle while an EV charging session is active. Stop charging first.")

        spots = [ParkingSpot.from_dict(d) for d in self._load_data(self.spots_file)]
        spot = next((s for s in spots if s.spot_id == session.spot_id), None)

        now_iso = datetime.now().isoformat()
        fee = session.calculate_fee(spot.hourly_rate, now_iso)

        session.check_out_time = now_iso
        session.parking_fee = fee
        session.status = "COMPLETED"

        self._atomic_write(self.parking_sessions_file, [s.to_dict() for s in p_sessions])

        if spot:
            spot.status = "AVAILABLE"
            self._atomic_write(self.spots_file, [s.to_dict() for s in spots])

        total_charging_cost = sum(cs.energy_cost for cs in c_sessions if cs.parking_session_id == session_id)

        return {
            "parking_session": session.to_dict(),
            "parking_fee": fee,
            "charging_fee": total_charging_cost,
            "total_due": round(fee + total_charging_cost, 2)
        }

    # --- Charging Session Lifecycle ---
    def start_charging(self, parking_session_id: str, start_meter: float) -> ChargingSession:
        p_sessions = [ParkingSession.from_dict(d) for d in self._load_data(self.parking_sessions_file)]
        p_sess = next((s for s in p_sessions if s.session_id == parking_session_id and s.status == "ACTIVE"), None)
        if not p_sess:
            raise InvalidSessionOperationException(f"No active parking session found for ID '{parking_session_id}'.")

        spots = [ParkingSpot.from_dict(d) for d in self._load_data(self.spots_file)]
        spot = next((s for s in spots if s.spot_id == p_sess.spot_id), None)
        if not spot or spot.spot_type != "EV":
            raise IncompatibleSpotException("Charging sessions can only be started on designated EV spots.")

        c_sessions = [ChargingSession.from_dict(d) for d in self._load_data(self.charging_sessions_file)]
        if any(cs.parking_session_id == parking_session_id and cs.status == "ACTIVE" for cs in c_sessions):
            raise InvalidSessionOperationException("An active charging session is already running for this parking session.")

        cs_id = f"CS-{uuid.uuid4().hex[:8].upper()}"
        c_sess = ChargingSession(
            charging_session_id=cs_id,
            parking_session_id=parking_session_id,
            start_time=datetime.now().isoformat(),
            start_meter=start_meter,
            status="ACTIVE"
        )
        c_sessions.append(c_sess)
        self._atomic_write(self.charging_sessions_file, [cs.to_dict() for cs in c_sessions])
        return c_sess

    def stop_charging(self, parking_session_id: str, end_meter: float) -> ChargingSession:
        c_sessions = [ChargingSession.from_dict(d) for d in self._load_data(self.charging_sessions_file)]
        c_sess = next((cs for cs in c_sessions if cs.parking_session_id == parking_session_id and cs.status == "ACTIVE"), None)
        if not c_sess:
            raise InvalidSessionOperationException("No active charging session found for this parking session.")

        p_sessions = [ParkingSession.from_dict(d) for d in self._load_data(self.parking_sessions_file)]
        p_sess = next((s for s in p_sessions if s.session_id == parking_session_id), None)

        spots = [ParkingSpot.from_dict(d) for d in self._load_data(self.spots_file)]
        spot = next((s for s in spots if s.spot_id == p_sess.spot_id), None)

        cost = c_sess.calculate_cost(end_meter, spot.kwh_rate)

        c_sess.end_time = datetime.now().isoformat()
        c_sess.end_meter = end_meter
        c_sess.energy_cost = cost
        c_sess.status = "COMPLETED"

        self._atomic_write(self.charging_sessions_file, [cs.to_dict() for cs in c_sessions])
        return c_sess

    # --- Searches & Status ---
    def get_vehicle_status(self, license_plate: str) -> Dict[str, Any]:
        plate = license_plate.upper().strip()
        vehicles = [Vehicle.from_dict(d) for d in self._load_data(self.vehicles_file)]
        vehicle = next((v for v in vehicles if v.license_plate == plate), None)
        if not vehicle:
            raise EntityNotFoundException(f"Vehicle '{plate}' not registered.")

        p_sessions = [ParkingSession.from_dict(d) for d in self._load_data(self.parking_sessions_file)]
        active_sess = next((s for s in p_sessions if s.license_plate == plate and s.status == "ACTIVE"), None)

        if not active_sess:
            return {"license_plate": plate, "is_checked_in": False, "active_session": None}

        c_sessions = [ChargingSession.from_dict(d) for d in self._load_data(self.charging_sessions_file)]
        active_cs = next((cs for cs in c_sessions if cs.parking_session_id == active_sess.session_id and cs.status == "ACTIVE"), None)

        return {
            "license_plate": plate,
            "is_checked_in": True,
            "active_session": active_sess.to_dict(),
            "active_charging_session": active_cs.to_dict() if active_cs else None
        }

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        p_sessions = [ParkingSession.from_dict(d) for d in self._load_data(self.parking_sessions_file)]
        return [s.to_dict() for s in p_sessions if s.status == "ACTIVE"]

    def get_vehicle_history(self, license_plate: str) -> List[Dict[str, Any]]:
        plate = license_plate.upper().strip()
        p_sessions = [ParkingSession.from_dict(d) for d in self._load_data(self.parking_sessions_file)]
        return [s.to_dict() for s in p_sessions if s.license_plate == plate]

    # --- Analytics & Facility Report ---
    def generate_report(self) -> str:
        lots = [ParkingLot.from_dict(d) for d in self._load_data(self.lots_file)]
        spots = [ParkingSpot.from_dict(d) for d in self._load_data(self.spots_file)]
        p_sessions = [ParkingSession.from_dict(d) for d in self._load_data(self.parking_sessions_file)]
        c_sessions = [ChargingSession.from_dict(d) for d in self._load_data(self.charging_sessions_file)]

        total_lots = len(lots)
        total_spots = len(spots)

        type_breakdown = {"REGULAR": 0, "HANDICAPPED": 0, "EV": 0}
        status_breakdown = {"AVAILABLE": 0, "OCCUPIED": 0, "OUT_OF_SERVICE": 0}

        for s in spots:
            type_breakdown[s.spot_type] = type_breakdown.get(s.spot_type, 0) + 1
            status_breakdown[s.status] = status_breakdown.get(s.status, 0) + 1

        parking_revenue = sum(s.parking_fee for s in p_sessions)
        charging_revenue = sum(cs.energy_cost for cs in c_sessions)

        completed_sessions = [s for s in p_sessions if s.status == "COMPLETED" and s.check_out_time]
        durations_hrs = []
        for s in completed_sessions:
            start = datetime.fromisoformat(s.check_in_time)
            end = datetime.fromisoformat(s.check_out_time)
            durations_hrs.append((end - start).total_seconds() / 3600.0)

        avg_duration = round(sum(durations_hrs) / len(durations_hrs), 2) if durations_hrs else 0.0

        lot_counts = {}
        for s in p_sessions:
            lot_counts[s.lot_id] = lot_counts.get(s.lot_id, 0) + 1
        busiest_lot = max(lot_counts, key=lot_counts.get) if lot_counts else "N/A"

        spender_map = {}
        for s in p_sessions:
            spender_map[s.license_plate] = spender_map.get(s.license_plate, 0.0) + s.parking_fee
        for cs in c_sessions:
            parent_p = next((p for p in p_sessions if p.session_id == cs.parking_session_id), None)
            if parent_p:
                spender_map[parent_p.license_plate] = spender_map.get(parent_p.license_plate, 0.0) + cs.energy_cost

        top_3 = sorted(spender_map.items(), key=lambda x: x[1], reverse=True)[:3]
        top_3_str = ", ".join([f"{plate} (${amt:.2f})" for plate, amt in top_3]) if top_3 else "N/A"

        active_p = sum(1 for s in p_sessions if s.status == "ACTIVE")
        active_c = sum(1 for cs in c_sessions if cs.status == "ACTIVE")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report_content = f"""==================================================
           FACILITY MANAGEMENT REPORT           
==================================================
Generated At: {now_str}

1. FACILITY OVERVIEW
--------------------
Total Lots: {total_lots}
Total Spots: {total_spots}

2. SPOT BREAKDOWN BY TYPE
-------------------------
Regular: {type_breakdown.get('REGULAR', 0)}
Handicapped: {type_breakdown.get('HANDICAPPED', 0)}
EV Charging: {type_breakdown.get('EV', 0)}

3. SPOT BREAKDOWN BY STATUS
---------------------------
Available: {status_breakdown.get('AVAILABLE', 0)}
Occupied: {status_breakdown.get('OCCUPIED', 0)}
Out of Service: {status_breakdown.get('OUT_OF_SERVICE', 0)}

4. FINANCIAL PERFORMANCE
------------------------
Parking Revenue: ${parking_revenue:.2f}
Charging Revenue: ${charging_revenue:.2f}
Total Revenue: ${parking_revenue + charging_revenue:.2f}

5. USAGE METRICS
----------------
Average Session Duration: {avg_duration} hours
Busiest Lot: {busiest_lot}
Top 3 Spenders: {top_3_str}

6. CURRENT REAL-TIME STATUS
---------------------------
Active Parking Sessions: {active_p}
Active Charging Sessions: {active_c}
==================================================
"""
        filepath = os.path.join(os.path.dirname(__file__), "facility_report.txt")
        with open(filepath, "w") as f:
            f.write(report_content)

        return report_content

    @staticmethod
    def _is_compatible(vehicle_type: str, spot_type: str) -> bool:
        if spot_type == "HANDICAPPED":
            return True
        if spot_type == "EV":
            return vehicle_type == "EV_CAR"
        return True