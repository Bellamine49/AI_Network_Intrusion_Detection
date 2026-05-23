#!/usr/bin/env python
"""NetAlert Dashboard — type 'python dashboard.py' to launch."""
import sys, webbrowser, os
from pathlib import Path
import importlib.util

BASE = Path(__file__).resolve().parent
os.chdir(str(BASE))
sys.path.insert(0, str(BASE / "src"))

spec = importlib.util.spec_from_file_location("_netalert_dash", str(BASE / "src/dashboard.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

app = mod.create_dashboard()
print(f"\n{'=' * 50}")
print("STARTING NETALERT DASHBOARD")
print("=" * 50)
webbrowser.open("http://localhost:5000")
print("Dashboard automatically opening in your browser...")
print("If it doesn't open, go to: http://localhost:5000")
print("Press CTRL+C to stop")
print("=" * 50)
app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5000)
