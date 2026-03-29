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
        self.geometry("700x620")
        self.grid_columnconfigure(0, weight=1)
        self.configure(fg_color=DARK_BG)

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

        # 2. Destination Card — just the CSV picker, no checklist
        self.dest_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=15, border_width=1, border_color="#404040")
        self.dest_card.grid(row=2, column=0, padx=40, pady=10, sticky="ew")
        self.dest_card.grid_columnconfigure(0, weight=1)

        self.label2 = ctk.CTkLabel(self.dest_card, text="2. DESTINATIONS CSV", font=ctk.CTkFont(size=13, weight="bold"), text_color="#a1a1aa")
        self.label2.grid(row=0, column=0, padx=25, pady=(20, 5), sticky="w")

        self.csv_row = ctk.CTkFrame(self.dest_card, fg_color="transparent")
        self.csv_row.grid(row=1, column=0, padx=25, pady=(5, 20), sticky="ew")
        self.csv_row.grid_columnconfigure(0, weight=1)

        self.csv_path_var = ctk.StringVar()
        self.csv_entry = ctk.CTkEntry(self.csv_row, textvariable=self.csv_path_var, state="readonly", placeholder_text="Select your destinations CSV...", height=40, border_color="#404040")
        self.csv_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.browse_btn = ctk.CTkButton(self.csv_row, text="Import", command=self.browse_csv, width=90, height=40, fg_color="#3f3f46", hover_color="#52525b")
        self.browse_btn.grid(row=0, column=1)

        self.dest_hint = ctk.CTkLabel(self.dest_card, text="All destinations in the CSV will be included.", 
                                      font=ctk.CTkFont(size=12, slant="italic"), text_color="#71717a")
        self.dest_hint.grid(row=2, column=0, padx=25, pady=(0, 20), sticky="w")

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

        # Auto-load default CSV if present
        default_csv = os.path.join(self.base_dir, "data", "vacation_destinations.csv")
        if os.path.exists(default_csv):
            self.csv_path_var.set(default_csv)
            self._load_csv(default_csv)

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
            self._load_csv(file_path)

    def _load_csv(self, csv_path):
        """Reads the CSV and validates columns."""
        try:
            df = pd.read_csv(csv_path)
            if not all(col in df.columns for col in ['label', 'latitude', 'longitude']):
                self.log("Error: CSV missing required columns (label, latitude, longitude).")
                return
            self.current_df = df
            n = len(df)
            cats = df['category'].nunique() if 'category' in df.columns else 1
            self.log(f"Loaded {n} destinations across {cats} categories.")
        except Exception as e:
            self.log(f"Failed to read CSV: {e}")

    def generate_map(self):
        if self.current_df is None:
            self.log("Please load a CSV file first.")
            return
        self.generate_btn.configure(state="disabled", text="BUILDING...")
        self.log("Generating map...")
        threading.Thread(target=self.process_map, daemon=True).start()

    def process_map(self):
        output_file = os.path.join(self.base_dir, "vacation_planning_map.html")
        
        # 1. Clean up stale file to prevent opening old results on failure
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception as e:
                self.log(f"Warning: Could not clear old map: {e}")

        try:
            df = self.current_df.copy()
            self.log(f"Building map for {len(df)} destinations...")

            # Geocode start location
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

            # Build & save map
            interactive_map = build_map(start_lat, start_lon, df)
            interactive_map.save(output_file)
            
            # 2. Verify file exists before launching
            if os.path.exists(output_file):
                self.log("Map generated successfully!")
                webbrowser.open('file://' + os.path.realpath(output_file))
            else:
                self.log("Error: Map file was not created.")

        except Exception as e:
            self.log(f"Failed: {e}")
        finally:
            self.generate_btn.configure(state="normal", text="GENERATE INTERACTIVE MAP")


if __name__ == "__main__":
    app = VacationPlannerApp()
    app.mainloop()
