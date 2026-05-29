import os
import csv
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

def detach_console(main_file_path):
    if "--detached" not in sys.argv:
        script_path = os.path.abspath(main_file_path)
        command = [sys.executable, script_path, "--detached"]

        if sys.platform == "win32":
            creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            subprocess.Popen(command, creationflags=creationflags, close_fds=True)
        else:
            with open(os.devnull, 'w') as devnull:
                subprocess.Popen(
                    command,
                    stdout=devnull,
                    stderr=devnull,
                    start_new_session=True,
                    close_fds=True
                )
        print("Application launched in the background. Terminal released.")
        sys.exit(0)

class FileOperations:
    def __init__(self):
        self.current_file = None

    def read_csv_from_path(self, path):
        try:
            with open(path, newline='', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            if not rows:
                return [["" for _ in range(5)] for _ in range(15)], ["A", "B", "C", "D", "E"]

            max_cols = max(len(r) for r in rows)
            headers = [f"Col {i+1}" for i in range(max_cols)]
            padded_rows = [r + [""] * (max_cols - len(r)) for r in rows]
            self.current_file = path
            return padded_rows, headers
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file natively:\n{str(e)}")
            return None, None

    def open_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if not path:
            return None, None
        return self.read_csv_from_path(path)

    def save_csv_direct(self, data, target_path):
        """Writes current grid rows directly to an explicitly forced path string."""
        try:
            with open(target_path, mode="w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(data)
            self.current_file = target_path
            messagebox.showinfo("Success", f"File saved directly to:\n{target_path}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file directly:\n{str(e)}")
            return False
