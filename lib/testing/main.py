import sys
import os

PROGRAM_ROOT = r"C:\Users\rich\code\101\ssh_router"

# Configure library dynamic lookup path
LIB_DIRECTORY = os.path.join(PROGRAM_ROOT, "lib")
if LIB_DIRECTORY not in sys.path:
    sys.path.insert(0, LIB_DIRECTORY)


from del_old_script import RouterManager

def main():
    # Define the path to your ini file
    ini_file = r'C:\Users\rich\code\101\ssh_router\router.ini'
    
    try:
        # Initialize the library
        router = RouterManager(ini_file)
        
        # Execute the delete operation
        status = router.delete_file_if_exists()
        
        if status:
            print("Operation completed successfully.")
        else:
            print("Operation finished with no changes or errors.")
            
    except Exception as e:
        print(f"Main Execution Error: {e}")

if __name__ == "__main__":
    main()