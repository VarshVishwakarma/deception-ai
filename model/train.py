import os
import argparse
import logging
import pandas as pd
import torch
from typing import Dict, Any, Tuple
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    set_seed,
    EvalPrediction
)

# --- Configuration & Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("deception_ai.train")

DEFAULT_MODEL_NAME = "distilbert-base-uncased"
DEFAULT_DATA_PATH = "data/clean_dataset.csv"
SAVE_DIRECTORY = "model/saved_model/"

def setup_environment(seed: int = 42) -> torch.device:
    """
    Sets the random seed for reproducibility and detects available hardware.
    """
    set_seed(seed)
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    logger.info(f"Environment setup complete. Hardware selected: {device} | Seed: {seed}")
    return device

def load_data(file_path: str) -> pd.DataFrame:
    """
    Loads the dataset from a CSV file.
    Expects columns: 'text' and 'label' (0=truthful, 1=deceptive).
    """
    logger.info(f"Attempting to load dataset from {file_path}...")
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Dataset not found at {file_path}. Please ensure the file exists."
        )
    
    df = pd.read_csv(file_path)
    if 'text' not in df.columns or 'label' not in df.columns:
        raise ValueError("Dataset must contain 'text' and 'label' columns.")
        
    logger.info(f"Successfully loaded dataset with {len(df)} records.")
    return df

def clean_text(text: str) -> str:
    """
    Basic text standardization before tokenization.
    """
    text = str(text).strip()
    # Normalize multiple spaces, tabs, and newlines
    text = " ".join(text.split())
    return text

def preprocess_data(df: pd.DataFrame, tokenizer: AutoTokenizer, max_length: int = 512) -> Tuple[Dataset, Dataset]:
    """
    Cleans text, splits the dataset, and converts it to tokenized Hugging Face Datasets.
    """
    # 1. Clean text
    logger.info("Cleaning and normalizing text data...")
    df['text'] = df['text'].apply(clean_text)
    
    # 2. Train/Test Split (80/20)
    logger.info("Splitting dataset into train (80%) and test (20%)...")
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label'])
    
    # 3. Convert to Hugging Face Dataset format
    train_dataset = Dataset.from_pandas(train_df, preserve_index=False)
    test_dataset = Dataset.from_pandas(test_df, preserve_index=False)
    
    # 4. Tokenization function
    def tokenize_function(examples):
        return tokenizer(
            examples["text"], 
            padding="max_length", 
            truncation=True, 
            max_length=max_length
        )
    
    logger.info("Tokenizing datasets...")
    train_tokenized = train_dataset.map(tokenize_function, batched=True, remove_columns=["text"])
    test_tokenized = test_dataset.map(tokenize_function, batched=True, remove_columns=["text"])
    
    return train_tokenized, test_tokenized

def compute_metrics(p: EvalPrediction) -> Dict[str, float]:
    """
    Computes classification metrics for model evaluation.
    """
    preds = p.predictions[0] if isinstance(p.predictions, tuple) else p.predictions
    preds = preds.argmax(axis=-1)
    
    precision, recall, f1, _ = precision_recall_fscore_support(p.label_ids, preds, average="binary")
    acc = accuracy_score(p.label_ids, preds)
    
    return {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }

def train():
    """
    Main training pipeline execution.
    """
    # 1. Parse CLI arguments
    parser = argparse.ArgumentParser(description="DeceptionAI Model Training Pipeline")
    parser.add_argument("--data_path", type=str, default=DEFAULT_DATA_PATH, help="Path to dataset CSV")
    parser.add_argument("--model_name", type=str, default=DEFAULT_MODEL_NAME, help="Pretrained model identifier")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Training batch size")
    args = parser.parse_args()

    # 2. Initialize environment
    setup_environment()
    
    # 3. Load Tokenizer and Model
    logger.info(f"Initializing tokenizer and model: {args.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name, 
        num_labels=2,
        id2label={0: "truthful", 1: "deceptive"},
        label2id={"truthful": 0, "deceptive": 1}
    )
    
    # 4. Prepare Data
    df = load_data(args.data_path)
    train_dataset, test_dataset = preprocess_data(df, tokenizer)
    
    # 5. Training Configuration
    # 5. Training Configuration
    logger.info("Configuring training arguments...")
    training_args = TrainingArguments(
        output_dir="./results",
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        eval_strategy="epoch",  
        save_strategy="epoch",
        logging_steps=10,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        report_to="none"
    )
    
    # 6. Initialize Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
    )
    
    # 7. Execute Training
    logger.info("🚀 Starting model training...")
    trainer.train()
    
    # 8. Final Evaluation
    logger.info("📊 Running final evaluation on test set...")
    eval_results = trainer.evaluate()
    logger.info(f"Evaluation Results: {eval_results}")
    
    # 9. Save Artifacts
    logger.info(f"💾 Saving trained model and tokenizer to {SAVE_DIRECTORY}...")
    os.makedirs(SAVE_DIRECTORY, exist_ok=True)
    trainer.save_model(SAVE_DIRECTORY)
    tokenizer.save_pretrained(SAVE_DIRECTORY)
    logger.info("✅ Training pipeline completed successfully.")

if __name__ == "__main__":
    train()