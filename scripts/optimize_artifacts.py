import pickle
import numpy as np
import os

src = "models/recommendation_artifacts.pkl"
dst = "models/recommendation_artifacts_optimized.pkl"

print("Chargement...")
with open(src, "rb") as f:
    data = pickle.load(f)

print("Avant optimisation :")
for k, v in data.items():
    if hasattr(v, "dtype"):
        print(f"  {k}: shape={v.shape}, dtype={v.dtype}")

data["user_factors"] = data["user_factors"].astype(np.float32)
data["item_factors"] = data["item_factors"].astype(np.float32)

print("\nAprès optimisation :")
for k, v in data.items():
    if hasattr(v, "dtype"):
        print(f"  {k}: shape={v.shape}, dtype={v.dtype}")

print("\nSauvegarde...")
with open(dst, "wb") as f:
    pickle.dump(data, f, protocol=4)

before = os.path.getsize(src) / 1024 / 1024
after = os.path.getsize(dst) / 1024 / 1024
print(f"\nTaille avant : {before:.1f} MB")
print(f"Taille après  : {after:.1f} MB")
print(f"Gain          : {before - after:.1f} MB ({(before - after) / before * 100:.0f}%)")
