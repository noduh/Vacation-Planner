import os
import sys
import streamlit.web.cli as stcli

def main():
    # If compiled with PyInstaller, the sys.frozen attribute is True, and the bundled data 
    # is extracted to sys._MEIPASS
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    os.chdir(application_path)

    sys.argv = ["streamlit", "run", "src/app.py", "--global.developmentMode=false", "--server.headless=false"]
    
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
