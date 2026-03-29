import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import pandas as pd
import os
import threading
import sys
import webbrowser

from api_client import get_coordinates
from map_renderer import build_map

# Setup Default Themes
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue") # We will override specific colors for Purple

PURPLE_ACCENT = "#a855f7"
PURPLE_HOVER = "#9333ea"
DARK_BG = "#1a1a1b"
CARD_BG = "#262626"

class VacationPlannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Vacation Planner")
        self.geometry("700x850")
        self.grid_columnconfigure(0, weight=1)
        self.configure(fg_color=DARK_BG)

        # State for checkboxes
        self.checklist_vars = {} # { category: { "master": var, "locations": { index: var } } }
        self.current_df = None

        # Header Section
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=40, pady=(40, 25), sticky="ew")
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="Vacation Planner", 
            font=ctk.CTkFont(family="Inter", size=36, weight="bold"),
            text_color="#ffffff"
        )
        self.title_label.pack(side="left")

        # 1. Start Location Card
        self.start_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=15, border_width=1, border_color="#404040")
        self.start_card.grid(row=1, column=0, padx=40, pady=10, sticky="ew")
        self.start_card.grid_columnconfigure(0, weight=1)

        self.label1 = ctk.CTkLabel(self.start_card, text="1. STARTING POINT", font=ctk.CTkFont(size=13, weight="bold"), text_color="#a1a1aa")
        self.label1.grid(row=0, column=0, padx=25, pady=(20, 5), sticky="w")

        self.loc_type_var = ctk.StringVar(value="Address")
        self.type_switch = ctk.CTkSegmentedButton(
            self.start_card, 
            values=["Address", "Coordinates"], 
            variable=self.loc_type_var, 
            command=self.switch_loc_type,
            selected_color=PURPLE_ACCENT,
            unselected_hover_color="#3f3f46",
            font=ctk.CTkFont(size=13)
        )
        self.type_switch.grid(row=1, column=0, padx=25, pady=5, sticky="ew")

        self.address_entry = ctk.CTkEntry(self.start_card, placeholder_text="Where does your journey begin?", height=45, border_color="#404040", font=ctk.CTkFont(size=14))
        self.address_entry.grid(row=2, column=0, padx=25, pady=15, sticky="ew")

        self.lat_entry = ctk.CTkEntry(self.start_card, placeholder_text="Latitude...", height=45, border_color="#404040")
        self.lon_entry = ctk.CTkEntry(self.start_card, placeholder_text="Longitude...", height=45, border_color="#404040")

        # 2. Destination Engine Card
        self.dest_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=15, border_width=1, border_color="#404040")
        self.dest_card.grid(row=2, column=0, padx=40, pady=10, sticky="nsew")
        self.grid_rowconfigure(2, weight=1) # Allow this row to grow
        self.dest_card.grid_columnconfigure(0, weight=1)

        self.label2 = ctk.CTkLabel(self.dest_card, text="2. MANAGE DESTINATIONS", font=ctk.CTkFont(size=13, weight="bold"), text_color="#a1a1aa")
        self.label2.grid(row=0, column=0, padx=25, pady=(20, 5), sticky="w")

        self.csv_row = ctk.CTkFrame(self.dest_card, fg_color="transparent")
        self.csv_row.grid(row=1, column=0, padx=25, pady=10, sticky="ew")
        self.csv_row.grid_columnconfigure(0, weight=1)

        self.csv_path_var = ctk.StringVar()
        self.csv_entry = ctk.CTkEntry(self.csv_row, textvariable=self.csv_path_var, state="readonly", placeholder_text="Select your destinations CSV...", height=40, border_color="#404040")
        self.csv_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.browse_btn = ctk.CTkButton(self.csv_row, text="Import", command=self.browse_csv, width=90, height=40, fg_color="#3f3f46", hover_color="#52525b")
        self.browse_btn.grid(row=0, column=1)

        # Master Toggle Row (hidden until CSV loaded)
        self.master_row = ctk.CTkFrame(self.dest_card, fg_color="transparent")
        
        self.master_var = tk.BooleanVar(value=True)
        self.master_cb = ctk.CTkCheckBox(self.master_row, text="SELECT ALL DESTINATIONS", variable=self.master_var, 
                                        font=ctk.CTkFont(size=11, weight="bold"),
                                        checkbox_width=16, checkbox_height=16, 
                                        fg_color=PURPLE_ACCENT, hover_color=PURPLE_HOVER,
                                        command=self.toggle_all_master)
        self.master_cb.pack(side="left")

        # Scrollable Destination Area (hidden until CSV loaded)
        self.scroll_frame = ctk.CTkScrollableFrame(self.dest_card, fg_color="#1e1e1e", corner_radius=10, border_width=1, border_color="#333333")
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.dest_card.grid_rowconfigure(3, weight=1)

        # 3. Action Zone
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, padx=40, pady=25, sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)

        self.generate_btn = ctk.CTkButton(
            self.action_frame, 
            text="GENERATE INTERACTIVE MAP", 
            command=self.generate_map, 
            height=60, 
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=PURPLE_ACCENT,
            hover_color=PURPLE_HOVER,
            corner_radius=12
        )
        self.generate_btn.grid(row=0, column=0, sticky="ew")

        self.status_label = ctk.CTkLabel(self.action_frame, text="Ready.", font=ctk.CTkFont(size=12), text_color="#71717a")
        self.status_label.grid(row=1, column=0, pady=(10, 0))


        # Handle frozen bundled environment resolving
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Initial Scan
        default_csv = os.path.join(self.base_dir, "data", "vacation_destinations.csv")
        if os.path.exists(default_csv):
            self.csv_path_var.set(default_csv)
            self.scan_destinations(default_csv)


    def log(self, text):
        """Simple status update."""
        self.status_label.configure(text=f"> {text}", text_color="#d1d5db")
        self.update_idletasks()

    def switch_loc_type(self, value):
        if value == "Address":
            self.lat_entry.grid_forget()
            self.lon_entry.grid_forget()
            self.address_entry.grid(row=2, column=0, padx=25, pady=15, sticky="ew")
        else:
            self.address_entry.grid_forget()
            self.lat_entry.grid(row=2, column=0, padx=(25, 200), pady=15, sticky="w")
            self.lon_entry.grid(row=2, column=0, padx=(200, 25), pady=15, sticky="e")

    def browse_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if file_path:
            self.csv_path_var.set(file_path)
            self.scan_destinations(file_path)

    def scan_destinations(self, csv_path):
        """Scans the CSV and populates the scrollable checklist."""
        try:
            for widget in self.scroll_frame.winfo_children():
                widget.destroy()
            
            # Show the master toggle and scroll frame now that we have data
            self.master_row.grid(row=2, column=0, padx=25, pady=(5, 0), sticky="ew")
            self.scroll_frame.grid(row=3, column=0, padx=25, pady=(10, 25), sticky="nsew")
            
            self.checklist_vars = {}
            self.current_df = pd.read_csv(csv_path)
            df = self.current_df
            
            if not all(col in df.columns for col in ['label', 'latitude', 'longitude']):
                self.log("Error: CSV missing required columns.")
                return

            categories = sorted(df['category'].dropna().unique().tolist()) if 'category' in df.columns else ['Uncategorized']
            
            for cat in categories:
                cat_var = tk.BooleanVar(value=True)
                cat_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
                cat_frame.pack(fill="x", pady=(5, 0))
                
                cat_cb = ctk.CTkCheckBox(cat_frame, text=cat.upper(), variable=cat_var, 
                                       font=ctk.CTkFont(size=12, weight="bold"),
                                       checkbox_width=18, checkbox_height=18, 
                                       fg_color=PURPLE_ACCENT, hover_color=PURPLE_HOVER,
                                       command=lambda c=cat, v=cat_var: self.toggle_category(c, v))
                cat_cb.pack(side="left", padx=5)
                
                self.checklist_vars[cat] = {"master": cat_var, "locations": {}}
                
                cat_items = df[df['category'] == cat] if 'category' in df.columns else df
                for idx, row in cat_items.iterrows():
                    loc_var = tk.BooleanVar(value=True)
                    loc_cb = ctk.CTkCheckBox(self.scroll_frame, text=f"  {row['label']}", variable=loc_var,
                                           font=ctk.CTkFont(size=12),
                                           checkbox_width=16, checkbox_height=16,
                                           fg_color=PURPLE_ACCENT, hover_color=PURPLE_HOVER,
                                           command=lambda c=cat: self.sync_category_state(c))
                    loc_cb.pack(fill="x", padx=30, pady=2)
                    self.checklist_vars[cat]["locations"][idx] = loc_var

            self.log(f"Loaded {len(df)} locations across {len(categories)} categories.")
        except Exception as e:
            self.log(f"Scan failed: {e}")

    def toggle_all_master(self):
        state = self.master_var.get()
        for cat_data in self.checklist_vars.values():
            cat_data["master"].set(state)
            for loc_var in cat_data["locations"].values():
                loc_var.set(state)

    def toggle_category(self, cat, cat_var):
        state = cat_var.get()
        for loc_var in self.checklist_vars[cat]["locations"].values():
            loc_var.set(state)
        self.sync_master_state()

    def sync_category_state(self, cat):
        all_checked = all(v.get() for v in self.checklist_vars[cat]["locations"].values())
        self.checklist_vars[cat]["master"].set(all_checked)
        self.sync_master_state()

    def sync_master_state(self):
        all_cats_checked = all(v["master"].get() for v in self.checklist_vars.values())
        self.master_var.set(all_cats_checked)

    def generate_map(self):
        if not self.current_df is not None:
            self.log("Please load a CSV file first.")
            return
            
        self.generate_btn.configure(state="disabled", text="BUILDING...")
        self.log("Filtering selected locations...")
        threading.Thread(target=self.process_map, daemon=True).start()

    def process_map(self):
        try:
            # Gather checked indices
            checked_indices = []
            for cat_data in self.checklist_vars.values():
                for idx, var in cat_data["locations"].items():
                    if var.get():
                        checked_indices.append(idx)
            
            if not checked_indices:
                self.log("Error: No locations selected!")
                return

            df = self.current_df.loc[checked_indices].copy()
            self.log(f"Generating map for {len(df)} selected spots...")

            # Geocoding Start
            loc_type = self.loc_type_var.get()
            start_lat, start_lon = None, None
            if loc_type == "Address":
                addr = self.address_entry.get().strip()
                if not addr:
                    self.log("Error: Missing starting address.")
                    return
                res = get_coordinates(addr)
                if not res[0]:
                    self.log("Error: Geocoding failed.")
                    return
                start_lat, start_lon = res
            else:
                try:
                    start_lat = float(self.lat_entry.get())
                    start_lon = float(self.lon_entry.get())
                except:
                    self.log("Error: Invalid coordinates.")
                    return

            # Build Map
            interactive_map = build_map(start_lat, start_lon, df)

            output_file = os.path.join(self.base_dir, "vacation_planning_map.html")
            interactive_map.save(output_file)
            self.log("Map generated successfully!")
            webbrowser.open('file://' + os.path.realpath(output_file))

        except Exception as e:
            self.log(f"Failed: {e}")
        finally:
            self.generate_btn.configure(state="normal", text="GENERATE INTERACTIVE MAP")


if __name__ == "__main__":
    app = VacationPlannerApp()
    app.mainloop()
