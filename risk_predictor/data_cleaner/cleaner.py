﻿import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import pickle as pc

# Load dataset
df = pd.read_csv("data/craigslist_cars_to_clean.csv")

# Drop unnecessary columns
df.drop(columns=["VIN", "Model", "Link"], errors="ignore", inplace=True)

# Convert numerical columns
for col in ["Price", "Year", "Mileage", "Cylinders"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Fill missing numerical values with median
for col in ["Price", "Year", "Mileage", "Cylinders"]:
    df[col].fillna(df[col].median(), inplace=True)

# Normalize text data
text_cols = ["Brand", "Condition", "Fuel Type", "Transmission", "Body Type", "Title Status"]
for col in text_cols:
    df[col] = df[col].str.lower().str.strip().replace("unknown", np.nan)

# Drop rows with critical missing values
df.dropna(subset=["Cylinders", "Transmission"], inplace=True)

# Calculate car age
CURRENT_YEAR = 2025
df["Car_Age"] = CURRENT_YEAR - df["Year"]

# Feature engineering: Price per Year, Mileage per Year
df["Mileage_per_Year"] = df["Mileage"] / (df["Car_Age"] + 1)

# Remove 'Year' column
df.drop(columns=["Year"], inplace=True)

# Encode 'Brand' by average price
brand_avg_price = df.groupby("Brand")["Price"].transform("mean")
df["Brand_Encoded"] = brand_avg_price

# Save the encoding mappings for 'Brand' for use in training
brand_price_mapping = df.groupby("Brand")["Price"].mean().to_dict()

with open("models/brand_encoding.pkl", "wb") as f:
    pc.dump(brand_price_mapping, f)

# Debugging after encoding categorical features
print("After encoding 'Brand' and other categorical features:")
print(df[["Brand", "Condition", "Fuel Type", "Transmission", "Body Type", "Title Status"]].head())

# Define risk mappings
condition_map = {
    "new": 0,
    "excellent": 1,
    "good": 2,
    "fair": 4,
    "salvage": 5,
    "unknown": 6
}

title_risk_map = {
    "clean": 0,
    "lien": 2,
    "missing": 3,
    "parts only": 4,
    "rebuilt": 3,
    "salvage": 5,
    "unknown": 6
}

# Updated body type risk mapping (default: 2 - moderate)
body_risk_map = {
    "sedan": 0,
    "hatchback": 1,
    "coupe": 1,
    "convertible": 2,
    "wagon": 1,
    "suv": 1,
    "minivan": 3,
    "van": 3,
    "pickup": 2,
    "other": 3,
    "truck": 4,
    "bus": 5,
    "offroad": 3
}

# Updated fuel type risk mapping (default: 2 - moderate)
fuel_risk_map = {
    "gas": 1,
    "diesel": 2,
    "hybrid": 1,
    "electric": 0,
    "other": 2
}

# Updated transmission risk mapping (default: 1 - moderate)
transmission_risk_map = {
    "automatic": 1,
    "manual": 2,
    "unknown": 2  # Mark "Unknown" as moderate risk
}

# Apply mappings with handling "Unknown" values as very risky
df["Condition_Risk"] = df["Condition"].map(condition_map).fillna(5)  # "Unknown" -> 5 (very risky)
df["Title_Risk"] = df["Title Status"].map(title_risk_map).fillna(5)  # "Unknown" -> 5 (very risky)
df["Body_Risk"] = df["Body Type"].map(body_risk_map).fillna(3)  # Use default risk for missing values
df["Fuel_Risk"] = df["Fuel Type"].map(fuel_risk_map).fillna(2)  # Use default risk for missing values
df["Transmission_Risk"] = df["Transmission"].map(transmission_risk_map).fillna(2)  # Use default risk for missing values

# Debugging risk mapping
print("Risk columns after mapping:")
print(df[["Condition_Risk", "Title_Risk", "Body_Risk", "Fuel_Risk", "Transmission_Risk"]].head())

# Price, Mileage, and Age risk (quantiles)
df["Price_Risk"] = pd.qcut(df["Price"], q=3, labels=[2, 1, 0], duplicates="drop").astype(int)
df["Mileage_Risk"] = pd.qcut(df["Mileage"], q=3, labels=[0, 1, 2], duplicates="drop").astype(int)
df["Age_Risk"] = pd.qcut(df["Car_Age"], q=3, labels=[0, 1, 2], duplicates="drop").astype(int)

# **Define Risk_Category Based on Data Distribution**
df["Risk_Category"] = pd.qcut(
    df["Price_Risk"] + df["Mileage_Risk"] + df["Age_Risk"] +
    df["Condition_Risk"] + df["Title_Risk"] + df["Body_Risk"] +
    df["Fuel_Risk"] + df["Transmission_Risk"],
    q=4, labels=["Low", "Medium", "High", "Very High"], duplicates="drop"
)

text_cols.remove("Brand")
# One-hot encode categorical features
df = pd.get_dummies(df, columns=text_cols)

# Drop irrelevant columns
df.drop(columns=["Brand"], errors="ignore", inplace=True)

# Feature Scaling
scaler = StandardScaler()
scaled_cols = ["Car_Age", "Mileage", "Cylinders", "Brand_Encoded"]
df[scaled_cols] = scaler.fit_transform(df[scaled_cols])

# Save scaler
with open("models/scaler.pkl", "wb") as f:
    pc.dump(scaler, f)

# Save cleaned dataset
df.to_csv("data/cleaned_risk_data.csv", index=False)

print("✅ Data cleaning complete! Saved as cleaned_risk_data.csv.")
