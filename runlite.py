import sys
import os
import streamlit.web.cli as stcli

if getattr(sys, 'frozen', False):
    # Si el ejecutable está congelado, los datos adicionales están en sys._MEIPASS.
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

gym_script = os.path.join(base_path, "gymlite.py")

if not os.path.exists(gym_script):
    sys.exit("Error: No se encontró gymlite.py en " + base_path)

sys.argv = ["streamlit", "run", gym_script]
sys.exit(stcli.main())