"""
KNN (K-Nearest Neighbors) comparison with Decision Tree.
Both algorithms were studied in class. This script compares them on the same dataset.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt

def compare_models(X_path, y_path, output_path):
    print("=" * 50)
    print("MODEL COMPARISON: DECISION TREE vs KNN")
    print("Both algorithms studied in class")
    print("=" * 50)

    X = pd.read_csv(X_path)
    y = pd.read_csv(y_path).squeeze()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Training samples: {X_train.shape[0]}, Test samples: {X_test.shape[0]}")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    models = {
        'Decision Tree (max_depth=3)': DecisionTreeClassifier(
            max_depth=3, random_state=42, class_weight='balanced'
        ),
        'KNN (k=5)': KNeighborsClassifier(n_neighbors=5),
        'KNN (k=7)': KNeighborsClassifier(n_neighbors=7),
        'KNN (k=10)': KNeighborsClassifier(n_neighbors=10)
    }

    results = []
    for name, model in models.items():
        if 'Decision Tree' in name:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
        else:
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0,0,0,0)

        results.append({
            'Model': name,
            'Accuracy': acc,
            'Precision': prec,
            'Recall': rec,
            'F1-Score': f1,
            'False Positives': fp,
            'False Negatives': fn
        })

        print(f"\n{name}:")
        print(f"  Accuracy:  {acc:.4f}")
        print(f"  Precision: {prec:.4f}")
        print(f"  Recall:    {rec:.4f}")
        print(f"  F1-Score:  {f1:.4f}")
        print(f"  FP: {fp}, FN: {fn}")

    results_df = pd.DataFrame(results)
    print("\n" + "=" * 50)
    print("COMPARISON SUMMARY")
    print("=" * 50)
    print(results_df.to_string(index=False))

    Path("../results").mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    print(f"\nResults saved to {output_path}")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    x = np.arange(len(metrics))
    width = 0.2

    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
    for i, (name, model) in enumerate(models.items()):
        r = results_df[results_df['Model'] == name].iloc[0]
        values = [r[m] for m in metrics]
        axes[0].bar(x + i*width, values, width, label=name, color=colors[i])

    axes[0].set_xlabel('Metrics')
    axes[0].set_ylabel('Score')
    axes[0].set_title('Model Comparison on Test Set')
    axes[0].set_xticks(x + width * 1.5)
    axes[0].set_xticklabels(metrics)
    axes[0].legend()
    axes[0].set_ylim(0, 1)

    fp_fn_data = results_df[['Model', 'False Positives', 'False Negatives']]
    x2 = np.arange(len(fp_fn_data))
    axes[1].bar(x2 - 0.15, fp_fn_data['False Positives'], 0.3,
                label='False Positives', color='#e74c3c')
    axes[1].bar(x2 + 0.15, fp_fn_data['False Negatives'], 0.3,
                label='False Negatives', color='#c0392b')
    axes[1].set_xlabel('Models')
    axes[1].set_ylabel('Count')
    axes[1].set_title('False Positives vs False Negatives')
    axes[1].set_xticks(x2)
    axes[1].set_xticklabels(fp_fn_data['Model'], rotation=15, ha='right')
    axes[1].legend()

    plt.tight_layout()
    plot_path = output_path.replace('.csv', '.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Comparison plot saved to {plot_path}")

    return results_df

if __name__ == "__main__":
    X_PATH = "../data/processed/engineered_features_features.csv"
    Y_PATH = "../data/processed/engineered_features_target.csv"
    OUTPUT_PATH = "../results/model_comparison.csv"
    Path("../results").mkdir(parents=True, exist_ok=True)
    results = compare_models(X_PATH, Y_PATH, OUTPUT_PATH)
    print("\nModel comparison completed!")
