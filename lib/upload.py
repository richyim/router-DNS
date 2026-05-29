import os
import socket
import threading
import time
import configparser
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from netmiko import ConnectHandler

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def start_ftp_server(directory, server_container):
    """Starts a simple FTP server on standard port 21."""
    authorizer = DummyAuthorizer()
    authorizer.add_user("cisco", "cisco", directory, perm="elradfmwMT")
    
    handler = FTPHandler
    handler.authorizer = authorizer
    
    server = FTPServer(("0.0.0.0", 21), handler)
    server_container['server'] = server
    server.serve_forever()

def run_upload(program_root, status_callback):
    """Orchestrates file transfer by enforcing a strictly hardcoded file target path."""
    # MANDATORY HARDCODED ASSETS
    HARDCODED_CONF_PATH = r"C:\Users\rich\code\101\ssh_router\ios.conf"
    conf_file = "ios.conf"
    local_dir = r"C:\Users\rich\code\101\ssh_router"
    
    # Load remaining network credential keys from INI
    config_path = os.path.join(program_root, 'router.ini')
    config = configparser.ConfigParser()
    config.read(config_path)
    
    try:
        creds = config['ROUTER_CREDENTIALS']
        router_ip = creds['host']
        username = creds['username']
        password = creds['password']
    except KeyError as e:
        return {"status": "error", "message": f"Missing INI credential mapping: {str(e)}"}

    local_ip = get_local_ip()

    status_callback("[*] Starting FTP server engine...")
    server_container = {'server': None}
    ftp_thread = threading.Thread(target=start_ftp_server, args=(local_dir, server_container), daemon=True)
    ftp_thread.start()
    time.sleep(2)

    device = {
        'device_type': 'cisco_ios',
        'host': router_ip,
        'username': username,
        'password': password,
    }

    try:
        status_callback(f"[*] Connecting to router {router_ip}...")
        with ConnectHandler(**device) as net_connect:
            copy_command = f"copy ftp://cisco:cisco@{local_ip}/{conf_file} flash:{conf_file}"
            status_callback(f"[*] Executing copy: {copy_command}")
            
            output = net_connect.send_command(
                copy_command, 
                expect_string=r"Destination filename",
                strip_prompt=False,
                strip_command=False
            )
            output += net_connect.send_command("\n", expect_string=r"#")
            
            if server_container['server']:
                server_container['server'].close_all()
                
            return {"status": "success", "message": output}
            
    except Exception as e:
        if server_container['server']:
            server_container['server'].close_all()
        return {"status": "error", "message": str(e)}
