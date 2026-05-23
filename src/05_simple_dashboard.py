from flask import Flask, jsonify, render_template
import pandas as pd
import numpy as np
import joblib
import os
import json
from pathlib import Path

def create_dashboard():
    print("=" * 50)
    print("STEP 5: CREATING DASHBOARD")
    print("=" * 50)

    BASE_DIR = Path(__file__).resolve().parent.parent
    app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))

    MODEL_PATH = str(BASE_DIR / "models/decision_tree_model.joblib")
    X_TEST_PATH = str(BASE_DIR / "data/processed/engineered_features_features.csv")
    Y_TEST_PATH = str(BASE_DIR / "data/processed/engineered_features_target.csv")
    METRICS_PATH = str(BASE_DIR / "results/evaluation_report.json")
    COMPARISON_PATH = str(BASE_DIR / "results/model_comparison.json")

    model = None
    X_test = None
    y_test = None
    metrics = {}

    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print(f"Loaded Decision Tree model (max_depth={getattr(model, 'max_depth', 'unknown')})")
    if os.path.exists(X_TEST_PATH) and os.path.exists(Y_TEST_PATH):
        X_test = pd.read_csv(X_TEST_PATH)
        y_test = pd.read_csv(Y_TEST_PATH).squeeze()
        print(f"Loaded test data: {X_test.shape[0]} samples, {X_test.shape[1]} features")
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, 'r') as f:
            metrics = json.load(f)
        print("Loaded evaluation metrics")

    @app.route('/')
    def index():
        return render_template("index.html")

    @app.route('/api/metrics')
    def api_metrics():
        if model is None or X_test is None:
            return jsonify({"error": "Model not loaded. Run training first."}), 503
        if metrics:
            perf = metrics.get('performance_metrics', {})
            cm = metrics.get('confusion_matrix', {})
        else:
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
            y_pred = model.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, zero_division=0)
            rec = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
            perf = {
                'accuracy': acc, 'precision': prec, 'recall': rec, 'f1_score': f1,
                'false_positive_rate': fp/(fp+tn) if (fp+tn)>0 else 0,
                'false_negative_rate': fn/(fn+tp) if (fn+tp)>0 else 0
            }
            cm = {'true_negative': int(tn), 'false_positive': int(fp),
                  'false_negative': int(fn), 'true_positive': int(tp)}

        return jsonify({
            "model": f"Decision Tree (max_depth={getattr(model, 'max_depth', '?')})",
            "version": "v1.0",
            "performance": perf,
            "confusion_matrix": cm
        })

    @app.route('/api/tree')
    def api_tree():
        if model is None or X_test is None:
            return jsonify({"error": "Model not loaded"}), 503
        from sklearn.tree import export_text
        feature_names = list(X_test.columns)
        tree_rules = export_text(model, feature_names=feature_names, spacing=3, decimals=4)
        return jsonify({"rules": tree_rules})

    @app.route('/api/features')
    def api_features():
        if model is None or X_test is None:
            return jsonify({"error": "Model not loaded"}), 503
        importances = model.feature_importances_
        feature_names = list(X_test.columns)
        features = [
            {"name": name, "importance": round(imp, 6)}
            for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1])
        ]
        return jsonify({"features": features})

    @app.route('/api/samples')
    def api_samples():
        if model is None or X_test is None:
            return jsonify({"error": "Model not loaded"}), 503
        sample_size = min(5, len(X_test))
        X_sample = X_test.iloc[:sample_size]
        y_sample_true = y_test.iloc[:sample_size]
        y_sample_pred = model.predict(X_sample)
        y_sample_proba = model.predict_proba(X_sample)[:, 1]
        feature_names = list(X_test.columns)

        samples = []
        for i in range(sample_size):
            sample = {
                "true_label": "Attack" if y_sample_true.iloc[i] == 1 else "Normal",
                "predicted": "Attack" if y_sample_pred[i] == 1 else "Normal",
                "confidence": round(float(y_sample_proba[i]), 6),
                "features": {feat: float(X_sample.iloc[i][feat]) for feat in feature_names}
            }
            samples.append(sample)
        return jsonify({"samples": samples})

    @app.route('/api/comparison')
    def api_comparison():
        if os.path.exists(COMPARISON_PATH):
            with open(COMPARISON_PATH, 'r') as f:
                comp_data = json.load(f)
            return jsonify(comp_data)
        return jsonify({"models": []})

    print("Dashboard routes configured")
    return app

if __name__ == "__main__":
    app = create_dashboard()
    print("\n" + "=" * 50)
    print("STARTING NETALERT DASHBOARD")
    print("=" * 50)
    print("Dashboard available at: http://localhost:5000")
    print("Press CTRL+C to stop")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
