"""
Exploratory Data Analysis — all techniques studied in class.
PCA, K-Means, Hierarchical Clustering, Correlation, Box Plots, Pair Plots.
"""
import pandas as pd
import numpy as np
import json, io, base64
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from scipy.cluster.hierarchy import linkage, dendrogram
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent

def run_eda():
    print("=" * 50)
    print("STEP 7: EXPLORATORY DATA ANALYSIS")
    print("=" * 50)

    data_path = BASE_DIR / "data/processed/engineered_features_features.csv"
    target_path = BASE_DIR / "data/processed/engineered_features_target.csv"

    df = pd.read_csv(data_path)
    y = pd.read_csv(target_path).squeeze()
    print(f"Loaded {df.shape[0]} samples with {df.shape[1]} features")

    results = {}

    # 1. OVERVIEW — df.info() + df.describe()
    info = []
    for col in df.columns:
        info.append({
            "column": col, "dtype": str(df[col].dtype),
            "non_null": int(df[col].notna().sum()),
            "null_count": int(df[col].isna().sum()),
        })
    results["info"] = info

    desc = df.describe().round(4)
    describe_data = {}
    for col in desc.columns:
        s = desc[col]
        describe_data[col] = {
            "count": int(s["count"]), "mean": float(s["mean"]),
            "std": float(s["std"]), "min": float(s["min"]),
            "25%": float(s["25%"]), "50%": float(s["50%"]),
            "75%": float(s["75%"]), "max": float(s["max"]),
        }
    results["describe"] = describe_data

    dist = y.value_counts()
    results["class_distribution"] = {
        "normal": int(dist.get(0, 0)), "attack": int(dist.get(1, 0)),
        "total": int(len(y)),
        "attack_pct": round(float(dist.get(1, 0) / len(y) * 100), 2),
    }
    print(f"  Class distribution: {results['class_distribution']}")

    # 2. CORRELATION MATRIX
    corr = df.corr().round(4)
    results["correlation"] = {
        "columns": list(corr.columns),
        "values": corr.values.tolist(),
    }
    print("  Correlation matrix computed")

    # 3. BOX PLOT STATISTICS per feature x class
    boxplot_data = {}
    for col in df.columns:
        groups = {}
        for label, name in [(0, "normal"), (1, "attack")]:
            vals = df.loc[y == label, col]
            q1, q3 = float(vals.quantile(0.25)), float(vals.quantile(0.75))
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outlier_list = [float(v) for v in vals if v < lower or v > upper]
            groups[name] = {
                "min": float(vals.min()), "q1": q1, "median": float(vals.median()),
                "q3": q3, "max": float(vals.max()),
                "outliers": outlier_list[:100],
            }
        boxplot_data[col] = groups
    results["boxplots"] = boxplot_data
    print("  Box plot statistics computed")

    # 4. PCA — 5D → 2D
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df)
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    results["pca"] = {
        "explained_variance_ratio": [float(v) for v in pca.explained_variance_ratio_],
        "cumulative_variance": float(np.cumsum(pca.explained_variance_ratio_)[-1]),
        "loadings": pca.components_.tolist(),
        "feature_names": list(df.columns),
        "projection": [{"pc1": float(X_pca[i, 0]), "pc2": float(X_pca[i, 1]), "label": int(y.iloc[i])}
                       for i in range(len(X_pca))],
    }
    print(f"  PCA: {results['pca']['explained_variance_ratio'][0]:.2%} + {results['pca']['explained_variance_ratio'][1]:.2%} variance")

    # 5. K-MEANS CLUSTERING
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    results["kmeans"] = {
        "inertia": float(kmeans.inertia_),
        "centroids": kmeans.cluster_centers_.tolist(),
        "assignments": [int(c) for c in clusters],
    }
    # Compare clusters to true labels
    correct = sum(1 for i in range(len(y)) if (clusters[i] == y.iloc[i]) or (clusters[i] != y.iloc[i] and (1 - clusters[i]) == y.iloc[i]))
    results["kmeans"]["accuracy_vs_true"] = round(correct / len(y), 4)
    print(f"  K-Means (k=2): inertia={kmeans.inertia_:.2f}, cluster accuracy={results['kmeans']['accuracy_vs_true']:.2%}")

    # 6. HIERARCHICAL CLUSTERING — dendrogram image (sample 300 rows)
    hc_sample = min(300, len(df))
    np.random.seed(42)
    hc_idx = np.random.choice(len(df), hc_sample, replace=False)
    X_hc = X_scaled[hc_idx]
    y_hc = y.iloc[hc_idx]
    linkage_matrix = linkage(X_hc, method="ward")
    fig, ax = plt.subplots(figsize=(10, 5))
    dn = dendrogram(linkage_matrix, ax=ax, color_threshold=0, above_threshold_color="#546e7a",
                    leaf_font_size=6, labels=None, count_sort=True)
    ax.set_title("Hierarchical Clustering Dendrogram (Ward, n=" + str(hc_sample) + ")", fontsize=11, color="#e0e0e0")
    ax.set_xlabel("Sample Index", color="#78909c")
    ax.set_ylabel("Distance (Ward)", color="#78909c")
    ax.tick_params(colors="#78909c")
    ax.set_facecolor("#0d1117")
    fig.patch.set_facecolor("#0d1117")
    for spine in ax.spines.values():
        spine.set_color("#1a2332")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor="#0d1117")
    buf.seek(0)
    dendrogram_b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    results["hierarchical"] = {
        "dendrogram_image": dendrogram_b64,
        "sample_size": hc_sample,
        "labels": [int(v) for v in y_hc.values],
    }
    print(f"  Hierarchical clustering dendrogram generated ({hc_sample} samples)")

    # 7. PAIR PLOT DATA — sampled 500 rows for scatter matrix
    pp_sample = min(500, len(df))
    np.random.seed(42)
    pp_idx = np.random.choice(len(df), pp_sample, replace=False)
    pp_data = {col: [float(df.iloc[i][col]) for i in pp_idx] for col in df.columns}
    pp_data["label"] = [int(y.iloc[i]) for i in pp_idx]
    results["pairplot"] = {
        "columns": list(df.columns),
        "data": pp_data,
        "sample_size": pp_sample,
    }
    print(f"  Pair plot data sampled ({pp_sample} rows)")

    # Save everything
    output_path = BASE_DIR / "results/eda_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f)
    print(f"\nEDA results saved to {output_path}")
    print("=" * 50)
    print("EDA COMPLETED SUCCESSFULLY")
    print("=" * 50)


if __name__ == "__main__":
    run_eda()
