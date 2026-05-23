"""
Run all pipeline steps in sequence.
python src/run_all.py
"""
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

steps = [
    ("01_data_cleaning.py", "Step 1: Data Cleaning"),
    ("02_feature_engineering.py", "Step 2: Feature Engineering"),
    ("03_model_training.py", "Step 3: Model Training (Decision Tree)"),
    ("04_model_evaluation.py", "Step 4: Model Evaluation"),
    ("06_knn_comparison.py", "Step 6: Decision Tree vs KNN Comparison")
]

print("=" * 60)
print("NETALERT - Full Pipeline Execution")
print("=" * 60)

for script, description in steps:
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"{'=' * 60}")
    result = subprocess.run([sys.executable, str(Path(__file__).parent / script)],
                           capture_output=False, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"ERROR in {script}. Stopping pipeline.")
        sys.exit(1)

print("\n" + "=" * 60)
print("ALL STEPS COMPLETED SUCCESSFULLY!")
print("=" * 60)
print("\nTo start the dashboard:")
print("  python src/05_simple_dashboard.py")
print("\nThen open: http://localhost:5000")
