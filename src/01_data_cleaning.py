import pandas as pd
import numpy as np
from pathlib import Path

def load_and_clean_data(input_path, output_path):
    print("=" * 50)
    print("STEP 1: DATA CLEANING")
    print("=" * 50)

    df = pd.read_csv(input_path)
    print(f"Original dataset shape: {df.shape}")

    missing_counts = df.isnull().sum()
    if missing_counts.sum() > 0:
        print(f"Missing values found:\n{missing_counts[missing_counts > 0]}")
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                df[col].fillna(df[col].median(), inplace=True)
            else:
                df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown', inplace=True)
        print("Missing values filled with median (numeric) or mode (categorical)")
    else:
        print("No missing values found")

    initial_rows = len(df)
    df = df.drop_duplicates()
    duplicates_removed = initial_rows - len(df)
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed} duplicate rows")
    else:
        print("No duplicate rows found")

    if 'Label' in df.columns:
        unique_labels = df['Label'].unique()
        print(f"Unique Label values: {unique_labels}")
        if set(unique_labels) <= {0, 1}:
            print("Label column already binary (0=normal, 1=attack)")
        else:
            df['Label'] = df['Label'].apply(lambda x: 0 if x == 0 else 1)
            print("Converted Label to binary: 0=normal, 1=attack")
    else:
        raise ValueError("No 'Label' column found in dataset")

    df.to_csv(output_path, index=False)
    print(f"Cleaned dataset shape: {df.shape}")
    print(f"Attack samples: {df['Label'].sum()} ({df['Label'].mean()*100:.1f}%)")
    print(f"Normal samples: {len(df) - df['Label'].sum()} ({(1-df['Label'].mean())*100:.1f}%)")

    return df

if __name__ == "__main__":
    INPUT_PATH = "../data/raw/final_project_data.csv"
    OUTPUT_PATH = "../data/processed/cleaned_data.csv"
    Path("../data/processed").mkdir(parents=True, exist_ok=True)
    cleaned_df = load_and_clean_data(INPUT_PATH, OUTPUT_PATH)
    print("\nData cleaning completed successfully!")
