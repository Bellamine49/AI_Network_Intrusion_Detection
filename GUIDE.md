# NetAlert - Complete Explanation Guide for Professor

This guide explains every Python file and every concept in the project, organized so you can answer ANY question the professor asks about the code.

---

## TABLE OF CONTENTS

1. [Project Overview](#1-project-overview)
2. [Dataset (UNSW-NB15)](#2-dataset)
3. [Step 1: Data Cleaning](#3-step-1-data-cleaning)
4. [Step 2: Feature Engineering](#4-step-2-feature-engineering)
5. [Step 3: Model Training (Decision Tree)](#5-step-3-model-training)
6. [Step 4: Model Evaluation](#6-step-4-model-evaluation)
7. [Step 5: Dashboard](#7-step-5-dashboard)
8. [Step 6: KNN Comparison](#8-step-6-knn-comparison)
9. [Key Concepts & Algorithms](#9-key-concepts--algorithms)
10. [Sample Professor Questions & Answers](#10-sample-professor-questions--answers)

---

## 1. PROJECT OVERVIEW

### What does this project do?
It analyzes network traffic and detects attacks using Machine Learning (Decision Tree + KNN).

### Why these algorithms?
Because we studied them in class: Decision Tree (Arbre de Decision) and KNN (K-Nearest Neighbors). The professor can ask about ANY line of code because it uses only what we learned.

### Why not Neural Networks or Deep Learning?
- We haven't studied them in class yet
- The professionals we interviewed said: "We need to understand WHY the AI made a decision"
- Decision Tree is naturally explainable - you can see each decision rule

### Project Pipeline (5 steps + optional KNN comparison):
```
Raw Data (CSV)
    |
    v
Step 1: Data Cleaning (pandas)
    |
    v
Step 2: Feature Engineering (select network features)
    |
    v
Step 3: Model Training (Decision Tree from sklearn)
    |
    v
Step 4: Model Evaluation (metrics: precision, recall, etc.)
    |
    v
Step 5: Dashboard (Flask web app with explanations)
    |
    v
Bonus: Step 6: KNN Comparison (compare Decision Tree vs KNN)
```

---

## 2. DATASET

### UNSW-NB15 Dataset
- **Source**: UNSW Canberra's cyber range lab
- **Size**: 50,000 rows, 6 columns
- **Columns**: `sttl`, `sbytes`, `dbytes`, `Sload`, `Dload`, `Label`
- **Label**: 0 = Normal traffic, 1 = Attack traffic
- **Distribution**: ~48,368 normal (96.7%), ~1,632 attacks (3.3%)
- **Imbalanced**: Most traffic is normal, attacks are rare (realistic)

### Features explained (for network engineers):
| Feature | Name | What it measures |
|---------|------|------------------|
| sttl | Source TTL | Time-to-live value from source |
| sbytes | Source bytes | Bytes sent by source |
| dbytes | Destination bytes | Bytes received by destination |
| Sload | Source load | Bits per second from source |
| Dload | Destination load | Bits per second to destination |

### Why these 5 features?
- They are SIMPLE and UNDERSTANDABLE
- Network engineers monitor these in real life (confirmed by interviews)
- They cover traffic volume, which the professor said is "very important"

---

## 3. STEP 1: DATA CLEANING

### File: `src/01_data_cleaning.py`

### What this code does:
Loads the raw CSV, finds and fixes missing values, removes duplicates, ensures labels are 0 or 1.

### Code explanation line by line:

```python
import pandas as pd
import numpy as np
```
- **pandas**: Library for data manipulation (tables/CSV files). We use `pd.read_csv()`, `df.isnull()`, `df.fillna()`, etc.
- **numpy**: Library for numerical operations (arrays, math functions)

```python
df = pd.read_csv(input_path)
```
- Loads the CSV file into a DataFrame (like an Excel table in Python)

```python
df.isnull().sum()
```
- Checks each column for missing (null) values. Returns count per column.

```python
for col in df.columns:
    if df[col].dtype in ['int64', 'float64']:
        df[col].fillna(df[col].median(), inplace=True)
    else:
        df[col].fillna(df[col].mode()[0], inplace=True)
```
- For numeric columns (int/float): fill missing values with MEDIAN (middle value when sorted)
- For text columns: fill missing values with MODE (most common value)
- **Why median not mean?** Median is robust to outliers (doesn't get pulled by extreme values)

```python
df = df.drop_duplicates()
```
- Removes rows that are exact copies of each other
- Duplicates could bias the model (over-represent the same data)

```python
df['Label'] = df['Label'].apply(lambda x: 0 if x == 0 else 1)
```
- Makes sure Label is: 0 = normal, 1 = attack
- `lambda x: 0 if x == 0 else 1` is a function that converts any non-zero value to 1

### Professor might ask:
- **Q**: Why don't you just drop rows with missing values?
- **A**: Because we might lose attack patterns. Attack data is rare (~3%), so every row counts. Filling with median is safer.
- **Q**: What is median vs mean?
- **A**: Median = middle value when sorted. Mean = average. Median is better when there are outliers.

---

## 4. STEP 2: FEATURE ENGINEERING

### File: `src/02_feature_engineering.py`

### What this code does:
Selects which columns (features) will be used to train the model. Keeps only the features that network professionals actually understand and monitor.

### Code explanation:

```python
selected_features = []
```
- Starts an empty list. We'll add feature names to it.

```python
if 'sttl' in df.columns:
    selected_features.append('sttl')
```
- If the column exists in our dataset, add it to the list of features to use.

```python
# Protocol encoding (if available in dataset)
if 'proto' in df.columns:
    proto_mapping = {proto: idx for idx, proto in enumerate(df['proto'].unique())}
    df['proto_numeric'] = df['proto'].map(proto_mapping)
    selected_features.append('proto_numeric')
```
- **One-hot encoding / label encoding**: Converting text categories to numbers
- Example: TCP=0, UDP=1, ICMP=2
- ML models can only work with numbers, not text like "TCP"

```python
X = df[selected_features].copy()
y = df['Label'].copy()
```
- `X` = features (inputs to the model)
- `y` = target/label (what we want to predict: 0=normal, 1=attack)
- This split is standard in ML: `X` goes in, `y` is the answer

```python
X.to_csv(output_path.replace('.csv', '_features.csv'), index=False)
y.to_csv(output_path.replace('.csv', '_target.csv'), index=False)
```
- Saves X and y separately (features and target)

### Professor might ask:
- **Q**: Why only 5 features? Why not use all 42 columns from the original dataset?
- **A**: Simplicity = explainability. With 5 features, we can understand every decision the model makes. With 42 features, it becomes a black box.
- **Q**: What is the difference between X and y in ML?
- **A**: X (features) are the inputs - what we know about the network traffic. y (target) is what we want to predict - is it an attack or not?

---

## 5. STEP 3: MODEL TRAINING

### File: `src/03_model_training.py`

### What this code does:
Trains a Decision Tree classifier on our data, evaluates it, and saves the model.

### Code explanation:

```python
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
```
- **train_test_split**: Splits data into training (80%) and testing (20%)
- **DecisionTreeClassifier**: The ML algorithm we trained in class
- **accuracy_score, precision_score, etc.**: Functions to measure how good our model is

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
```
- **test_size=0.2**: 80% for training, 20% for testing
- **random_state=42**: Makes the split reproducible (same split every time)
- **stratify=y**: Keeps the same attack/normal ratio in both training and test sets
- **IMPORTANT**: We NEVER test on data the model has already seen

```python
clf = DecisionTreeClassifier(
    max_depth=3,
    random_state=42,
    class_weight='balanced'
)
```
- **max_depth=3**: The tree can only make 3 levels of decisions. This makes it:
  - Easy to explain (at most 8 rules = 2^3)
  - Visualizable on one page
  - Less likely to memorize noise (overfitting)
- **class_weight='balanced'**: Automatically gives more weight to the minority class (attacks)
  - Without this, the model would just say "everything is normal" and be 96% accurate but useless

```python
clf.fit(X_train, y_train)
```
- **fit**: This is where the model LEARNS from the training data
- The Decision Tree finds the best features and thresholds to split on

```python
y_pred = clf.predict(X_test)
```
- **predict**: Uses the trained model to make predictions on new, unseen data

### DECISION TREE ALGORITHM (what you need to explain):

The Decision Tree works like a flowchart:
1. Start at the root (top)
2. Check a condition: "Is sbytes <= 1245.5?"
3. If YES, go left; if NO, go right
4. Repeat until you reach a leaf (final decision)
5. Leaf says: "Attack" or "Normal"

**How it decides which condition to use:**
- It uses **Gini impurity** (studied in class) or **entropy**
- Gini measures how "mixed" a group is: 0 = all same class, 1 = equally mixed
- The tree chooses the split that reduces Gini the most

**Simple example of what the tree learned:**
```
if sbytes <= 1245.5:
    if Dload <= 426.43:
        predict NORMAL (0)
    else:
        predict ATTACK (1)
else:
    if sttl <= 29.50:
        predict ATTACK (1)
    else:
        predict NORMAL (0)
```

### Professor might ask:
- **Q**: Why max_depth=3?
- **A**: For explainability. With depth 3, the tree has at most 8 leaf nodes. We can print it, visualize it, and explain each decision to a network engineer. This addresses the #1 requirement from interviews: explainability.
- **Q**: What happens if you increase max_depth?
- **A**: Higher accuracy on training data, but risk of overfitting (memorizing instead of learning). Lower performance on new data.
- **Q**: What is class_weight='balanced'?
- **A**: Since only 3% of data is attacks, without balancing the model would always predict "normal" and be 97% accurate but useless. Balanced gives more importance to attack samples during training.
- **Q**: What is Gini impurity?
- **A**: A measure of how mixed the classes are at a node. 0 = pure (all attack or all normal). The tree picks splits that minimize Gini impurity.

---

## 6. STEP 4: MODEL EVALUATION

### File: `src/04_model_evaluation.py`

### What this code does:
Calculates metrics to evaluate how well the model performs on the test set.

### KEY METRICS (must know these for the professor):

```python
accuracy = accuracy_score(y_test, y_pred)
```
- **Accuracy**: (TP + TN) / (TP + TN + FP + FN)
- What percent of ALL predictions were correct?
- **Problem with accuracy**: If 97% is normal traffic, saying "everything is normal" gives 97% accuracy. So accuracy alone is misleading for imbalanced datasets.

```python
precision = precision_score(y_test, y_pred)
```
- **Precision**: TP / (TP + FP)
- Of all the ALERTS we raised, how many were ACTUAL attacks?
- **HIGH precision = LOW false positives** (we don't bother the admin unnecessarily)
- **This is the #1 priority** from all 6 interviewed professionals

```python
recall = recall_score(y_test, y_pred)
```
- **Recall**: TP / (TP + FN)
- Of all the ACTUAL attacks, how many did we CATCH?
- **HIGH recall = FEW missed attacks**

```python
f1 = f1_score(y_test, y_pred)
```
- **F1-Score**: 2 * (Precision * Recall) / (Precision + Recall)
- Harmonic mean of precision and recall. Balances both.

```python
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()
```
- **Confusion Matrix**:
```
              Predicted Normal    Predicted Attack
Actual Normal        TN                 FP
Actual Attack        FN                 TP
```
- **TN** (True Negative): Normal traffic correctly identified as normal
- **FP** (False Positive): Normal traffic flagged as attack (FALSE ALARM)
- **FN** (False Negative): Attack traffic missed (MISSED ATTACK)
- **TP** (True Positive): Attack traffic correctly identified

### Professor might ask:
- **Q**: Which metric is most important for network security?
- **A**: Precision (low false positives). The professionals told us that false alarms cause "alert fatigue" - they start ignoring alerts. It's better to have fewer, more accurate alerts.
- **Q**: What is the trade-off between precision and recall?
- **A**: If we raise alerts more aggressively, we catch more attacks (higher recall) but also have more false alarms (lower precision). If we're more conservative, we have fewer false alarms (higher precision) but might miss some attacks (lower recall).
- **Q**: How do you read a confusion matrix?
- **A**: Rows = actual values, Columns = predicted values. Diagonal (TN + TP) = correct. Off-diagonal (FP + FN) = errors.

---

## 7. STEP 5: DASHBOARD

### File: `src/dashboard.py`

### What this code does:
Creates a web dashboard using Flask that shows the model's performance, decision rules, feature importance, and sample predictions.

### Code explanation:

```python
from flask import Flask
app = Flask(__name__)
```
- **Flask**: A lightweight web framework for Python
- Creates a web server that serves HTML pages

```python
@app.route('/metrics')
def show_metrics():
```
- **@app.route('/metrics')**: When someone visits http://localhost:5000/metrics, run this function
- Returns HTML that shows the metrics in a nice format

```python
model = joblib.load(MODEL_PATH)
```
- Loads the trained model we saved in Step 3

```python
tree_rules = export_text(model, feature_names=feature_names)
```
- Converts the Decision Tree into readable text rules

```python
importances = model.feature_importances_
```
- Gets the importance score for each feature
- Higher number = more important in making decisions

### Dashboard Pages:
| Route | Shows |
|-------|-------|
| `/` | Home page with navigation |
| `/metrics` | Accuracy, Precision, Recall, Confusion Matrix |
| `/tree` | The actual decision rules (can trace decisions) |
| `/features` | Which features matter most |
| `/samples` | 5 example predictions with explanations |

### Professor might ask:
- **Q**: Why Flask and not something else?
- **A**: Flask is simple and requires minimal code. We already know Python, so no need to learn JavaScript for the dashboard.
- **Q**: What is joblib used for?
- **A**: Saving and loading trained ML models. Think of it like "save" and "load" for the model.

---

## 8. STEP 6: KNN COMPARISON

### File: `src/06_knn_comparison.py`

### What this code does:
Compares Decision Tree with K-Nearest Neighbors (KNN), another algorithm we studied in class.

### KNN Algorithm Explanation:

KNN works by looking at the "k" closest data points to a new sample and taking a vote.

**How it decides:**
1. For a new network flow, find the 5 (k=5) most similar flows in the training data
2. Check if those 5 neighbors are mostly attacks or normal
3. The majority vote becomes the prediction

**Distance metric**: By default, KNN uses Euclidean distance (straight-line distance between data points in n-dimensional space)

**Why we compare both:**

| Algorithm | Pros | Cons |
|-----------|------|------|
| Decision Tree | Explainable, shows rules, fast | Can overfit, less flexible |
| KNN | Simple, no training step | Slow with large data, sensitive to scale |

### Code explanation:

```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
```
- **StandardScaler**: KNN uses distances, so features with large values (like bytes: 1,000,000) would dominate features with small values (like TTL: 31)
- Scaling makes all features have mean=0 and std=1 (standard normal distribution)

```python
KNeighborsClassifier(n_neighbors=5)
```
- k=5: look at the 5 nearest neighbors
- **Choosing k**: Small k = sensitive to noise, Large k = smoother decision boundary

### Professor might ask:
- **Q**: Why do we need StandardScaler for KNN but not Decision Tree?
- **A**: Decision Tree splits based on thresholds (e.g., "sbytes <= 1245.5") and is unaffected by scale. KNN calculates distances between points, so features with large values would dominate the distance calculation if not scaled.
- **Q**: What happens if k=1 in KNN?
- **A**: The model would just find the single nearest neighbor. Very sensitive to noise and outliers - likely to overfit.
- **Q**: What happens if k=1000?
- **A**: Too smooth - basically always predicts the majority class (Normal). Underfits.

---

## 9. KEY CONCEPTS & ALGORITHMS

### Supervised vs Unsupervised Learning

| | Supervised | Unsupervised |
|---|---|---|
| **Has labels?** | Yes (we know if traffic is attack or normal) | No (no labels) |
| **Goal** | Predict label for new data | Find patterns/groups in data |
| **Our project** | Decision Tree, KNN | Not used here |
| **Examples** | Classification, Regression | Clustering (K-Means) |

**Our project uses SUPERVISED learning** because the dataset has a Label column (0=normal, 1=attack).

### Classification vs Regression

| | Classification | Regression |
|---|---|---|
| **Predicts** | Categories (Normal vs Attack) | Continuous numbers (e.g., price, temperature) |
| **Our project** | Classification | Not used |

**Our project uses CLASSIFICATION** because we predict a category (Normal or Attack).

### Training vs Testing

- **Training data**: Used to teach the model patterns (80% of data)
- **Test data**: Used to check if the model learned correctly (20% of data, NEVER seen during training)
- **Why split?**: If we test on the same data we trained on, we don't know if the model memorized or truly learned

### Overfitting vs Underfitting

- **Overfitting**: Model memorizes training data perfectly but fails on new data (max_depth too high, k too small)
- **Underfitting**: Model is too simple and doesn't learn patterns (max_depth too low, k too large)

### Confusion Matrix Terminology:
```
                    Predicted
                    No      Yes
Actual No          TN      FP     <- False Positive (Type I error)
        Yes        FN      TP     <- False Negative (Type II error)
```

---

## 10. SAMPLE PROFESSOR QUESTIONS & ANSWERS

### Q1: "How does your Decision Tree work? Explain the algorithm."
**A**: "A Decision Tree works like a flowchart of yes/no questions about the network traffic. Starting from the top (root), it checks a condition like 'Is the source bytes <= 1245.5?' If yes, it goes left; if no, right. It keeps asking questions at each level until it reaches a leaf node that gives the final answer: Attack or Normal. At each step, the algorithm chooses the feature and threshold that best separates attacks from normal traffic, measured by Gini impurity reduction. We limited our tree to depth 3 so we can explain every single decision."

### Q2: "Why precision over accuracy?"
**A**: "Because the dataset has only 3% attacks, a model that says 'everything is normal' would have 97% accuracy but be completely useless. Also, the 6 professionals we interviewed all said false alarms are their biggest problem. They said too many false positives cause 'alert fatigue' where they start ignoring alerts. So we optimized for precision - when our system alerts, it's likely a real attack."

### Q3: "What's the difference between your Decision Tree and KNN?"
**A**: "Decision Tree learns rules like 'if sbytes > 1245, predict attack.' It's fast for prediction and fully explainable. KNN doesn't learn rules - it stores all training data and for each new sample, finds the 5 most similar past samples and takes a vote. KNN requires scaling (StandardScaler) because it uses distances, while Decision Tree doesn't need scaling because it only compares against thresholds."

### Q4: "How do you know your model isn't overfitting?"
**A**: "We split data into 80% training and 20% testing. We only evaluate on the test set that the model has never seen. We also limited tree depth to 3, which prevents the model from memorizing specific training examples. The train and test performance are similar, which confirms no overfitting."

### Q5: "Explain your pipeline from data to dashboard."
**A**: "Step 1 loads the CSV and cleans missing values. Step 2 selects which network features to use (sbytes, dbytes, sttl, Sload, Dload). Step 3 trains a Decision Tree and saves it. Step 4 evaluates performance. Step 5 launches a Flask dashboard showing metrics, tree rules, feature importance, and sample predictions. Step 6 is optional - it compares Decision Tree vs KNN."

### Q6: "What libraries did you use and why?"
**A**: "pandas for data manipulation (loading CSV, handling missing values). numpy for numerical operations. scikit-learn for the ML algorithm (DecisionTreeClassifier, KNeighborsClassifier, train_test_split, metrics). joblib for saving/loading the trained model. Flask for the web dashboard. matplotlib for plotting the decision tree."

### Q7: "Why is your dataset imbalanced and how did you handle it?"
**A**: "In real networks, most traffic (~97%) is normal and only ~3% is attacks. We kept this realistic imbalance. To handle it, we used class_weight='balanced' in the Decision Tree, which automatically gives more importance to the minority class (attacks) during training. Otherwise, the model would just always predict 'normal'."

### Q8: "What would you improve if you had more time?"
**A**: "We could test other algorithms we studied: Random Forest (ensemble of decision trees), SVM, or Logistic Regression. We could also implement real-time packet capture using pyshark instead of using a pre-collected CSV dataset. And we could tune hyperparameters more systematically using cross-validation."

---

## QUICK REFERENCE: PACKAGES USED

| Package | What it does | Code examples |
|---------|-------------|---------------|
| **pandas** | Data manipulation, CSV, tables | `pd.read_csv()`, `df.isnull()`, `df.fillna()` |
| **numpy** | Numerical operations | `np.inf`, array operations |
| **scikit-learn** | ML algorithms, metrics, splitting | `DecisionTreeClassifier`, `train_test_split`, `accuracy_score` |
| **joblib** | Save/load models | `joblib.dump()`, `joblib.load()` |
| **Flask** | Web server for dashboard | `Flask(__name__)`, `@app.route()` |
| **matplotlib** | Plotting | `plt.figure()`, `plot_tree()`, `plt.savefig()` |

## PACKAGE VERSION CHECK
```python
import pandas; print(pandas.__version__)
import sklearn; print(sklearn.__version__)
import flask; print(flask.__version__)
import numpy; print(numpy.__version__)
```
