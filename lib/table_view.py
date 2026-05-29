import tkinter as tk
from tkinter import ttk, messagebox

class ExcelGrid(tk.Frame):
    def __init__(self, parent, file_ops, update_label_cb):
        super().__init__(parent)
        self.file_ops = file_ops
        self.update_label = update_label_cb
        
        self.headers = ["A", "B", "C", "D", "E"]
        self.data_rows = [["" for _ in range(5)] for _ in range(15)]
        
        self.row_idx = 0
        self.col_idx = 0
        self.edit_entry = None
        self.active_editing_cell = None 
        
        self.tooltip_window = None
        self.current_tip_cell = None

        self.build_ui()

    def build_ui(self):
        """Builds spreadsheet with an un-editable actions column first."""
        for widget in self.winfo_children():
            widget.destroy()

        scroll_y = ttk.Scrollbar(self, orient="vertical")
        scroll_y.pack(side="right", fill="y")
        scroll_x = ttk.Scrollbar(self, orient="horizontal")
        scroll_x.pack(side="bottom", fill="x")

        self.all_columns = ["Actions"] + self.headers

        self.tree = ttk.Treeview(
            self, columns=self.all_columns, show="headings",
            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set,
            style="Custom.Treeview"
        )
        self.tree.pack(fill="both", expand=True)
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        self.tree.heading("Actions", text="Actions")
        # Widened slightly to give emojis more horizontal space safely
        self.tree.column("Actions", width=110, anchor="center", stretch=False)

        for col in self.headers:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="w")

        for row in self.data_rows:
            self.tree.insert("", "end", values=["⬆️  ⬇️  ❌"] + list(row))

        self.tree.bind("<Button-1>", self.on_cell_click)
        self.tree.bind("<Motion>", self.on_mouse_hover)
        self.tree.bind("<Leave>", lambda e: self.hide_tooltip())

        self.master.bind("<Up>", lambda e: self.move_focus(-1, 0))
        self.master.bind("<Down>", lambda e: self.move_focus(1, 0))
        self.master.bind("<Left>", lambda e: self.move_focus(0, -1))
        self.master.bind("<Right>", lambda e: self.move_focus(0, 1))

    def get_action_type(self, event, bbox):
        """Calculates precisely which icon was selected based on absolute pixel boundaries."""
        x_inside_column = event.x - bbox[0]
        column_width = bbox[2]
        
        # Split into three equal programmatic sectors across the column area
        relative_position = x_inside_column / column_width
        
        if relative_position < 0.33:
            return "above"
        elif relative_position < 0.66:
            return "below"
        else:
            return "delete"

    def on_cell_click(self, event):
        """Processes cells and executes targeted row operations."""
        self.commit_active_editor()
        
        if self.tree.identify_region(event.x, event.y) != "cell":
            return

        col_id = self.tree.identify_column(event.x)
        item_id = self.tree.identify_row(event.y)
        
        col_num = int(col_id.replace("#", "")) - 1
        items = self.tree.get_children()
        row_num = items.index(item_id)

        if col_num == 0:
            self.tree.selection_set(item_id)
            bbox = self.tree.bbox(item_id, column=0)
            if bbox:
                action = self.get_action_type(event, bbox)
                if action == "above":
                    self.insert_row_at(row_num)
                elif action == "below":
                    self.insert_row_at(row_num + 1)
                elif action == "delete":
                    self.delete_row_at(item_id)
            return

        self.col_idx = col_num - 1
        self.row_idx = row_num
        self.spawn_editor(item_id, col_num)

    def on_mouse_hover(self, event):
        """Tracks the mouse to show tooltips over action icons."""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            self.hide_tooltip()
            return

        col_id = self.tree.identify_column(event.x)
        item_id = self.tree.identify_row(event.y)
        col_num = int(col_id.replace("#", "")) - 1

        if col_num == 0:
            bbox = self.tree.bbox(item_id, column=0)
            if bbox:
                action = self.get_action_type(event, bbox)
                if action == "above":
                    text = "Add Row Above"
                elif action == "below":
                    text = "Add Row Below"
                else:
                    text = "Delete This Row"
                
                cell_key = f"{item_id}_{text}"
                if self.current_tip_cell != cell_key:
                    self.current_tip_cell = cell_key
                    self.show_tooltip(text, event.x_root + 15, event.y_root + 10)
        else:
            self.hide_tooltip()

    def show_tooltip(self, text, x, y):
        self.hide_tooltip()
        self.tooltip_window = tk.Toplevel(self)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        # Added absolute top level display enforcement to prevent getting lost behind main UI windows
        self.tooltip_window.attributes("-topmost", True)
        
        lbl = tk.Label(self.tooltip_window, text=text, bg="#333333", fg="#ffffff", 
                       font=("Arial", 9), padx=6, pady=3, bd=1, relief="solid")
        lbl.pack()

    def hide_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
        self.current_tip_cell = None

    def insert_row_at(self, target_idx):
        self.hide_tooltip()
        blank = ["⬆️  ⬇️  ❌"] + ([""] * len(self.headers))
        items = self.tree.get_children()
        
        if target_idx >= len(items):
            new_item = self.tree.insert("", "end", values=blank)
            self.row_idx = len(items)
        else:
            new_item = self.tree.insert("", target_idx, values=blank)
            self.row_idx = target_idx
            
        self.tree.selection_set(new_item)
        self.tree.focus(new_item)
        self.tree.see(new_item)


    def delete_row_at(self, item_id):
        """Deletes the target row, updates the data matrix, and fully updates the UI layout."""
        self.hide_tooltip()
        self.abort_editor()  # Throw away any temporary floating box configurations

        # 1. Grab all current row text entries from the table view right now
        current_data = self.get_all_data()
        
        # 2. Identify the numerical index of the item being deleted
        items = self.tree.get_children()
        try:
            target_index = items.index(item_id)
        except ValueError:
            return  # Safety exit if the item was already wiped out

        # 3. Remove that item explicitly from our text data array
        if 0 <= target_index < len(current_data):
            current_data.pop(target_index)

        # 4. Update our master rows variable with the remaining data subset
        self.data_rows = current_data

        # 5. Completely rebuild the spreadsheet to guarantee clean visuals
        self.build_ui()

        # 6. Safety restore focus positioning highlight bounds
        new_items = self.tree.get_children()
        if new_items:
            self.row_idx = max(0, min(target_index - 1, len(new_items) - 1))
            fallback_item = new_items[self.row_idx]
            self.tree.selection_set(fallback_item)
            self.tree.focus(fallback_item)
        else:
            self.row_idx = 0
            self.col_idx = 0



    def spawn_editor(self, item_id, tree_col_idx):
        self.tree.selection_set(item_id)
        self.tree.focus(item_id)
        
        bbox = self.tree.bbox(item_id, column=tree_col_idx)
        if not bbox: return
        x, y, w, h = bbox

        val = list(self.tree.item(item_id, "values"))[tree_col_idx]
        self.edit_entry = tk.Entry(self, font=("Arial", 10), bd=1, relief="solid")
        self.edit_entry.insert(0, val)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.focus_set()
        self.edit_entry.place(x=x, y=y, width=w, height=h)
        
        self.active_editing_cell = (item_id, tree_col_idx)

        self.edit_entry.bind("<Return>", lambda e: self.close_editor())
        self.edit_entry.bind("<FocusOut>", lambda e: self.close_editor())
        self.edit_entry.bind("<Escape>", lambda e: self.abort_editor())

    def commit_active_editor(self):
        if self.edit_entry and self.active_editing_cell:
            item_id, tree_col_idx = self.active_editing_cell
            new_val = self.edit_entry.get()
            vals = list(self.tree.item(item_id, "values"))
            vals[tree_col_idx] = new_val
            self.tree.item(item_id, values=vals)

    def abort_editor(self):
        self.active_editing_cell = None
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None

    def close_editor(self):
        self.commit_active_editor()
        self.active_editing_cell = None
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None

    def move_focus(self, row_change, col_change):
        items = self.tree.get_children()
        if not items: return
        
        self.close_editor()

        self.row_idx = max(0, min(self.row_idx + row_change, len(items) - 1))
        self.col_idx = max(0, min(self.col_idx + col_change, len(self.headers) - 1))

        target = items[self.row_idx]
        tree_col_idx = self.col_idx + 1
        
        self.tree.selection_set(target)
        self.tree.focus(target)
        self.tree.see(target)
        self.spawn_editor(target, tree_col_idx)

#    def get_all_data(self):
#        return [list(self.tree.item(i, "values"))[1:] for i in self.tree.get_children()]

    def get_all_data(self):
        """Forces open cell commits, reads all Treeview children, and returns data without action icons."""
        self.close_editor()  # Force-save any active cell being typed in right now
        
        all_rows = []
        for item in self.tree.get_children():
            values = list(self.tree.item(item, "values"))
            if values:
                # Strip out the first column (the "⬆️  ⬇️  ❌" action icons)
                clean_row = values[1:]
                all_rows.append(clean_row)
        return all_rows
