import configparser
import os
from netmiko import ConnectHandler

class RouterManager:
    def __init__(self, ini_path):
        self.ini_path = ini_path
        self.config = self._load_config()
        self.creds = self._get_credentials()

    def _load_config(self):
        """Reads the .ini file."""
        config = configparser.ConfigParser()
        if not os.path.exists(self.ini_path):
            raise FileNotFoundError(f"Configuration file not found at: {self.ini_path}")
        config.read(self.ini_path)
        return config

    def _get_credentials(self):
        """Extracts credentials from the [ROUTER_CREDENTIALS] section."""
        try:
            return {
                'device_type': 'cisco_ios',
                'host': self.config.get('ROUTER_CREDENTIALS', 'host'),
                'username': self.config.get('ROUTER_CREDENTIALS', 'username'),
                'password': self.config.get('ROUTER_CREDENTIALS', 'password'),
                'filename': self.config.get('ROUTER_CREDENTIALS', 'config')
            }
        except Exception as e:
            raise KeyError(f"Missing required fields in router.ini: {e}")

    def delete_file_if_exists(self):
        """Connects to the router and deletes the file if it exists on flash."""
        target_file = self.creds['filename']
        device_params = {
            'device_type': self.creds['device_type'],
            'host': self.creds['host'],
            'username': self.creds['username'],
            'password': self.creds['password'],
        }

        try:
            print(f"[*] Connecting to {device_params['host']}...")
            with ConnectHandler(**device_params) as net_connect:
                # Check existence
                check_output = net_connect.send_command(f"dir flash:{target_file}")
                
                if "No such file" in check_output or "not found" in check_output.lower():
                    print(f"[!] {target_file} not found on flash. Skipping.")
                    return False
                
                print(f"[*] Found {target_file}. Deleting...")
                # Use /force to bypass confirmation prompts
                cmd = f"delete /force flash:{target_file}"
                result = net_connect.send_command(cmd)
                print(f"[+] Success: {result.strip()}")
                return True

        except Exception as e:
            print(f"[!] Netmiko Error: {e}")
            return False