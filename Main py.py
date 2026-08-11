import sys
import json
from facility_manager import FacilityManager
from exceptions import ParkingSystemException

def print_menu():
    print("\n" + "="*50)
    print(" SMART PARKING LOT MANAGEMENT SYSTEM ")
    print("="*50)
    print("1. Add Parking Lot")
    print("2. Add Parking Spot")
    print("3. View All Lots & Occupancy")
    print("4. Register Vehicle")
    print("5. Check-In Vehicle")
    print("6. Check-Out Vehicle")
    print("7. Start EV Charging Session")
    print("8. Stop EV Charging Session")
    print("9. Search Vehicle Status")
    print("10. View Active Sessions")
    print("11. View Vehicle Session History")
    print("12. Update Spot Status / Metadata")
    print("13. Delete Parking Spot")
    print("14. Generate Facility Report")
    print("15. Exit")
    print("="*50)

def main():
    fm = FacilityManager()

    while True:
        print_menu()
        choice = input("Enter your choice (1-15): ").strip()

        try:
            if choice == "1":
                lot_id = input("Enter Lot ID: ").strip()
                name = input("Enter Lot Name: ").strip()
                location = input("Enter Location: ").strip()
                fm.add_lot(lot_id, name, location)
                print(f"[SUCCESS] Parking Lot '{name}' added.")

            elif choice == "2":
                lot_id = input("Enter Lot ID: ").strip()
                spot_id = input("Enter Spot ID: ").strip()
                spot_type = input("Enter Spot Type (REGULAR/HANDICAPPED/EV): ").strip().upper()
                hourly_rate = float(input("Enter Hourly Rate ($): "))
                kwh_rate = 0.0
                if spot_type == "EV":
                    kwh_rate = float(input("Enter kWh Rate ($): "))
                fm.add_spot(lot_id, spot_id, spot_type, hourly_rate, kwh_rate)
                print(f"[SUCCESS] Spot '{spot_id}' created.")

            elif choice == "3":
                lots = fm.get_all_lots()
                for lot in lots:
                    occ = lot["occupancy_summary"]
                    print(f"\nLot: {lot['name']} ({lot['lot_id']}) | Location: {lot['location']}")
                    print(f"   Total: {occ['total']} | Available: {occ['available']} | Occupied: {occ['occupied']} | Out of Service: {occ['out_of_service']}")

            elif choice == "4":
                plate = input("Enter License Plate: ").strip()
                owner = input("Enter Owner Name: ").strip()
                vtype = input("Enter Vehicle Type (CAR/MOTORCYCLE/EV_CAR): ").strip().upper()
                fm.register_vehicle(plate, owner, vtype)
                print(f"[SUCCESS] Vehicle '{plate}' registered.")

            elif choice == "5":
                plate = input("Enter License Plate: ").strip()
                lot_id = input("Enter Lot ID: ").strip()
                spot_id = input("Enter Spot ID (leave blank to auto-assign): ").strip()
                session = fm.check_in(plate, lot_id, spot_id if spot_id else None)
                print(f"[SUCCESS] Checked in! Session ID: {session.session_id}, Assigned Spot: {session.spot_id}")

            elif choice == "6":
                sess_id = input("Enter Session ID: ").strip()
                res = fm.check_out(sess_id)
                print(f"[SUCCESS] Checked out!")
                print(f"   Parking Fee: ${res['parking_fee']:.2f}")
                print(f"   Charging Fee: ${res['charging_fee']:.2f}")
                print(f"   Total Due: ${res['total_due']:.2f}")

            elif choice == "7":
                sess_id = input("Enter Active Parking Session ID: ").strip()
                start_meter = float(input("Enter Start Meter Reading (kWh): "))
                cs = fm.start_charging(sess_id, start_meter)
                print(f"[SUCCESS] EV Charging started! Charging Session ID: {cs.charging_session_id}")

            elif choice == "8":
                sess_id = input("Enter Active Parking Session ID: ").strip()
                end_meter = float(input("Enter End Meter Reading (kWh): "))
                cs = fm.stop_charging(sess_id, end_meter)
                print(f"[SUCCESS] Charging stopped! Energy Cost: ${cs.energy_cost:.2f}")

            elif choice == "9":
                plate = input("Enter License Plate: ").strip()
                status = fm.get_vehicle_status(plate)
                print("\nSTATUS DETAILS:")
                print(json.dumps(status, indent=2))

            elif choice == "10":
                active = fm.get_active_sessions()
                print(f"\nActive Sessions Count: {len(active)}")
                for a in active:
                    print(f"   Session ID: {a['session_id']} | Plate: {a['license_plate']} | Spot: {a['spot_id']}")

            elif choice == "11":
                plate = input("Enter License Plate: ").strip()
                history = fm.get_vehicle_history(plate)
                print(f"\nFound {len(history)} session(s):")
                for h in history:
                    print(f"   [{h['status']}] Session: {h['session_id']} | Spot: {h['spot_id']} | Fee: ${h['parking_fee']}")

            elif choice == "12":
                spot_id = input("Enter Spot ID to update: ").strip()
                st = input("Enter New Status (AVAILABLE/OUT_OF_SERVICE or leave blank): ").strip()
                hr = input("Enter New Hourly Rate (or leave blank): ").strip()
                kr = input("Enter New kWh Rate (or leave blank): ").strip()

                fm.update_spot(
                    spot_id,
                    status=st if st else None,
                    hourly_rate=float(hr) if hr else None,
                    kwh_rate=float(kr) if kr else None
                )
                print(f"[SUCCESS] Spot '{spot_id}' updated.")

            elif choice == "13":
                spot_id = input("Enter Spot ID to delete: ").strip()
                fm.delete_spot(spot_id)
                print(f"[SUCCESS] Spot '{spot_id}' deleted.")

            elif choice == "14":
                report = fm.generate_report()
                print("\n" + report)

            elif choice == "15":
                print("Exiting Smart Parking Lot System. Goodbye!")
                sys.exit(0)

            else:
                print("[ERROR] Invalid choice. Please enter a number between 1 and 15.")

        except ParkingSystemException as e:
            print(f"\n[BUSINESS ERROR ({e.__class__.__name__})]: {e.message}")
        except Exception as e:
            print(f"\n[SYSTEM ERROR]: {str(e)}")

if __name__ == "__main__":
    main()