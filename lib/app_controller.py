import os
import configparser
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from file_handler import FileOperations
from table_view import ExcelGrid

class ExcelApp:
    def __init__(self, root, program_root):
        self.root = root
        self.program_root = program_root
        self.root.title("Excel-like CSV Editor")
        self.root.geometry("850x550")

        self.file_ops = FileOperations()
        self.running_file, self.modified_file, _ = self.load_ini_config()
        
        # Strictly hardcoded local file asset tracking location
        self.config_file = r"C:\Users\rich\code\101\ssh_router\ios.conf"

        self.lbl = tk.Label(root, text="No file loaded.", bg="#f0f0f0", font=("Arial", 10, "italic"), anchor="w")
        self.lbl.pack(fill="x", side="top", padx=10, pady=5)

        self.grid = ExcelGrid(root, self.file_ops, self.update_file_label)
        self.grid.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_menu()
        self.auto_load_running()

    def load_ini_config(self):
        ini_path = os.path.join(self.program_root, "router.ini")
        running = "running.csv"
        modified = "modified.csv"
        config_file = "ios.conf"

        if os.path.exists(ini_path):
            config = configparser.ConfigParser()
            config.read(ini_path)
            if "ROUTER_CREDENTIALS" in config:
                running = config["ROUTER_CREDENTIALS"].get("running", running)
                modified = config["ROUTER_CREDENTIALS"].get("modified", modified)
        return running, modified, config_file

    def auto_load_running(self):
        target_path = os.path.join(self.program_root, self.running_file)
        if os.path.exists(target_path):
            data, headers = self.file_ops.read_csv_from_path(target_path)
            if data and headers:
                self.grid.headers = headers
                self.grid.data_rows = data
                self.grid.build_ui()
                self.update_file_label(self.file_ops.current_file)
        else:
            self.lbl.config(text=f"Default configuration '{self.running_file}' not found.", fg="red")

    def create_menu(self):
        menubar = tk.Menu(self.root)
        system_menu = tk.Menu(menubar, tearoff=0)
        system_menu.add_command(label="Cancel Change", command=self.menu_cancel_change)
        system_menu.add_command(label="Save", command=self.menu_save)
        system_menu.add_command(label="Deploy", command=self.menu_deploy)
        system_menu.add_separator()
        system_menu.add_command(label="Activate", command=self.menu_activate)
        system_menu.add_command(label="Quit", command=self.root.quit)
        menubar.add_cascade(label="System", menu=system_menu)
        self.root.config(menu=menubar)

    def update_file_label(self, path):
        self.lbl.config(text=f"Active File: {path}", fg="green")

    def menu_cancel_change(self):
        self.grid.close_editor()
        self.auto_load_running()

    def menu_save(self):
        self.grid.close_editor()
        target_path = os.path.join(self.program_root, self.modified_file)
        if self.file_ops.save_csv_direct(self.grid.get_all_data(), target_path):
            self.update_file_label(self.file_ops.current_file)
    def menu_deploy(self):
        """Generates fresh config, then opens a text preview window targeting ios.conf."""
        self.grid.close_editor()
        
        try:
            import gen_conf
            ini_file_path = os.path.join(self.program_root, "router.ini")
            build_result = gen_conf.generate_ios_config(ini_file_path)
            
            if build_result["status"] == "error":
                messagebox.showerror("Generation Error", f"Could not compile new layout data:\n{build_result['message']}")
                return
        except Exception as gen_err:
            messagebox.showerror("System Error", f"Failed to run configuration generator engine:\n{str(gen_err)}")
            return
        
        if not os.path.exists(self.config_file):
            messagebox.showerror("Error", f"Hardcoded configuration file not found at:\n{self.config_file}")
            return

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                conf_content = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Could not read config file:\n{str(e)}")
            return

        preview_win = tk.Toplevel(self.root)
        preview_win.title("Deploy Preview - ios.conf")
        preview_win.geometry("600x500")
        preview_win.transient(self.root)
        preview_win.grab_set()

        lbl_title = tk.Label(preview_win, text="Review hardcoded ios.conf payload contents before upload:", 
                             font=("Arial", 10, "bold"), anchor="w", pady=5)
        lbl_title.pack(fill="x", padx=10)

        txt_area = scrolledtext.ScrolledText(preview_win, wrap="word", font=("Courier New", 10))
        txt_area.insert("1.0", conf_content)
        txt_area.config(state="disabled")
        txt_area.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = tk.Frame(preview_win, pady=10)
        btn_frame.pack(fill="x")

        def on_confirm():
            preview_win.destroy()
            self.start_background_upload()

        btn_confirm = tk.Button(btn_frame, text="✔️ Confirm Deployment", font=("Arial", 10, "bold"), 
                               bg="#d4edda", fg="#155724", padx=10, command=on_confirm)
        btn_confirm.pack(side="right", padx=15)

        btn_cancel = tk.Button(btn_frame, text="❌ Cancel", font=("Arial", 10), 
                              bg="#f8d7da", fg="#721c24", padx=10, command=preview_win.destroy)
        btn_cancel.pack(side="right", padx=5)

    def update_status_label(self, message):
        self.root.after(0, lambda: self.lbl.config(text=message, fg="blue"))

    def start_background_upload(self):
        """Spawns an execution thread to delete the old file and then upload the new one."""
        self.lbl.config(text="Initializing deployment pipeline...", fg="orange")
        
        def thread_target():
            # 1. EXECUTE THE DELETE OPERATION FIRST via del_old_script
            self.update_status_label("[*] Connecting to delete stale configuration files...")
            try:
                from del_old_script import RouterManager
                ini_file_path = os.path.join(self.program_root, "router.ini")
                
                router_manager = RouterManager(ini_file_path)
                delete_status = router_manager.delete_file_if_exists()
                
                if delete_status:
                    self.update_status_label("[+] Stale flash memory profile cleared successfully.")
                else:
                    self.update_status_label("[*] Target file not found on flash. Proceeding clean.")
            except Exception as delete_error:
                self.update_status_label(f"[!] Warning during file deletion loop: {str(delete_error)}")
            
            import time
            time.sleep(1)

            # 2. RUN TRANSFER AND UPLOAD PIPELINE via upload
            self.update_status_label("[*] Initializing FTP upload engine...")
            import upload
            result = upload.run_upload(self.program_root, self.update_status_label)
            
            if result["status"] == "success":
                self.root.after(0, lambda: messagebox.showinfo("Deployment Success", "Old file deleted and new configuration uploaded successfully!"))
                self.root.after(0, lambda: self.lbl.config(text="Deployment successful.", fg="darkgreen"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Deployment Failure", f"Upload operation failed:\n{result['message']}"))
                self.root.after(0, lambda: self.lbl.config(text="Deployment failed.", fg="red"))

        worker = threading.Thread(target=thread_target, daemon=True)
        worker.start()

    def menu_activate(self):
        """Spawns a thread to trigger configuration merging via activate.py without locking the UI."""
        self.grid.close_editor()
        self.lbl.config(text="Initializing activation sequence...", fg="orange")
        
        def activation_thread_target():
            ini_file_path = os.path.join(self.program_root, "router.ini")
            self.update_status_label("[*] Connecting to router for activation task...")
            
            try:
                from activate import RouterConfigManager
                manager = RouterConfigManager(ini_file_path)
                
                success, result = manager.apply_config_to_running()
                
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Activation Success", f"Configuration merged successfully!\n\nRouter Log:\n{result}"))
                    self.root.after(0, lambda: self.lbl.config(text="Activation complete. Config running.", fg="darkgreen"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Activation Failed", f"Notice: {result}"))
                    self.root.after(0, lambda: self.lbl.config(text="Activation aborted.", fg="red"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("System Error", f"Failed to run activation script:\n{str(e)}"))
                self.root.after(0, lambda: self.lbl.config(text="Activation module failed.", fg="red"))

        worker = threading.Thread(target=activation_thread_target, daemon=True)
        worker.start()


def launch_app(program_root):
    """Initializes and runs the primary GUI application context."""
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.Treeview", rowheight=25, font=("Arial", 10))
    style.configure("Custom.Treeview.Heading", font=("Arial", 10, "bold"))
    
    app = ExcelApp(root, program_root)
    root.mainloop()
