# AI-Network-Intrusion-Detection

Network intrusion detection using Decision Tree (and KNN comparison) - algorithms studied in class.

## Pipeline

```
01_data_cleaning.py      ->  Clean CSV, handle missing values, remove duplicates
02_feature_engineering.py ->  Select network features (sbytes, dbytes, sttl, Sload, Dload)
03_model_training.py     ->  Train Decision Tree (max_depth=3 for explainability)
04_model_evaluation.py   ->  Evaluate precision, recall, F1, confusion matrix
dashboard.py             ->  Flask dashboard with explanations
06_knn_comparison.py     ->  Compare Decision Tree vs KNN (also studied in class)
```

## Quick Start

```bash
pip install -r requirements.txt

# Run all steps
python src/run_all.py

# Or step by step:
python src/01_data_cleaning.py
python src/02_feature_engineering.py
python src/03_model_training.py
python src/04_model_evaluation.py
python src/06_knn_comparison.py

# Launch dashboard
python src/dashboard.py
# Open http://localhost:5000
```

## Dataset

UNSW-NB15 with 50,000 samples, 5 features + Label (0=normal, 1=attack).

## For Professor Questions

See [GUIDE.md](GUIDE.md) for detailed explanation of every Python file, algorithm, and likely professor questions with answers.

## Based on Professional Interviews

6 interviews with IT professionals (network admins, security engineers) guided the design:
- Explainability as top priority
- Low false positives (high precision)
- Simple, understandable features
- Decision support (not full automation)
