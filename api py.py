from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
from facility_manager import FacilityManager
from exceptions import ParkingSystemException

app = FastAPI(title="Smart Parking Lot Management API", version="1.0.0")
manager = FacilityManager()

@app.exception_handler(ParkingSystemException)
async def parking_exception_handler(request: Request, exc: ParkingSystemException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "message": exc.message}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": "BadRequest", "message": str(exc)}
    )

# --- Request Models ---
class CreateLotRequest(BaseModel):
    lot_id: str
    name: str
    location: str

class CreateSpotRequest(BaseModel):
    spot_id: str
    spot_type: str
    hourly_rate: float
    kwh_rate: Optional[float] = 0.0

class UpdateSpotRequest(BaseModel):
    status: Optional[str] = None
    hourly_rate: Optional[float] = None
    kwh_rate: Optional[float] = None

class RegisterVehicleRequest(BaseModel):
    license_plate: str
    owner_name: str
    vehicle_type: str

class CheckInRequest(BaseModel):
    license_plate: str
    lot_id: str
    spot_id: Optional[str] = None

class ChargingStartRequest(BaseModel):
    start_meter: float

class ChargingStopRequest(BaseModel):
    end_meter: float

# --- REST Endpoints ---
@app.post("/lots", status_code=201)
def create_lot(req: CreateLotRequest):
    lot = manager.add_lot(req.lot_id, req.name, req.location)
    return lot.to_dict()

@app.get("/lots")
def list_lots():
    return manager.get_all_lots()

@app.post("/lots/{lot_id}/spots", status_code=201)
def add_spot(lot_id: str, req: CreateSpotRequest):
    spot = manager.add_spot(lot_id, req.spot_id, req.spot_type, req.hourly_rate, req.kwh_rate or 0.0)
    return spot.to_dict()

@app.get("/spots/{spot_id}")
def get_spot(spot_id: str):
    return manager.get_spot(spot_id).to_dict()

@app.patch("/spots/{spot_id}")
def update_spot(spot_id: str, req: UpdateSpotRequest):
    spot = manager.update_spot(spot_id, req.status, req.hourly_rate, req.kwh_rate)
    return spot.to_dict()

@app.delete("/spots/{spot_id}")
def delete_spot(spot_id: str):
    manager.delete_spot(spot_id)
    return {"message": f"Spot '{spot_id}' deleted successfully."}

@app.post("/vehicles", status_code=201)
def register_vehicle(req: RegisterVehicleRequest):
    v = manager.register_vehicle(req.license_plate, req.owner_name, req.vehicle_type)
    return v.to_dict()

@app.post("/sessions/check-in", status_code=201)
def check_in(req: CheckInRequest):
    session = manager.check_in(req.license_plate, req.lot_id, req.spot_id)
    return session.to_dict()

@app.post("/sessions/{session_id}/check-out")
def check_out(session_id: str):
    return manager.check_out(session_id)

@app.post("/sessions/{session_id}/charging/start", status_code=201)
def start_charging(session_id: str, req: ChargingStartRequest):
    cs = manager.start_charging(session_id, req.start_meter)
    return cs.to_dict()

@app.post("/sessions/{session_id}/charging/stop")
def stop_charging(session_id: str, req: ChargingStopRequest):
    cs = manager.stop_charging(session_id, req.end_meter)
    return cs.to_dict()

@app.get("/vehicles/{plate}/status")
def vehicle_status(plate: str):
    return manager.get_vehicle_status(plate)

@app.get("/sessions/active")
def active_sessions():
    return manager.get_active_sessions()

@app.get("/vehicles/{plate}/history")
def vehicle_history(plate: str):
    return manager.get_vehicle_history(plate)

@app.get("/report")
def get_report():
    report_str = manager.generate_report()
    return {"status": "Report generated successfully", "report_preview": report_str}