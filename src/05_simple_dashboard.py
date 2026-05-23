from flask import Flask, jsonify
import pandas as pd
import numpy as np
import joblib
import os
from pathlib import Path
import json

def create_dashboard():
    print("=" * 50)
    print("STEP 5: CREATING DASHBOARD")
    print("=" * 50)

    BASE_DIR = Path(__file__).resolve().parent.parent
    app = Flask(__name__)

    MODEL_PATH = str(BASE_DIR / "models/decision_tree_model.joblib")
    X_TEST_PATH = str(BASE_DIR / "data/processed/engineered_features_features.csv")
    Y_TEST_PATH = str(BASE_DIR / "data/processed/engineered_features_target.csv")
    METRICS_PATH = str(BASE_DIR / "results/evaluation_report.json")

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run training first.")
    if not os.path.exists(X_TEST_PATH):
        raise FileNotFoundError(f"Test features not found at {X_TEST_PATH}.")

    model = joblib.load(MODEL_PATH)
    print(f"Loaded Decision Tree model (max_depth={getattr(model, 'max_depth', 'unknown')})")

    X_test = pd.read_csv(X_TEST_PATH)
    y_test = pd.read_csv(Y_TEST_PATH).squeeze()
    print(f"Loaded test data: {X_test.shape[0]} samples, {X_test.shape[1]} features")

    metrics = {}
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, 'r') as f:
            metrics = json.load(f)
        print("Loaded evaluation metrics")

    @app.route('/')
    def index():
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>NetAlert: Network Intrusion Detection</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #2c3e50; text-align: center; }
                h2 { color: #3498db; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }
                .section { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }
                a { color: #3498db; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .footer { text-align: center; margin-top: 30px; color: #95a5a6; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>NetAlert - Network Intrusion Detection</h1>
                <p>Decision Tree based system for detecting network attacks. Designed for explainability.</p>
                <h2>Dashboard Sections</h2>
                <div class="section">
                    <h3>Model Performance Metrics</h3>
                    <p>View accuracy, precision, recall, and confusion matrix.</p>
                </div>
                <div class="section">
                    <h3>Decision Tree Rules</h3>
                    <p>See the exact decision rules learned by the model.</p>
                </div>
                <div class="section">
                    <h3>Feature Importance</h3>
                    <p>Understand which network features drive detection decisions.</p>
                </div>
                <div class="section">
                    <h3>Sample Predictions</h3>
                    <p>Example predictions with explanations of each decision.</p>
                </div>
                <p>
                    <a href="/metrics">View Performance Metrics</a> |
                    <a href="/tree">View Decision Tree Rules</a> |
                    <a href="/features">View Feature Importance</a> |
                    <a href="/samples">View Sample Predictions</a>
                </p>
                <div class="footer">
                    <p>NetAlert - Explainable AI for Network Security - Decision Tree (max_depth=3)</p>
                </div>
            </div>
        </body>
        </html>
        '''

    @app.route('/metrics')
    def show_metrics():
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

        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>NetAlert: Performance Metrics</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }
                .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1, h2 { color: #2c3e50; }
                .card { background: #ecf0f1; border-left: 4px solid #3498db; padding: 20px; margin: 15px 0; border-radius: 0 5px 5px 0; }
                .value { font-size: 28px; font-weight: bold; color: #2c3e50; }
                .label { display: block; font-size: 16px; color: #7f8c8d; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #f2f2f2; font-weight: bold; }
                .back-link { display: inline-block; margin-top: 20px; color: #3498db; }
                .footer { text-align: center; margin-top: 40px; color: #95a5a6; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Model Performance Metrics</h1>
                <p><a href="/" class="back-link">Back to Home</a></p>
                <h2>Overall Performance</h2>
                <div class="card">
                    <span class="label">Accuracy</span>
                    <div class="value">{accuracy:.1%}</div>
                </div>
                <div class="card">
                    <span class="label">Precision (TOP PRIORITY)</span>
                    <div class="value">{precision:.1%}</div>
                </div>
                <div class="card">
                    <span class="label">Recall</span>
                    <div class="value">{recall:.1%}</div>
                </div>
                <div class="card">
                    <span class="label">F1-Score</span>
                    <div class="value">{f1:.1%}</div>
                </div>
                <h2>Error Rates</h2>
                <div class="card">
                    <span class="label">False Positive Rate</span>
                    <div class="value">{fpr:.1%}</div>
                </div>
                <div class="card">
                    <span class="label">False Negative Rate</span>
                    <div class="value">{fnr:.1%}</div>
                </div>
                <h2>Confusion Matrix</h2>
                <table>
                    <tr><th></th><th>Predicted Normal</th><th>Predicted Attack</th></tr>
                    <tr><th>Actual Normal</th><td>{tn:,}</td><td>{fp:,}</td></tr>
                    <tr><th>Actual Attack</th><td>{fn:,}</td><td>{tp:,}</td></tr>
                </table>
                <p><strong>TN</strong> = Correctly identified normal | <strong>FP</strong> = False alarm<br>
                <strong>FN</strong> = Missed attack | <strong>TP</strong> = Correctly identified attack</p>
                <div class="footer">
                    <p>NetAlert - Decision Tree (max_depth=3) - Explainable AI</p>
                </div>
            </div>
        </body>
        </html>
        '''.format(
            accuracy=perf.get('accuracy', 0),
            precision=perf.get('precision', 0),
            recall=perf.get('recall', 0),
            f1=perf.get('f1_score', 0),
            fpr=perf.get('false_positive_rate', 0)*100,
            fnr=perf.get('false_negative_rate', 0)*100,
            tn=cm.get('true_negative', 0),
            fp=cm.get('false_positive', 0),
            fn=cm.get('false_negative', 0),
            tp=cm.get('true_positive', 0)
        )
        return html

    @app.route('/tree')
    def show_tree():
        from sklearn.tree import export_text
        feature_names = list(X_test.columns)
        tree_rules = export_text(model, feature_names=feature_names, spacing=3, decimals=4)

        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>NetAlert: Decision Tree Rules</title>
            <style>
                body { font-family: 'Courier New', monospace; margin: 20px; background-color: #f8f9fa; }
                .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1, h2 { color: #2c3e50; text-align: center; }
                .tree-code { background: #f8f9fa; border: 1px solid #dee2e6; padding: 25px; border-radius: 5px; white-space: pre-wrap; font-size: 14px; line-height: 1.5; }
                .info-box { background: #e8f4fc; border-left: 4px solid #3498db; padding: 20px; margin: 25px 0; border-radius: 0 5px 5px 0; }
                .back-link { display: inline-block; margin-top: 20px; color: #3498db; }
                .footer { text-align: center; margin-top: 30px; color: #95a5a6; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Decision Tree Rules</h1>
                <p><a href="/" class="back-link">Back to Home</a></p>
                <div class="info-box">
                    <p><strong>How to Read:</strong></p>
                    <ul>
                        <li>Start at top. Check condition (e.g., "sbytes <= 1245.50")</li>
                        <li>If True, follow left branch. If False, follow right branch.</li>
                        <li>Leaf node shows prediction: 0 = Normal, 1 = Attack</li>
                    </ul>
                </div>
                <h2>Tree Structure (max_depth=3)</h2>
                <div class="tree-code">{tree_rules}</div>
                <div class="info-box">
                    <p><strong>Example:</strong> If a flow has <= 1245.5 source bytes AND destination load <= 426.43, it predicts NORMAL.</p>
                </div>
                <div class="footer">
                    <p>NetAlert - Decision Tree - Explainable AI</p>
                </div>
            </div>
        </body>
        </html>
        '''.format(tree_rules=tree_rules)
        return html

    @app.route('/features')
    def show_features():
        importances = model.feature_importances_
        feature_names = list(X_test.columns)
        feat_imp = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)

        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>NetAlert: Feature Importance</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }
                .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1, h2 { color: #2c3e50; }
                .bar-container { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
                .feature-row { padding: 15px; border-bottom: 1px solid #eee; }
                .feature-name { font-weight: bold; color: #2c3e50; }
                .bar-bg { background: #ecf0f1; height: 25px; margin: 10px 0; border-radius: 3px; overflow: hidden; }
                .bar-fill { background: #3498db; height: 100%; }
                .info-box { background: #e8f4fc; border-left: 4px solid #3498db; padding: 20px; margin: 25px 0; border-radius: 0 5px 5px 0; }
                .back-link { display: inline-block; margin-top: 20px; color: #3498db; }
                .footer { text-align: center; margin-top: 30px; color: #95a5a6; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Feature Importance</h1>
                <p><a href="/" class="back-link">Back to Home</a></p>
                <div class="info-box">
                    <p>Feature importance shows which traffic characteristics the model considers most predictive of attacks. Higher importance = more influential in decisions.</p>
                </div>
                <h2>Feature Ranking</h2>
                <div class="bar-container">
        '''
        max_imp = feat_imp['importance'].max()
        for _, row in feat_imp.iterrows():
            percent = (row['importance'] / max_imp) * 100 if max_imp > 0 else 0
            html += f'''
                <div class="feature-row">
                    <div class="feature-name">{row['feature']}</div>
                    <div>Importance: {row['importance']:.4f}</div>
                    <div class="bar-bg">
                        <div class="bar-fill" style="width: {percent}%;"></div>
                    </div>
                </div>
            '''

        interpretations = {
            'sttl': 'TTL - abnormal values indicate tunneling/spoofing',
            'sbytes': 'Source bytes - high values may indicate data exfiltration',
            'dbytes': 'Destination bytes - high values may indicate incoming attack',
            'Sload': 'Source rate (bytes/sec) - spikes indicate scanning/flooding',
            'Dload': 'Destination rate (bytes/sec) - spikes indicate DDoS',
            'proto_numeric': 'Protocol type (TCP/UDP/ICMP)',
            'state_numeric': 'Connection state in lifecycle'
        }

        html += '''
                </div>
                <h2>Feature Interpretations for Network Engineers</h2>
                <div class="info-box">
        '''
        for _, row in feat_imp.iterrows():
            feat = row['feature']
            base = feat.replace('_numeric', '').replace('_original', '')
            desc = interpretations.get(base, f"Network feature: {base}")
            html += f'<p><strong>{feat}</strong>: {desc}</p>'

        html += '''
                </div>
                <div class="footer">
                    <p>NetAlert - Feature Importance - Decision Tree</p>
                </div>
            </div>
        </body>
        </html>
        '''
        return html

    @app.route('/samples')
    def show_samples():
        sample_size = min(5, len(X_test))
        X_sample = X_test.iloc[:sample_size]
        y_sample_true = y_test.iloc[:sample_size]
        y_sample_pred = model.predict(X_sample)
        y_sample_proba = model.predict_proba(X_sample)[:, 1]
        feature_names = list(X_test.columns)

        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>NetAlert: Sample Predictions</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }
                .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1, h2 { color: #2c3e50; }
                .sample-card { border: 1px solid #ddd; margin: 20px 0; border-radius: 8px; overflow: hidden; }
                .sample-header { background: #3498db; color: white; padding: 15px; font-size: 18px; font-weight: bold; }
                .sample-body { padding: 20px; }
                .feature-row { display: flex; margin: 8px 0; padding: 8px; background: #f8f9fa; border-radius: 4px; }
                .f-label { flex: 0 0 120px; font-weight: bold; }
                .f-value { flex: 1; font-family: monospace; }
                .pred-box { background: #e8f4fc; border-left: 4px solid #3498db; padding: 15px; margin: 15px 0; border-radius: 0 5px 5px 0; }
                .back-link { display: inline-block; margin-top: 20px; color: #3498db; }
                .footer { text-align: center; margin-top: 30px; color: #95a5a6; font-size: 14px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Sample Predictions with Explanations</h1>
                <p><a href="/" class="back-link">Back to Home</a></p>
        '''

        for i in range(sample_size):
            is_correct = (y_sample_pred[i] == y_sample_true.iloc[i])
            status_text = "CORRECT" if is_correct else "INCORRECT"
            true_label = "Attack" if y_sample_true.iloc[i] == 1 else "Normal"
            pred_label = "Attack" if y_sample_pred[i] == 1 else "Normal"
            confidence = y_sample_proba[i] * 100
            sample_features = X_sample.iloc[i]

            html += f'''
                <div class="sample-card">
                    <div class="sample-header">
                        Sample #{i+1} - True: {true_label} | Predicted: {pred_label} ({status_text})
                    </div>
                    <div class="sample-body">
                        <h3>Network Flow Characteristics</h3>
            '''
            for feat in feature_names:
                val = sample_features[feat]
                if isinstance(val, float):
                    if abs(val) < 0.01:
                        formatted_val = f"{val:.2e}"
                    elif abs(val) < 1000:
                        formatted_val = f"{val:.2f}"
                    else:
                        formatted_val = f"{val:,.0f}"
                else:
                    formatted_val = str(val)
                html += f'''
                        <div class="feature-row">
                            <span class="f-label">{feat}:</span>
                            <span class="f-value">{formatted_val}</span>
                        </div>
                '''

            html += f'''
                        <div class="pred-box">
                            <p><strong>Prediction:</strong> {pred_label}</p>
                            <p><strong>Confidence (Attack Probability):</strong> {confidence:.1f}%</p>
                        </div>
                    </div>
                </div>
            '''

        html += '''
                <div class="footer">
                    <p>NetAlert - Sample Predictions - Explainable AI</p>
                </div>
            </div>
        </body>
        </html>
        '''
        return html

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
