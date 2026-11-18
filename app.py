"""Root application launcher to support running `streamlit run app.py` directly from workspace root."""

import os
import sys

project_dir = os.path.join(os.path.dirname(__file__), "payment-reconciliation")
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

import runpy

app_path = os.path.join(project_dir, "app.py")
runpy.run_path(app_path, run_name="__main__")
