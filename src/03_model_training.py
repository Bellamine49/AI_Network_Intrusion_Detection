import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import joblib

def train_decision_tree(X_path, y_path, model_output_path, plot_output_path=None):
    print("=" * 50)
    print("STEP 3: MODEL TRAINING (DECISION TREE)")
    print("=" * 50)

    X_path, y_path = str(X_path), str(y_path)
    model_output_path = str(model_output_path)
    plot_output_path = str(plot_output_path) if plot_output_path else None
    X = pd.read_csv(X_path)
    y = pd.read_csv(y_path).squeeze()
    print(f"Features shape: {X.shape}")
    print(f"Attack rate: {y.mean()*100:.1f}%")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")

    clf = DecisionTreeClassifier(
        max_depth=3,
        random_state=42,
        class_weight='balanced'
    )
    print("\nTraining Decision Tree (max_depth=3 for explainability)...")
    clf.fit(X_train, y_train)
    print("Training completed!")

    y_train_pred = clf.predict(X_train)
    y_test_pred = clf.predict(X_test)

    train_accuracy = accuracy_score(y_train, y_train_pred)
    train_precision = precision_score(y_train, y_train_pred, zero_division=0)
    train_recall = recall_score(y_train, y_train_pred, zero_division=0)
    train_f1 = f1_score(y_train, y_train_pred, zero_division=0)

    test_accuracy = accuracy_score(y_test, y_test_pred)
    test_precision = precision_score(y_test, y_test_pred, zero_division=0)
    test_recall = recall_score(y_test, y_test_pred, zero_division=0)
    test_f1 = f1_score(y_test, y_test_pred, zero_division=0)

    cm = confusion_matrix(y_test, y_test_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0,0,0,0)

    print("\n" + "=" * 50)
    print("MODEL PERFORMANCE ON TEST SET")
    print("=" * 50)
    print(f"Accuracy:  {test_accuracy:.4f}")
    print(f"Precision: {test_precision:.4f}")
    print(f"Recall:    {test_recall:.4f}")
    print(f"F1-Score:  {test_f1:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"              Predicted")
    print(f"              Neg    Pos")
    print(f"Actual Neg  {tn:4d}  {fp:4d}")
    print(f"        Pos  {fn:4d}  {tp:4d}")
    print(f"\nFalse Positive Rate: {fp/(fp+tn):.4f}")
    print(f"False Negative Rate: {fn/(fn+tp):.4f}")

    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': clf.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\nFEATURE IMPORTANCE:")
    for _, row in feature_importance.iterrows():
        print(f"  {row['feature']:<20} {row['importance']:.4f}")

    print("\nDECISION TREE RULES:")
    tree_rules = export_text(clf, feature_names=list(X.columns))
    print(tree_rules)

    joblib.dump(clf, model_output_path)
    print(f"Model saved to {model_output_path}")

    if plot_output_path:
        plt.figure(figsize=(20, 10))
        plot_tree(clf, feature_names=X.columns,
                  class_names=['Normal', 'Attack'],
                  filled=True, rounded=True, fontsize=10)
        plt.title("Decision Tree for Network Intrusion Detection (max_depth=3)")
        Path(plot_output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(plot_output_path, bbox_inches='tight', dpi=300)
        plt.close()
        print(f"Decision tree plot saved to {plot_output_path}")

    return clf, X_test, y_test, y_test_pred

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    X_PATH = BASE_DIR / "data/processed/engineered_features_features.csv"
    Y_PATH = BASE_DIR / "data/processed/engineered_features_target.csv"
    MODEL_OUTPUT_PATH = BASE_DIR / "models/decision_tree_model.joblib"
    PLOT_OUTPUT_PATH = BASE_DIR / "results/decision_tree_plot.png"
    Path(BASE_DIR / "models").mkdir(parents=True, exist_ok=True)
    Path(BASE_DIR / "results").mkdir(parents=True, exist_ok=True)
    model, X_test, y_test, y_test_pred = train_decision_tree(
        X_PATH, Y_PATH, MODEL_OUTPUT_PATH, PLOT_OUTPUT_PATH
    )
    print("\nModel training completed successfully!")
