import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
import json

def evaluate_model(model_path, X_test_path, y_test_path, output_path):
    print("=" * 50)
    print("STEP 4: MODEL EVALUATION")
    print("=" * 50)

    model = joblib.load(model_path)
    X_test = pd.read_csv(X_test_path)
    y_test = pd.read_csv(y_test_path).squeeze()
    print(f"Test set shape: {X_test.shape}")

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0,0,0,0)
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0

    print("\n" + "=" * 50)
    print("EVALUATION RESULTS")
    print("=" * 50)
    print(f"Accuracy:    {accuracy:.4f}")
    print(f"Precision:   {precision:.4f}  (lower false positives = higher precision)")
    print(f"Recall:      {recall:.4f}  (higher recall = fewer missed attacks)")
    print(f"F1-Score:    {f1:.4f}")
    print(f"Specificity: {specificity:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"              Predicted")
    print(f"              Normal  Attack")
    print(f"Actual Normal  {tn:4d}   {fp:4d}")
    print(f"        Attack  {fn:4d}   {tp:4d}")
    print(f"\nFalse Positive Rate (FPR): {fpr:.4f}")
    print(f"False Negative Rate (FNR): {fnr:.4f}")

    print("\nPROFESSIONAL INTERPRETATION:")
    print(f"  - When our system raises an alert, it is correct {precision:.1%} of the time")
    print(f"  - {(1-precision)*100:.1f}% of alerts are false positives (investigation needed)")
    print(f"  - We catch {recall:.1%} of all actual attacks")
    print(f"  - {fnr*100:.1f}% of attacks go undetected (false negatives)")

    Path("../results").mkdir(parents=True, exist_ok=True)

    report = {
        "model_info": {
            "type": "Decision Tree",
            "max_depth": getattr(model, 'max_depth', 'unknown'),
            "features_used": list(pd.read_csv(X_test_path).columns)
        },
        "performance_metrics": {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "specificity": float(specificity),
            "false_positive_rate": float(fpr),
            "false_negative_rate": float(fnr)
        },
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp)
        }
    }

    json_path = output_path.replace('.txt', '.json')
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)

    with open(output_path, 'w') as f:
        f.write("NetAlert-Basic Model Evaluation Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Model Type: Decision Tree (max_depth={getattr(model, 'max_depth', 'unknown')})\n")
        f.write(f"Features Used: {list(pd.read_csv(X_test_path).columns)}\n")
        f.write(f"Test Set Size: {X_test.shape[0]} samples\n\n")
        f.write("PERFORMANCE METRICS:\n")
        f.write(f"  Accuracy:  {accuracy:.4f}\n")
        f.write(f"  Precision: {precision:.4f}\n")
        f.write(f"  Recall:    {recall:.4f}\n")
        f.write(f"  F1-Score:  {f1:.4f}\n")
        f.write(f"  Specificity: {specificity:.4f}\n")
        f.write(f"  False Positive Rate: {fpr:.4f}\n")
        f.write(f"  False Negative Rate: {fnr:.4f}\n\n")
        f.write("CONFUSION MATRIX:\n")
        f.write(f"              Predicted\n")
        f.write(f"              Normal  Attack\n")
        f.write(f"Actual Normal  {tn:4d}   {fp:4d}\n")
        f.write(f"        Attack  {fn:4d}   {tp:4d}\n\n")
        f.write("INTERPRETATION:\n")
        f.write(f"  Precision {precision:.1%}: When system alerts, {precision:.1%} are real attacks\n")
        f.write(f"  Recall {recall:.1%}: System catches {recall:.1%} of all attacks\n")

    print(f"\nReports saved:\n  {output_path}\n  {json_path}")
    return report

if __name__ == "__main__":
    MODEL_PATH = "../models/decision_tree_model.joblib"
    X_TEST_PATH = "../data/processed/engineered_features_features.csv"
    Y_TEST_PATH = "../data/processed/engineered_features_target.csv"
    OUTPUT_PATH = "../results/evaluation_report.txt"
    Path("../models").mkdir(parents=True, exist_ok=True)
    Path("../results").mkdir(parents=True, exist_ok=True)
    Path("../data/processed").mkdir(parents=True, exist_ok=True)
    results = evaluate_model(MODEL_PATH, X_TEST_PATH, Y_TEST_PATH, OUTPUT_PATH)
    print("\nModel evaluation completed successfully!")
