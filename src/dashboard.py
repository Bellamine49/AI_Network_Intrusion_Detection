from flask import Flask, jsonify, render_template
import pandas as pd
import numpy as np
import joblib
import os, json, subprocess, sys, threading, uuid
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
    EDA_PATH = str(BASE_DIR / "results/eda_results.json")

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

    # ===== PAGE ROUTE =====
    @app.route('/')
    def index():
        return render_template("index.html")

    # ===== METRICS API =====
    @app.route('/api/metrics')
    def api_metrics():
        if model is None or X_test is None:
            return jsonify({"error": "Model not loaded"}), 503
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

    # ===== TREE RULES API =====
    @app.route('/api/tree')
    def api_tree():
        if model is None or X_test is None:
            return jsonify({"error": "Model not loaded"}), 503
        from sklearn.tree import export_text
        tree_rules = export_text(model, feature_names=list(X_test.columns), spacing=3, decimals=4)
        return jsonify({"rules": tree_rules})

    # ===== FEATURE IMPORTANCE API =====
    @app.route('/api/features')
    def api_features():
        if model is None or X_test is None:
            return jsonify({"error": "Model not loaded"}), 503
        importances = model.feature_importances_
        features = [
            {"name": name, "importance": round(imp, 6)}
            for name, imp in sorted(zip(list(X_test.columns), importances), key=lambda x: -x[1])
        ]
        return jsonify({"features": features})

    # ===== SAMPLES API =====
    @app.route('/api/samples')
    def api_samples():
        if model is None or X_test is None:
            return jsonify({"error": "Model not loaded"}), 503
        sample_size = min(5, len(X_test))
        X_sample = X_test.iloc[:sample_size]
        y_sample_true = y_test.iloc[:sample_size]
        y_sample_pred = model.predict(X_sample)
        y_sample_proba = model.predict_proba(X_sample)[:, 1]
        samples = []
        for i in range(sample_size):
            samples.append({
                "true_label": "Attack" if y_sample_true.iloc[i] == 1 else "Normal",
                "predicted": "Attack" if y_sample_pred[i] == 1 else "Normal",
                "confidence": round(float(y_sample_proba[i]), 6),
                "features": {feat: float(X_sample.iloc[i][feat]) for feat in list(X_test.columns)}
            })
        return jsonify({"samples": samples})

    # ===== COMPARISON API =====
    @app.route('/api/comparison')
    def api_comparison():
        if os.path.exists(COMPARISON_PATH):
            with open(COMPARISON_PATH, 'r') as f:
                return jsonify(json.load(f))
        return jsonify({"models": []})

    # ===== EDA API =====
    @app.route('/api/eda')
    def api_eda():
        if os.path.exists(EDA_PATH):
            with open(EDA_PATH, 'r') as f:
                return jsonify(json.load(f))
        return jsonify({"error": "EDA not available. Run EDA pipeline step first."}), 503

    # ===== PIPELINE RUNNER =====
    pipeline_tasks = {}
    SRC_DIR = str(BASE_DIR / "src")
    steps_map = {
        "clean": "01_data_cleaning.py",
        "train": "03_model_training.py",
        "evaluate": "04_model_evaluation.py",
        "knn": "06_knn_comparison.py",
        "eda": "07_exploratory_analysis.py",
    }

    def _run_step_async(step_name, script, task_id):
        try:
            pipeline_tasks[task_id] = {"status": "running", "output": "", "error": ""}
            script_path = os.path.join(SRC_DIR, script)
            result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, cwd=str(BASE_DIR))
            if result.returncode == 0:
                pipeline_tasks[task_id] = {"status": "done", "output": result.stdout, "error": ""}
            else:
                pipeline_tasks[task_id] = {"status": "failed", "output": result.stdout, "error": result.stderr}
        except Exception as e:
            pipeline_tasks[task_id] = {"status": "failed", "output": "", "error": str(e)}

    @app.route('/api/pipeline/<step>', methods=["POST"])
    def api_pipeline(step):
        if step not in steps_map:
            return jsonify({"error": f"Unknown step: {step}. Valid: {list(steps_map.keys())}"}), 400
        task_id = str(uuid.uuid4())
        t = threading.Thread(target=_run_step_async, args=(step, steps_map[step], task_id), daemon=True)
        t.start()
        return jsonify({"task_id": task_id})

    @app.route('/api/pipeline/status/<task_id>')
    def api_pipeline_status(task_id):
        s = pipeline_tasks.get(task_id)
        if not s:
            return jsonify({"status": "not_found"})
        if s["status"] in ("done", "failed"):
            result = dict(s)
            pipeline_tasks.pop(task_id, None)
            return jsonify(result)
        return jsonify(s)

    print("Dashboard routes configured (6 model + 7 EDA + pipeline)")
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
