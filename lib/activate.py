import configparser
import os
from netmiko import ConnectHandler

class RouterConfigManager:
    def __init__(self, ini_path):
        self.ini_path = ini_path
        if not os.path.exists(ini_path):
            raise FileNotFoundError(f"INI file not found: {ini_path}")
        
        self.config = configparser.ConfigParser()
        self.config.read(ini_path)
        
        self.host = self.config.get('ROUTER_CREDENTIALS', 'host')
        self.username = self.config.get('ROUTER_CREDENTIALS', 'username')
        self.password = self.config.get('ROUTER_CREDENTIALS', 'password')
        self.config_file = self.config.get('ROUTER_CREDENTIALS', 'config')

    def apply_config_to_running(self):
        """Checks for file existence on flash, then copies to running-config."""
        device = {
            'device_type': 'cisco_ios',
            'host': self.host,
            'username': self.username,
            'password': self.password,
        }

        try:
            print(f"[*] Connecting to {self.host}...")
            with ConnectHandler(**device) as net_connect:
                
                # --- NEW: Check if file exists on flash ---
                print(f"[*] Checking for flash:{self.config_file}...")
                check_cmd = f"dir flash:{self.config_file}"
                check_output = net_connect.send_command(check_cmd)
                
                if "No such file" in check_output or "not found" in check_output.lower():
                    # Return False and a custom message
                    return False, f"The file '{self.config_file}' is not presented on the router flash."

                # --- Proceed with Copy if file exists ---
                print(f"[*] File found. Executing: copy flash:{self.config_file} running-config")
                
                output = net_connect.send_command(
                    f"copy flash:{self.config_file} running-config",
                    expect_string=r"Destination filename",
                    strip_prompt=False,
                    strip_command=False
                )
                
                output += net_connect.send_command(
                    "\n", 
                    expect_string=r"#", 
                    delay_factor=2
                )
                
                return True, output

        except Exception as e:
            return False, f"Connection Error: {str(e)}"