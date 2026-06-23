import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
import joblib
import os
import time

def evaluate_models(X_train, X_test, y_train, y_test, target_name):
    print(f"\n--- Training and evaluating models for target: {target_name} ---")
    
    models = {
        'RandomForest': RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1),
        'LightGBM': LGBMRegressor(n_estimators=100, max_depth=5, learning_rate=0.08, num_threads=16, random_state=42, verbose=-1),
        'XGBoost': XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.08, n_jobs=-1, random_state=42)
    }
    
    results = {}
    best_mae = float('inf')
    best_model_name = None
    best_model_obj = None
    
    for name, model in models.items():
        t0 = time.time()
        model.fit(X_train, y_train)
        t_train = time.time() - t0
        
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        
        print(f"[{name}] Training Time: {t_train:.3f}s | Test MAE: {mae:.4f} | R² Score: {r2:.4f}")
        
        results[name] = {'model': model, 'mae': mae, 'r2': r2}
        
        if mae < best_mae:
            best_mae = mae
            best_model_name = name
            best_model_obj = model
            
    print(f">> Selected BEST model for {target_name}: {best_model_name} (MAE: {best_mae:.4f})")
    return best_model_name, best_model_obj

def run_training_pipeline():
    # Make sure dataset exists
    dataset_path = 'port_operations_dataset.csv'
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}. Launching generator script...")
        from generate_data import generate_synthetic_dataset
        generate_synthetic_dataset(output_path=dataset_path)
        
    df = pd.read_csv(dataset_path)
    
    # Define Input Features
    features = ['wind_speed', 'visibility', 'precipitation', 'temperature', 'vessel_queue', 'yard_occupancy', 'is_holiday']
    X = df[features]
    
    # Define Target Variables
    targets = {
        'crane_efficiency': 'crane_model.pkl',
        'turnaround_time_hours': 'vessel_model.pkl',
        'rail_dispatch_delay_mins': 'rail_model.pkl'
    }
    
    saved_meta = {}
    
    for target_col, model_filename in targets.items():
        y = df[target_col]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        best_name, best_model = evaluate_models(X_train, X_test, y_train, y_test, target_col)
        
        # Save model
        joblib.dump(best_model, model_filename)
        saved_meta[target_col] = {
            'best_model': best_name,
            'filename': model_filename,
            'features': features
        }
        print(f"Saved model to: {model_filename}")
        
    # Write model metadata summary
    print("\n--- Training Complete! ---")
    for key, value in saved_meta.items():
        print(f"Target [{key}] -> Trained using {value['best_model']} and saved to {value['filename']}")
        
if __name__ == '__main__':
    # Make sure we run in the correct folder
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_training_pipeline()
