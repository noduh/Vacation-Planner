import sys
import os

# Ensure the 'src' directory is in the search path so that 
# internal imports like 'from api_client import ...' work correctly.
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import VacationPlannerApp

if __name__ == "__main__":
    app = VacationPlannerApp()
    app.mainloop()
