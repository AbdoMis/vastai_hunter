import os
import subprocess
import json
import time
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# --- CONFIGURATION ---
TARGET_PRICE = float(os.getenv("TARGET_PRICE", "0.11"))
GPU_NAME = os.getenv("GPU_NAME", "RTX_3090")
MAX_DISK_COST_HR = float(os.getenv("MAX_DISK_COST_HR", "0.016"))
IMAGE = os.getenv("IMAGE", "vastai/pytorch:@vastai-automatic-tag")
DISK_SIZE = int(os.getenv("DISK_SIZE", "34"))

# Parse the ignored IDs from the environment variables into a list of integers
ignored_ids_raw = os.getenv("IGNORED_IDS", "")
IGNORED_IDS = [
    int(i.strip()) for i in ignored_ids_raw.split(",") if i.strip()
] if ignored_ids_raw else []

def search_and_rent():
    """Searches for available Vast.ai instances and attempts to rent the best one."""
    sys.stdout.write(f"\r[{datetime.now().strftime('%H:%M:%S')}] Searching for {GPU_NAME} under ${TARGET_PRICE}/h...  ")
    sys.stdout.flush()
    
    # Query prioritizing verified machines with sufficient reliability
    search_query = f"gpu_name={GPU_NAME} dph_total<={TARGET_PRICE} disk_space>=50 rentable=true verified=true reliability>=0.90"
    cmd = ["vastai", "search", "offers", search_query, "--raw"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if not result.stdout.strip():
            return False
            
        offers = json.loads(result.stdout)

        if not offers:
            return False
        
        valid_offers = []
        for offer in offers:
            if offer.get('id') in IGNORED_IDS or offer.get('machine_id') in IGNORED_IDS:
                continue
            
            # Calculate actual hourly disk cost (Storage cost is provided as $/GB/month)
            storage_cost_gb_month = offer.get('storage_cost', 0.15)
            disk_cost_hr = (storage_cost_gb_month * DISK_SIZE) / 730
            
            if disk_cost_hr <= MAX_DISK_COST_HR:
                offer['disk_cost_hr'] = disk_cost_hr
                valid_offers.append(offer)

        offers = valid_offers

        if not offers:
            return False

        # Sort by total price to get the cheapest valid option
        offers = sorted(offers, key=lambda x: x.get('dph_total', x.get('dph_base', 999)))
        best_offer = offers[0]
        offer_id = best_offer['id']
        price = best_offer.get('dph_total', best_offer.get('dph_base', 0))
        disk_cost_hr = best_offer.get('disk_cost_hr', 0)

        print(f"\n\n🎉 FOUND A Verified COMMUNITY MACHINE! Market Offer ID: {offer_id} at ${price:.3f}/h")
        print(f"💾 Storage Price: {DISK_SIZE:.2f} GB Disk @ ${disk_cost_hr:.3f}/hr")
        
        for _ in range(10):
            print("\a", end="", flush=True)
            time.sleep(0.4)

        # Standard Vast.ai Web UI Jupyter arguments
        rent_cmd = [
            "vastai", "create", "instance", str(offer_id), 
            "--image", IMAGE, 
            "--disk", str(DISK_SIZE),
            "--env", '-p 1111:1111 -p 6006:6006 -p 8080:8080 -p 8384:8384 -p 72299:72299 -e OPEN_BUTTON_PORT="1111" -e OPEN_BUTTON_TOKEN="1" -e JUPYTER_DIR="/" -e DATA_DIRECTORY="/workspace/" -e PORTAL_CONFIG="localhost:1111:11111:/:Instance Portal|localhost:8080:18080:/:Jupyter|localhost:8080:8080:/terminals/1:Jupyter Terminal|localhost:8384:18384:/:Syncthing|localhost:6006:16006:/:Tensorboard"',
            "--onstart-cmd", "entrypoint.sh",
            "--jupyter",
            "--direct",
            "--raw"
        ]
        
        print(f"\nExecuting rent command: {' '.join(rent_cmd[:-1])}\n")
        rent_result = subprocess.run(rent_cmd, capture_output=True, text=True)
        
        try:
            rent_data = json.loads(rent_result.stdout)
            
            if "new_contract" in rent_data and rent_data["new_contract"]:
                instance_id = rent_data["new_contract"]
                print(f"✅ Instance successfully rented! Your personal Instance ID is {instance_id}.")
                print("🔍 Monitoring startup progress... (PyTorch is huge, this can take 5-15 mins)")
                
                # Check instance status every 10 seconds for up to 15 minutes
                for _ in range(90): 
                    time.sleep(10)
                    check_cmd = ["vastai", "show", "instances", "--raw"]
                    check_result = subprocess.run(check_cmd, capture_output=True, text=True)
                    
                    try:
                        my_instances = json.loads(check_result.stdout)
                        my_machine = next((inst for inst in my_instances if inst['id'] == instance_id), None)
                        
                        if my_machine:
                            state = my_machine.get('actual_status', 'unknown')
                            status_msg = my_machine.get('status_msg', '') 
                            
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Status: {state.upper()}")
                            if status_msg:
                                print(f"    └─ Message: {status_msg}")
                            
                            # Auto-destroy if the host errors out
                            if "context deadline exceeded" in status_msg or ("error" in state.lower() and "already exists" not in status_msg.lower()):
                                print("\n🚨 HOST ERROR DETECTED: This machine is broken.")
                                print(f"🗑️ Destroying broken instance {instance_id} to save money...")
                                subprocess.run(["vastai", "destroy", "instance", str(instance_id)])
                                print("🔄 Resuming search for a healthy machine in 5 seconds...\n")
                                return False 
                            
                            if state == 'running':
                                print("\n🚀 SUCCESS! The instance is fully booted.")
                                print("Go to your Vast.ai dashboard—the standard 'OPEN' Jupyter button is waiting for you!")
                                return True 
                                
                    except Exception:
                        pass 
                        
                print("\n⚠️ This machine is taking unusually long to boot (>15 minutes).")
                print("Please check the website manually.")
                return True 
                
            else:
                print(f"❌ FAILED TO RENT. Vast.ai error:\n{rent_data}")
                return False
                
        except json.JSONDecodeError:
            error_msg = rent_result.stderr.strip() or rent_result.stdout.strip()
            print(f"❌ FAILED TO RENT. Raw error:\n{error_msg}")
            return False

    except Exception as e:
        print(f"\nAn error occurred: {e}")

    return False

if __name__ == "__main__":
    print("Starting Vast.ai Auto-Renter... Press Ctrl+C to stop.")
    while True:
        success = search_and_rent()
        if success:
            break 
        time.sleep(5)