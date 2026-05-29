import csv
import configparser
import os

def get_csv_dict(filepath):
    """Reads CSV and returns a dictionary {hostname: ip}."""
    entries = {}
    if not os.path.exists(filepath):
        return entries
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2:
                entries[row[0].strip()] = row[1].strip()
    return entries

def generate_ios_config(ini_path):
    """
    Reads paths from router.ini and generates the Cisco configuration file.
    Accepts ini_path as a parameter to keep the code entirely portable.
    """
    config = configparser.ConfigParser()
    if not os.path.exists(ini_path):
        return {"status": "error", "message": f"ini file not found at {ini_path}"}
        
    config.read(ini_path)
    
    try:
        base_dir = os.path.dirname(ini_path)
        running_dns_records = config.get('ROUTER_CREDENTIALS', 'running')
        modified_dns_records = config.get('ROUTER_CREDENTIALS', 'modified')
        
        config_out_name = config.get('ROUTER_CREDENTIALS', 'config')
        
        file_set1_path = os.path.join(base_dir, modified_dns_records)  # Mandate, modified
        file_set2_path = os.path.join(base_dir, running_dns_records)  # Previous, running
        output_path = os.path.join(base_dir, config_out_name)
    except Exception as e:
        return {"status": "error", "message": f"Error reading ini: {str(e)}"}

    # Read both files into dictionaries {hostname: ip}
    dict1 = get_csv_dict(file_set1_path)
    dict2 = get_csv_dict(file_set2_path)

    ios_commands = []

    # Process Set 1: Create/Update all mandate entries
    ios_commands.append("! --- Apply Current Mandate (Adds and Updates) ---")
    for hostname, ip in sorted(dict1.items()):
        ios_commands.append(f"ip host {hostname} {ip}")

    # Process Deletions: Only if the HOSTNAME is gone from Set 1
    removed_hostnames = set(dict2.keys()) - set(dict1.keys())
    
    if removed_hostnames:
        ios_commands.append("! --- Remove Retired Hosts ---")
        for hostname in sorted(removed_hostnames):
            ios_commands.append(f"no ip host {hostname}")

    # ---- UPDATED FILE-WRITING LOGIC FOR CISCO IOS COMPATIBILITY ----
    try:
        # Enforce explicit Windows-style carriage returns natively (\r\n)
        with open(output_path, 'w', newline='\r\n', encoding='utf-8') as f:
            # Write all generated command elements line-by-line
            for cmd in ios_commands:
                f.write(cmd + "\n")
            
            # Append mandatory structural termination tags with a clean trailing baseline buffer
            f.write("end\n\n")
            
        return {
            "status": "success", 
            "message": f"Config generated at {output_path}",
            "active": len(dict1),
            "deleted": len(removed_hostnames)
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to write file: {str(e)}"}
