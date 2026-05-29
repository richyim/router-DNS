import os
import sys

PROGRAM_ROOT = r"C:\Users\rich\code\101\ssh_router"

# Configure library dynamic lookup path
LIB_DIRECTORY = os.path.join(PROGRAM_ROOT, "lib")
if LIB_DIRECTORY not in sys.path:
    sys.path.insert(0, LIB_DIRECTORY)

import dnssync

def main():
    # Execute the fully bundled routine
    dnssync.sync(PROGRAM_ROOT)

if __name__ == "__main__":
    main()
