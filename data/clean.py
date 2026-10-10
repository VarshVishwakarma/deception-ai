import pandas as pd

def load_data(file_path: str) -> pd.DataFrame:
    """Load dataset from CSV file."""
    try:
        df = pd.read_csv(file_path)
        print(f"[INFO] Dataset loaded successfully with shape: {df.shape}")
        return df
    except Exception as e:
        print(f"[ERROR] Failed to load dataset: {e}")
        exit()


def clean_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Convert 'truthful'/'deceptive' to 0/1."""
    mapping = {
        "truthful": 0,
        "deceptive": 1
    }
    
    df["label"] = df["deceptive"].map(mapping)
    
    if df["label"].isnull().sum() > 0:
        print("[WARNING] Some labels could not be mapped!")
    
    return df


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only required columns."""
    return df[["text", "label"]]


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows."""
    before = df.shape[0]
    df = df.drop_duplicates()
    after = df.shape[0]
    
    print(f"[INFO] Removed {before - after} duplicate rows")
    return df


def basic_validation(df: pd.DataFrame):
    """Check dataset quality."""
    print("\n📊 Dataset Summary:")
    print(df.head())
    
    print("\n📈 Label Distribution:")
    print(df["label"].value_counts())
    
    print("\n🔍 Null Values:")
    print(df.isnull().sum())


def save_data(df: pd.DataFrame, output_path: str):
    """Save cleaned dataset."""
    df.to_csv(output_path, index=False)
    print(f"\n✅ Clean dataset saved at: {output_path}")


def main():
    input_path = "deceptive-opinion.csv"   # your file name
    output_path = "clean_dataset.csv"

    df = load_data(input_path)
    df = clean_labels(df)
    df = select_columns(df)
    df = remove_duplicates(df)

    basic_validation(df)
    save_data(df, output_path)


if __name__ == "__main__":
    main()