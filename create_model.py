# create_model.py
from sklearn.linear_model import LogisticRegression
import joblib
import numpy as np

X = np.array([[10], [1000], [200], [50]])
y = np.array([0, 1, 1, 0])

model = LogisticRegression().fit(X, y)
joblib.dump(model, "model.pkl")
print("Model saved!")
