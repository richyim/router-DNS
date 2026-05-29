import os
import sys

PROGRAM_ROOT = r"C:\Users\rich\code\101\ssh_router"

# Configure library dynamic lookup path
LIB_DIRECTORY = os.path.join(PROGRAM_ROOT, "lib")
if LIB_DIRECTORY not in sys.path:
    sys.path.insert(0, LIB_DIRECTORY)

from file_handler import detach_console
from app_controller import launch_app
import dnssync

if __name__ == "__main__":
   dnssync.sync(PROGRAM_ROOT)
   detach_console(__file__)    
   launch_app(PROGRAM_ROOT)
