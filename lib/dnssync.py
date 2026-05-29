import os
import csv
import configparser
from netmiko import ConnectHandler

def collect_router_hosts(router_config, csv_path):
    """Connects to a router and saves hosts directly to a single <filename>."""
    cisco_router = {
        "device_type": "cisco_ios",
        "host": router_config["host"],
        "username": router_config.get("username", "admin"),
        "password": router_config["password"],
    }

    command = "show run | include ^ip host."
    parsed_records = []
    
    try:
        connection = ConnectHandler(**cisco_router)
        raw_output = connection.send_command(command)
        connection.disconnect()
        
        for line in raw_output.splitlines():
            parts = line.strip().split()
            if len(parts) >= 4 and parts[0] == 'ip' and parts[1] == 'host':
                parsed_records.append([parts[2], parts[3]])
    except Exception as e:
        return {"status": "error", "message": f"Network Connection Failed: {str(e)}"}

    if not parsed_records:
        return {"status": "success", "message": "No host entries found.", "count": 0}

    # Enforce writing strictly to the single target file path
    target_file = csv_path

    try:
        with open(target_file, mode="w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(parsed_records)
        return {"status": "success", "message": f"Saved to {target_file}", "count": len(parsed_records)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to save file: {str(e)}"}

def sync(program_root):
    """Orchestrates the entire configuration parsing and router synchronization pipeline."""
    print("--- Calling Collector ---")
    ini_path = os.path.join(program_root, "router.ini")
    
    if not os.path.exists(ini_path):
        print(f"o_O Error: Configuration file not found at {ini_path}")
        return

    config = configparser.ConfigParser()
    config.read(ini_path)
    
    try:
        router_config = dict(config["ROUTER_CREDENTIALS"])
    except KeyError:
        print("o_O Error: Missing [ROUTER_CREDENTIALS] section in router.ini")
        return

    filename = router_config.get("running", "running.csv").strip()
    if not filename.lower().endswith(".csv"):
        filename += ".csv"

    full_csv_path = os.path.join(program_root, filename)

    print(f"Target Router IP : {router_config['host']}")
    print(f"Base Output File : {full_csv_path}")
    print("\nWorking in progress...")

    result = collect_router_hosts(router_config, full_csv_path)

    if result["status"] == "success":
        print(f"(^_^)  Success! {result['message']} (Count: {result['count']})")
    else:
        print(f"o_O Error encountered: {result['message']}")
