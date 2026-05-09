"""
AquaSmart - Prepare Smart Irrigation Dataset
Uses REAL Kaggle Crop Recommendation Dataset (by Atharva Ingle)
Adds soil_moisture and irrigation_needed columns
FIXED: Rainfall now has much stronger influence on irrigation decision
"""

import pandas as pd
import numpy as np
import os

np.random.seed(42)

# ---- Load Real Kaggle Dataset ----
print("Loading real Kaggle Crop Recommendation Dataset...")
df = pd.read_csv('data/crop_recommendation_kaggle.csv')
print(f"  Original: {len(df)} samples, {df['label'].nunique()} crops")
print(f"  Columns: {list(df.columns)}")

# Rename 'label' to 'crop' for consistency
df.rename(columns={'label': 'crop'}, inplace=True)

# ---- Add Soil Moisture (simulated from real weather patterns) ----
df['soil_moisture'] = (
    df['rainfall'] / 300 * 30 +          # Rainfall contribution (0-30%)
    df['humidity'] / 100 * 35 +           # Humidity contribution (0-35%)
    (44 - df['temperature']) / 36 * 15 +  # Inverse temp contribution (0-15%)
    np.random.normal(10, 5, len(df))      # Base + noise
).clip(10, 90).round(2)

print(f"  Soil moisture range: {df['soil_moisture'].min():.1f}% - {df['soil_moisture'].max():.1f}%")

# ---- Derive Irrigation Needed Label ----
# BALANCED formula: every feature matters significantly
irrigation_score = (
    (100 - df['soil_moisture']) * 0.25 +   # Low moisture -> need water
    df['temperature'] * 0.20 +              # High temp -> need water  
    (100 - df['humidity']) * 0.20 +          # Low humidity -> need water
    (300 - df['rainfall']) / 3 * 0.25 +     # Low rainfall -> need water (STRONGER now)
    np.random.normal(0, 4, len(df))         # Noise for realism
)

# Threshold: approximately 45% needs irrigation
threshold = np.percentile(irrigation_score, 55)
df['irrigation_needed'] = (irrigation_score >= threshold).astype(int)

# ---- Save Final Dataset ----
os.makedirs('data', exist_ok=True)
df.to_csv('data/smart_irrigation.csv', index=False)

print(f"\nFinal dataset saved: {len(df)} samples")
print(f"  Irrigation needed: {df['irrigation_needed'].sum()} ({df['irrigation_needed'].mean()*100:.1f}%)")
print(f"  No irrigation:     {(1-df['irrigation_needed']).sum():.0f} ({(1-df['irrigation_needed']).mean()*100:.1f}%)")
print(f"  Columns: {list(df.columns)}")
print(f"\nSample data:")
print(df.head(10).to_string(index=False))

# ---- Show per-crop irrigation rates ----
print(f"\nIrrigation rate by crop:")
crop_rates = df.groupby('crop')['irrigation_needed'].mean().sort_values(ascending=False) * 100
for crop, rate in crop_rates.items():
    bar = '#' * int(rate / 2)
    print(f"  {crop:15s} {rate:5.1f}% {bar}")
