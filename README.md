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
python dashboard.py
# Open http://localhost:5000
```

## Dataset

UNSW-NB15 with 50,000 samples, 5 features + Label (0=normal, 1=attack).

## For Professor Questions

See [GUIDE.md](GUIDE.md) for detailed explanation of every Python file, algorithm, and likely professor questions with answers.

## Based on 6 Professional Interviews (ENSA Kénitra 2025–2026)

6 entretiens menés auprès de professionnels IT (Société Générale, CGI, Cour de cassation, entreprise) ont guidé chaque décision de conception :

| Besoin exprimé dans les entretiens | Implémentation dans le projet |
|---|---|
| **Explicabilité non négociable** (6/6) — « comprendre pourquoi une alerte est levée » | Decision Tree `max_depth=3` : règles visibles dans le dashboard, traçables ligne par ligne |
| **Faible taux de faux positifs** (6/6) — « priorité absolue, fatigue aux alertes » | `class_weight='balanced'` + optimisation de la **precision** (73,8 %, 298 FP seulement) |
| **Aide à la décision humaine** (6/6) — « l'IA recommande, l'humain décide » | Dashboard en mode **recommandation uniquement** — pas de blocage automatique |
| **Features simples et compréhensibles** (5/6) — « des métriques réseau que les ingénieurs utilisent » | 5 features réseau : `sttl`, `sbytes`, `dbytes`, `Sload`, `Dload` — interprétables par tout admin réseau |
| **Intégration facile avec l'existant** (5/6) — API, compatibilité SIEM | API REST Flask (`/api/metrics`, `/api/tree`, etc.) — peut être consommée par n'importe quel SIEM |
| **Détection en temps réel** (6/6) — « impossible manuellement de façon continue » | Dashboard avec métriques en direct, pipeline automatisé (`run_all.py`) |
| **Génération automatique de rapports** (E4, E5) | Export JSON + TXT des métriques, comparaison DT vs KNN, EDA complète |
| **Traçabilité et audit** (E4, E5) — historique exploitable | Résultats sauvegardés dans `results/`, règles de décision affichées et exportables |

### Correspondance détaillée Questions ↔ Code

| Phase entretien | Question | Réponse synthèse | Où dans le code |
|---|---|---|---|
| Phase 1 — Contexte | Q3 — Incidents récurrents | Lenteurs, erreurs config, faux positifs | `01_data_cleaning.py` (gestion des anomalies données) |
| Phase 2 — Pratiques | Q6 — Logs : collecte et analyse | SIEM centralisé nécessaire | Dashboard centralise toutes les métriques |
| Phase 2 — Pratiques | Q8 — Faux positifs / négatifs | Problème #1, fatigue aux alertes | `class_weight='balanced'`, priorité à la precision |
| Phase 3 — Perception IA | Q10 — Opinion sur l'IA | Adhésion 6/6 pour analyse temps réel | `dashboard.py` avec rafraîchissement en direct |
| Phase 3 — Perception IA | Q11 — Blocage auto vs humain | Humain décide (6/6) | Dashboard en mode recommandation |
| Phase 3 — Perception IA | Q12 — Explicabilité | Indispensable (6/6) | `export_text()` arbre de décision affiché |
| Phase 4 — Attentes | Q13 — 3 priorités | Précision > intégration > interface | Métriques affichées + API standards |
| Phase 4 — Attentes | Q14 — Freins adoption | Budget, résistance, confidentialité | Solution on-premise, open-source compatible |

### Synthèse des entretiens

Le document complet est inclus dans le projet : [`Synthese_Entretiens_AI.txt`](Synthese_Entretiens_AI.txt)
