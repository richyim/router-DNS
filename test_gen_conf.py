import os
import sys

# Define your portable environment root path variable
PROGRAM_ROOT = r"C:\Users\rich\code\101\ssh_router"

# Register the local 'lib' directory dynamically to python runtime paths
LIB_DIRECTORY = os.path.join(PROGRAM_ROOT, "lib")
if LIB_DIRECTORY not in sys.path:
    sys.path.insert(0, LIB_DIRECTORY)

# Import your library module
import gen_conf

def run_pipeline():
    ini_filepath = os.path.join(PROGRAM_ROOT, "router.ini")
    
    print("🔄 Running configuration generator task...")
    
    # Call the library function and capture its response payload
    result = gen_conf.generate_ios_config(ini_filepath)
    
    if result["status"] == "success":
        print(f"✅ {result['message']}")
        print(f"📊 Active Nodes: {result['active']} | Deleted Nodes: {result['deleted']}")
    else:
        print(f"❌ Pipeline Blocked: {result['message']}")

if __name__ == "__main__":
    run_pipeline()
