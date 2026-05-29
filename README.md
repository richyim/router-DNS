# router-DNS
# Router-DNS Sync Tool

An interactive, Excel-like desktop application designed to pull, edit, and safely sync DNS (`ip host`) table configurations on Cisco IOS routers. The application features an integrated, thread-safe automated pipeline that extracts active records, presents them in an embedded GUI spreadsheet, and deploys updates seamlessly via an isolated FTP background engine.

---

## 🚀 Key Features

* **Automated Data Fetching**: Automatically connects via SSH to your Cisco router on boot to extract all current `ip host` records.
* **Interactive Spreadsheet View**: Modifies names, adds elements, or purges cells using dedicated row action widgets (`⬆️`, `⬇️`, `❌`) with dynamic tooltips.
* **Safe Input Persistence**: Automatically saves edits on focus-out or layout key movements to prevent typing data loss.
* **Pre-Deployment Text Verification**: Compiles changes into a Cisco-compatible `ios.conf` profile and previews it inside a text modal before touching the live router hardware.
* **Multi-Threaded FTP Pipeline**: Clears old instances using `delete /force`, launches a temporary internal FTP server, and copies files directly to flash memory without freezing the app window.

---

## 📂 System Architecture

The application repository is organized into a clean component layer:

```text
C:\Users\rich\code\101\ssh_router\
├── main.py               # Main entry point and subprocess detacher
├── router.ini            # Configuration and credential storage asset
├── running.csv           # Storage backup for active router DNS records
├── modified.csv          # Export container for modified spreadsheet changes
├── ios.conf              # Compiled Cisco IOS XE configuration script
├── requirements.txt      # Virtual environment package definitions
└── lib/                  # Application system core libraries
    ├── app_controller.py # Interface lifecycle state handler
    ├── table_view.py     # Custom ExcelGrid spreadsheet framework
    ├── file_handler.py   # File system reader/writer utility layer
    ├── gen_conf.py       # Configuration compiler (adds and updates differentials)
    ├── del_old_script.py # Secure SSH flash-cleanup worker
    └── upload.py         # Multi-threaded background FTP transfer loop
```

---

## 🛠️ Installation & Setup

Set up a clean local Python virtual environment to manage dependencies securely.

1. **Clone and navigate to the project directory**:
   ```cmd
   cd C:\Users\rich\code\101\ssh_router
   ```

2. **Initialize and activate the virtual environment**:
   ```cmd
   python -m venv venv
   vnev\Scripts\activate
   ```

3. **Install required packages**:
   ```cmd
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration Setup (`router.ini`)

Before running the application, make sure to add your specific hardware profile parameters inside your root workspace directory folder named `router.ini`:

```ini
[ROUTER_CREDENTIALS]
host = < ip address of the router >
username = admin
password = YourSecretPassword Here
running = running.csv
modified = modified.csv
config = ios.conf
```

---

## 💻 Workflow Usage Guide

Execute `python main.py` inside your environment terminal prompt to handle network tasks:

1. **Boot Loop**: The program executes `dnssync.sync` on boot to extract your active `ip host` configurations directly into `running.csv`. It then detaches your console to launch the window view cleanly.
2. **Spreadsheet Edits**: Click cells directly to update IP strings or map new rows cleanly.
3. **Save**: Click **System > Save** to burn your current row edits natively into `modified.csv`.
4. **Deploy**: Click **System > Deploy** to review the compiled line differentials. Clicking **✔️ Confirm Deployment** purges stale files from the router's flash memory and pushes the fresh config via the FTP server thread.
5. **Activate**: Click **System > Activate** to safely load the file from flash memory into the router's `running-config` in real time.
