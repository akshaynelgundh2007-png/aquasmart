"""
AquaSmart - Train ML Model for Smart Irrigation Prediction
Uses Random Forest Classifier for high accuracy with beginner-friendly approach
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle
import os
import json

# ---- Load Dataset ----
print("Loading dataset...")
df = pd.read_csv('data/smart_irrigation.csv')
print(f"   Total samples: {len(df)}")

# ---- Feature Selection ----
feature_cols = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall', 'soil_moisture']
X = df[feature_cols]
y = df['irrigation_needed']

# ---- Train/Test Split ----
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"   Training: {len(X_train)} | Testing: {len(X_test)}")

# ---- Scale Features ----
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ---- Train Logistic Regression ----
# Logistic Regression provides a very smooth, continuous probability curve
# which makes the UI feel much more responsive to small manual input changes
print("\nTraining Logistic Regression Model...")
lr_model = LogisticRegression(random_state=42, max_iter=1000)
lr_model.fit(X_train_scaled, y_train)
lr_pred = lr_model.predict(X_test_scaled)
lr_accuracy = accuracy_score(y_test, lr_pred)
print(f"   Logistic Regression Accuracy: {lr_accuracy*100:.2f}%")

best_model = lr_model
best_name = "Logistic Regression"
best_accuracy = lr_accuracy
best_pred = lr_pred

print(f"\nBest Model: {best_name} ({best_accuracy*100:.2f}%)")

# ---- Classification Report ----
print("\n📋 Classification Report:")
print(classification_report(y_test, best_pred, target_names=['No Irrigation', 'Irrigation Needed']))

# ---- Feature Importance ----
if hasattr(best_model, 'feature_importances_'):
    importance = best_model.feature_importances_
else:
    importance = np.abs(best_model.coef_[0])
    importance = importance / np.sum(importance)

feat_importance = sorted(zip(feature_cols, importance), key=lambda x: x[1], reverse=True)
print("\nFeature Importance:")
for feat, imp in feat_importance:
    bar = "#" * int(imp * 50)
    print(f"   {feat:15s} {imp:.4f} {bar}")

# ---- Save Model & Scaler ----
os.makedirs('models', exist_ok=True)

with open('models/irrigation_model.pkl', 'wb') as f:
    pickle.dump(best_model, f)

with open('models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

# ---- Save Model Metadata ----
# Confusion matrix
cm = confusion_matrix(y_test, best_pred)
metadata = {
    'model_name': best_name,
    'accuracy': round(best_accuracy * 100, 2),
    'features': feature_cols,
    'feature_importance': {feat: round(float(imp), 4) for feat, imp in feat_importance} if hasattr(best_model, 'feature_importances_') else {feat: round(float(abs(imp)), 4) for feat, imp in zip(feature_cols, best_model.coef_[0])},
    'confusion_matrix': cm.tolist(),
    'training_samples': len(X_train),
    'test_samples': len(X_test),
    'dataset_stats': {
        col: {
            'min': round(float(df[col].min()), 2),
            'max': round(float(df[col].max()), 2),
            'mean': round(float(df[col].mean()), 2),
            'std': round(float(df[col].std()), 2)
        } for col in feature_cols
    }
}

with open('models/model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"\nModel saved to models/irrigation_model.pkl")
print(f"Scaler saved to models/scaler.pkl")
print(f"Metadata saved to models/model_metadata.json")
