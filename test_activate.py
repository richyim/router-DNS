import sys
import os

# Ensure Python can find the 'lib' folder
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from lib.activate import RouterConfigManager

def main():
    ini_file = os.path.join(current_dir, 'router.ini')
    
    try:
        manager = RouterConfigManager(ini_file)
        
        # Run the operation
        success, result = manager.apply_config_to_running()
        
        if success:
            print("[+] Configuration merged successfully!")
            print("-" * 40)
            print(result)
            print("-" * 40)
        else:
            # This will print the "not presented" message or connection errors
            print(f"[!] Notice: {result}")
            
    except Exception as e:
        print(f"[!] Script Error: {e}")

if __name__ == "__main__":
    main()