import pandas as pd
import numpy as np
from pathlib import Path

def engineer_features(input_path, output_path):
    print("=" * 50)
    print("STEP 2: FEATURE ENGINEERING")
    print("=" * 50)

    input_path, output_path = str(input_path), str(output_path)
    df = pd.read_csv(input_path)
    print(f"Dataset shape: {df.shape}")

    selected_features = []

    if 'sttl' in df.columns:
        selected_features.append('sttl')
        print("Added 'sttl': Source to Destination TTL")

    if 'sbytes' in df.columns:
        selected_features.append('sbytes')
        print("Added 'sbytes': Source Bytes Transferred")
    if 'dbytes' in df.columns:
        selected_features.append('dbytes')
        print("Added 'dbytes': Destination Bytes Transferred")

    if 'Sload' in df.columns:
        selected_features.append('Sload')
        print("Added 'Sload': Source Load (bytes/sec)")
    if 'Dload' in df.columns:
        selected_features.append('Dload')
        print("Added 'Dload': Destination Load (bytes/sec)")

    if 'proto' in df.columns:
        proto_mapping = {proto: idx for idx, proto in enumerate(df['proto'].unique())}
        df['proto_numeric'] = df['proto'].map(proto_mapping)
        selected_features.append('proto_numeric')
        print(f"Added 'proto_numeric': Protocol Type")
        df['proto_original'] = df['proto']

    if 'state' in df.columns:
        state_mapping = {state: idx for idx, state in enumerate(df['state'].unique())}
        df['state_numeric'] = df['state'].map(state_mapping)
        selected_features.append('state_numeric')
        print(f"Added 'state_numeric': Connection State")
        df['state_original'] = df['state']

    print(f"Final selected features ({len(selected_features)}): {selected_features}")

    X = df[selected_features].copy()
    y = df['Label'].copy()

    missing_in_features = X.isnull().sum()
    if missing_in_features.sum() > 0:
        print(f"Missing values in features: {missing_in_features[missing_in_features > 0]}")
        for col in X.columns:
            if X[col].dtype in ['int64', 'float64']:
                X[col].fillna(X[col].median(), inplace=True)
        print("Missing values in features handled")
    else:
        print("No missing values in selected features")

    output_str = str(output_path)
    X.to_csv(output_str.replace('.csv', '_features.csv'), index=False)
    y.to_csv(output_str.replace('.csv', '_target.csv'), index=False)

    df_combined = X.copy()
    df_combined['Label'] = y
    df_combined.to_csv(output_str, index=False)

    print(f"Features shape: {X.shape}")
    print(f"Target shape: {y.shape}")
    print(f"Attack rate in dataset: {y.mean()*100:.1f}%")

    print("\nFeature interpretations (understandable by network engineers):")
    interpretations = {
        'sttl': 'TTL value - abnormal values may indicate tunneling or spoofing',
        'sbytes': 'Bytes sent from source - high values may indicate data exfiltration',
        'dbytes': 'Bytes received at destination - high values may indicate incoming attack',
        'Sload': 'Source traffic rate (bytes/sec) - sudden spikes may indicate scanning/flooding',
        'Dload': 'Destination traffic rate (bytes/sec) - sudden spikes may indicate DDoS target',
        'proto_numeric': 'Protocol type (TCP/UDP/ICMP) - different attacks use different protocols',
        'state_numeric': 'Connection state - indicates connection lifecycle phase'
    }
    for feat in selected_features:
        base = feat.replace('_numeric', '').replace('_original', '')
        if base in interpretations:
            print(f"  - {feat}: {interpretations[base]}")

    return X, y

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    INPUT_PATH = BASE_DIR / "data/processed/cleaned_data.csv"
    OUTPUT_PATH = BASE_DIR / "data/processed/engineered_features.csv"
    Path(BASE_DIR / "data/processed").mkdir(parents=True, exist_ok=True)
    X, y = engineer_features(INPUT_PATH, OUTPUT_PATH)
    print("\nFeature engineering completed successfully!")
