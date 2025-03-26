﻿from datetime import datetime
import pandas as pd
import pickle as pc
import os
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from xgboost import XGBRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Load cleaned dataset
df = pd.read_csv("cleaned_craigslist_cars.csv")

year = datetime.now().year

# Feature Engineering
df["Car_Age"] = year - df["Year"]
df["Mileage_per_Year"] = df["Mileage"] / (df["Car_Age"] + 1)  # Avoid division by zero

# Drop 'Year' column as we now have 'Car_Age'
df.drop(columns=["Year"], inplace=True)

# Use the already encoded 'Brand_Encoded' and 'Model_Encoded' columns
brand_avg_price = df.groupby("Brand_Encoded")["Price"].transform("mean")
model_avg_price = df.groupby("Model_Encoded")["Price"].transform("mean")

df["Brand_Encoded"] = brand_avg_price
df["Model_Encoded"] = model_avg_price

# Saving the encoding mappings for later use in prediction
with open("models/brand_encoding.pkl", "wb") as f:
    pc.dump(brand_avg_price.to_dict(), f)  # Save as dictionary for faster lookups

with open("models/model_encoding.pkl", "wb") as f:
    pc.dump(model_avg_price.to_dict(), f)  # Save as dictionary for faster lookups

# Define features (X) and target variable (y)
X = df.drop(columns=["Price"])  # Features
y = df["Price"]  # Target variable

# Split dataset (80% training, 20% testing)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Feature Scaling (Standardization)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Inspect the columns before fitting the model
print("Columns used during model training:", X.columns.tolist())


with open("models/scaler.pkl", "wb") as f:
    pc.dump(scaler, f)

# 🚀 Train Models
print("🔍 Training models...")

# 🎯 Random Forest with Hyperparameter Tuning
rf_params = {
    "n_estimators": [100, 200],
    "max_depth": [10, 20, None],
    "min_samples_split": [2, 5],
    "min_samples_leaf": [1, 2]
}

rf_grid = GridSearchCV(RandomForestRegressor(random_state=42), rf_params, cv=3, n_jobs=-1, verbose=1)
rf_grid.fit(X_train, y_train)
best_rf = rf_grid.best_estimator_

# 🎯 XGBoost
xgb = XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=6, random_state=42)
xgb.fit(X_train, y_train)

# 🎯 Gradient Boosting
gradient = GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
gradient.fit(X_train, y_train)

# 🎯 Decision Tree
decision = DecisionTreeRegressor(max_depth=10, random_state=42)
decision.fit(X_train, y_train)

# 🎯 AdaBoost
ada = AdaBoostRegressor(n_estimators=200, learning_rate=0.1, random_state=42)
ada.fit(X_train, y_train)

# 🎯 Linear Regression
lr = LinearRegression()
lr.fit(X_train, y_train)

# 🚀 Evaluate Models
models = {
    "RandomForest": best_rf,
    "XGBoost": xgb,
    "GradientBoosting": gradient,
    "DecisionTree": decision,
    "AdaBoost": ada,
    "LinearRegression": lr
}

print("\n📊 Model Performance:")
for name, model in models.items():
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"🔹 {name}:")
    print(f"   MAE: {mae:.2f}")
    print(f"   MSE: {mse:.2f}")
    print(f"   R² Score: {r2:.4f}\n")

# 🚀 Save Models
os.makedirs("models", exist_ok=True)
for name, model in models.items():
    filename = f"models/{name.lower().replace(' ', '_')}_model.pkl"
    pc.dump(model, open(filename, 'wb'))
    print(f"✅ Model saved: {filename}")

print("\n🎯 All models trained and exported successfully!")
