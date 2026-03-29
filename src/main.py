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
ctk.set_default_color_theme("blue")

class VacationPlannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Vacation Planning Map Generator")
        self.geometry("600x650")
        self.grid_columnconfigure(0, weight=1)

        # Title Output
        self.title_label = ctk.CTkLabel(self, text="Vacation Planning Map Generator", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # 1. Start Location Frame
        self.start_frame = ctk.CTkFrame(self)
        self.start_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.start_frame.grid_columnconfigure(1, weight=1)

        self.start_label = ctk.CTkLabel(self.start_frame, text="1. Start Location", font=ctk.CTkFont(size=16, weight="bold"))
        self.start_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        self.loc_type_var = ctk.StringVar(value="Address")
        self.type_switch = ctk.CTkSegmentedButton(
            self.start_frame, 
            values=["Address", "Coordinates"], 
            variable=self.loc_type_var, 
            command=self.switch_loc_type
        )
        self.type_switch.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

        self.address_entry = ctk.CTkEntry(self.start_frame, placeholder_text="e.g. San Francisco, CA")
        self.address_entry.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.lat_entry = ctk.CTkEntry(self.start_frame, placeholder_text="Latitude (e.g. 37.7749)")
        self.lon_entry = ctk.CTkEntry(self.start_frame, placeholder_text="Longitude (e.g. -122.4194)")

        # 2. CSV Upload Frame
        self.csv_frame = ctk.CTkFrame(self)
        self.csv_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.csv_frame.grid_columnconfigure(1, weight=1)

        self.csv_label = ctk.CTkLabel(self.csv_frame, text="2. Destinations CSV", font=ctk.CTkFont(size=16, weight="bold"))
        self.csv_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        self.csv_path_var = ctk.StringVar()
        self.csv_entry = ctk.CTkEntry(self.csv_frame, textvariable=self.csv_path_var, state="readonly", placeholder_text="No file selected...")
        self.csv_entry.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="ew")

        self.browse_btn = ctk.CTkButton(self.csv_frame, text="Browse...", command=self.browse_csv, width=100)
        self.browse_btn.grid(row=1, column=1, padx=(5, 10), pady=10)

        self.cat_label = ctk.CTkLabel(self.csv_frame, text="Filter by Category:", font=ctk.CTkFont(size=12))
        self.cat_label.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="w")

        self.category_var = ctk.StringVar(value="All Categories")
        self.category_menu = ctk.CTkOptionMenu(self.csv_frame, variable=self.category_var, values=["All Categories"])
        self.category_menu.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 15), sticky="ew")

        # 3. Output / Generate Frame
        self.gen_frame = ctk.CTkFrame(self)
        self.gen_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.gen_frame.grid_columnconfigure(0, weight=1)
        self.gen_frame.grid_rowconfigure(1, weight=1)

        self.generate_btn = ctk.CTkButton(self.gen_frame, text="Generate Map", command=self.generate_map, height=45, font=ctk.CTkFont(size=15, weight="bold"))
        self.generate_btn.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.log_textbox = ctk.CTkTextbox(self.gen_frame, height=140)
        self.log_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.log_textbox.insert("0.0", "Ready.\n")
        self.log_textbox.configure(state="disabled")

        # Handle frozen bundled environment resolving
        if getattr(sys, 'frozen', False):
            # Running as compiled binary
            self.base_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            # Running as script
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Initial Scan of default CSV if it exists
        default_csv = os.path.join(self.base_dir, "data", "vacation_destinations.csv")
        if os.path.exists(default_csv):
            self.scan_categories(default_csv)


    def log(self, text):
        """Thread-safe logging window."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", text + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.update_idletasks()

    def switch_loc_type(self, value):
        if value == "Address":
            self.lat_entry.grid_forget()
            self.lon_entry.grid_forget()
            self.address_entry.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        else:
            self.address_entry.grid_forget()
            self.lat_entry.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
            self.lon_entry.grid(row=2, column=1, padx=(0, 10), pady=10, sticky="ew")

    def browse_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if file_path:
            self.csv_path_var.set(file_path)
            self.scan_categories(file_path)

    def scan_categories(self, csv_path):
        """Scans the CSV for unique categories and updates the OptionMenu."""
        try:
            df = pd.read_csv(csv_path)
            if 'category' in df.columns:
                unique_cats = sorted(df['category'].dropna().unique().tolist())
                new_values = ["All Categories"] + unique_cats
                self.category_menu.configure(values=new_values)
                self.category_var.set("All Categories")
            else:
                self.category_menu.configure(values=["All Categories"])
                self.category_var.set("All Categories")
        except Exception as e:
            self.log(f"Error scanning categories: {e}")

    def generate_map(self):
        self.generate_btn.configure(state="disabled")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("0.0", "end")
        self.log_textbox.configure(state="disabled")
        self.log("Starting map generation...")
        threading.Thread(target=self.process_map, daemon=True).start()

    def process_map(self):
        try:
            loc_type = self.loc_type_var.get()
            start_lat = None
            start_lon = None

            if loc_type == "Address":
                address = self.address_entry.get().strip()
                if not address:
                    self.log("Error: Please enter a starting address.")
                    return
                self.log(f"Geocoding address: {address}")
                lat, lon = get_coordinates(address)
                if lat is None or lon is None:
                    self.log("Error: Could not automatically geocode address.")
                    return
                start_lat, start_lon = lat, lon
                self.log(f"Found Coordinates: {start_lat:.6f}, {start_lon:.6f}")
            else:
                try:
                    start_lat = float(self.lat_entry.get())
                    start_lon = float(self.lon_entry.get())
                except ValueError:
                    self.log("Error: Invalid latitude or longitude. Please enter numbers.")
                    return

            csv_path = self.csv_path_var.get()
            if not csv_path or not os.path.exists(csv_path):
                # Try generic default for tester
                default_data = os.path.join(self.base_dir, "data", "vacation_destinations.csv")
                if os.path.exists(default_data):
                    self.log(f"No CSV selected. Falling back to default testing sample.")
                    csv_path = default_data
                else:
                    self.log("Error: Please explicitly select a valid CSV file.")
                    return

            self.log("Loading CSV data...")
            try:
                df = pd.read_csv(csv_path)
                req_cols = ['label', 'latitude', 'longitude']
                if not all(col in df.columns for col in req_cols):
                    self.log(f"Error: CSV missing required columns: {req_cols}")
                    return
                
                # Filter by Category if specified
                selected_cat = self.category_var.get()
                if selected_cat != "All Categories" and 'category' in df.columns:
                    df = df[df['category'] == selected_cat]
                    self.log(f"Filtered for category: {selected_cat} ({len(df)} locations)")
                
            except Exception as e:
                self.log(f"Error loading CSV: {e}")
                return

            self.log(f"Building routes for {len(df)} locations via OSRM...")
            
            # Map Build execution
            interactive_map = build_map(start_lat, start_lon, df)

            # Export HTML Document locally
            output_file = os.path.join(self.base_dir, "vacation_planning_map.html")
            
            # Delete if exists
            if os.path.exists(output_file):
                os.remove(output_file)
                
            self.log(f"Saving Offline Map explicitly to: \n -> {output_file}")
            interactive_map.save(output_file)

            self.log("\nSuccess! ✨ Opening Map in your browser automatically...")
            
            webbrowser.open('file://' + os.path.realpath(output_file))

        except Exception as e:
            self.log(f"An unexpected error occurred: {e}")
            
        finally:
            self.generate_btn.configure(state="normal")
            self.generate_btn.configure(text="Regenerate Map")


if __name__ == "__main__":
    app = VacationPlannerApp()
    app.mainloop()
