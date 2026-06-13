"""
Utility functions pentru GridSearchCV experiments
"""
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, log_loss, brier_score_loss
)
import pickle
import os
from datetime import datetime


def load_data(data_path: str):
    """
    Încarcă datele de training/testing din CSV
    
    Returns:
        X_train, X_test, y_train, y_test, feature_names
    """
    print(f"[INFO] Loading data from {data_path}...")
    
    df = pd.read_csv(data_path)
    
    # Separare features și target
    feature_cols = [col for col in df.columns if col not in ['match_id', 'target', 'outcome']]
    
    # Separare în train/test pe bază de match_id (80/20)
    unique_matches = df['match_id'].unique()
    np.random.seed(42)
    np.random.shuffle(unique_matches)
    
    train_size = int(0.8 * len(unique_matches))
    train_matches = set(unique_matches[:train_size])
    test_matches = set(unique_matches[train_size:])
    
    train_df = df[df['match_id'].isin(train_matches)].copy()
    test_df = df[df['match_id'].isin(test_matches)].copy()
    
    X_train = train_df[feature_cols].values
    y_train = train_df['target'].values
    
    X_test = test_df[feature_cols].values
    y_test = test_df['target'].values
    
    print(f"[INFO] Train set: {X_train.shape[0]} samples")
    print(f"[INFO] Test set: {X_test.shape[0]} samples")
    print(f"[INFO] Features: {len(feature_cols)}")
    print(f"[INFO] Target distribution - Train: {np.bincount(y_train)}")
    print(f"[INFO] Target distribution - Test: {np.bincount(y_test)}")
    
    return X_train, X_test, y_train, y_test, feature_cols


def evaluate_model(model, X_train, X_test, y_train, y_test, model_name: str):
    """
    Evaluează modelul pe metrici standard
    """
    print(f"\n{'='*70}")
    print(f"EVALUATION: {model_name}")
    print(f"{'='*70}")
    
    # Predicții
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Probabilități (dacă modelul le suportă)
    y_train_proba = model.predict_proba(X_train) if hasattr(model, 'predict_proba') else None
    y_test_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None
    
    # Metrici de clasificare
    train_accuracy = accuracy_score(y_train, y_train_pred)
    test_accuracy = accuracy_score(y_test, y_test_pred)
    
    print(f"\nACCURACY:")
    print(f"  Train: {train_accuracy:.4f}")
    print(f"  Test:  {test_accuracy:.4f}")
    
    # Metrici probabilistice (dacă disponibile)
    if y_test_proba is not None:
        test_log_loss = log_loss(y_test, y_test_proba)
        test_brier = brier_score_loss(y_test, y_test_proba[:, 1])  # Pentru clasa 1 (Draw/positiv)
        
        print(f"\nMETRICI PROBABILISTICE:")
        print(f"  Log-Loss:     {test_log_loss:.4f}")
        print(f"  Brier Score:  {test_brier:.4f}")
    
    # Per-class metrics
    print(f"\nPER-CLASS METRICS (Test):")
    for class_idx in range(len(np.unique(y_test))):
        class_name = {0: "Away Win", 1: "Draw", 2: "Home Win"}.get(class_idx, f"Class {class_idx}")
        precision = precision_score(y_test, y_test_pred, labels=[class_idx], average='micro', zero_division=0)
        recall = recall_score(y_test, y_test_pred, labels=[class_idx], average='micro', zero_division=0)
        print(f"  {class_name:12} - Precision: {precision:.4f}, Recall: {recall:.4f}")
    
    results = {
        'model_name': model_name,
        'train_accuracy': train_accuracy,
        'test_accuracy': test_accuracy,
        'timestamp': datetime.now().isoformat()
    }
    
    if y_test_proba is not None:
        results['log_loss'] = test_log_loss
        results['brier_score'] = test_brier
    
    return results


def save_results(results: dict, model, output_dir: str, model_name: str):
    """
    Salvează rezultatele și modelul antrenat
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Salvează model
    model_path = os.path.join(output_dir, f"{model_name}_best_model.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"[OK] Model salvat: {model_path}")
    
    # Salvează rezultate
    results_path = os.path.join(output_dir, f"{model_name}_results.txt")
    with open(results_path, 'w', encoding='utf-8') as f:
        f.write(f"GridSearchCV Results - {model_name}\n")
        f.write(f"{'='*70}\n\n")
        for key, value in results.items():
            f.write(f"{key}: {value}\n")
    print(f"[OK] Rezultate salvate: {results_path}")


def print_grid_search_summary(grid_search, top_n: int = 5):
    """
    Afișează sumar din GridSearchCV cu top N rezultate
    """
    print(f"\n{'='*70}")
    print(f"GRID SEARCH SUMMARY - TOP {top_n} PARAMETERS")
    print(f"{'='*70}")
    
    results_df = pd.DataFrame(grid_search.cv_results_)
    
    # Sortează după mean_test_score (descrescător)
    results_df = results_df.sort_values('mean_test_score', ascending=False).head(top_n)
    
    print(f"\n{'Rank':<5} {'Mean Score':<15} {'Std Score':<15} {'Parametri':<40}")
    print("-" * 75)
    
    for idx, (_, row) in enumerate(results_df.iterrows(), 1):
        params = row['params']
        params_str = str(params)[:35] + "..." if len(str(params)) > 35 else str(params)
        print(f"{idx:<5} {row['mean_test_score']:<15.4f} {row['std_test_score']:<15.4f} {params_str:<40}")
    
    print(f"\nBEST PARAMETERS:")
    print(f"  {grid_search.best_params_}")
    print(f"  Best CV Score: {grid_search.best_score_:.4f}")
    
    return results_df
