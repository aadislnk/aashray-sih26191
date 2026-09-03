from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml"
    / "susceptibility_dataset.csv"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
)

MODEL_FILE = (
    MODEL_DIR
    / "aashray_susceptibility_rf.joblib"
)

ROC_FILE = (
    MODEL_DIR
    / "susceptibility_roc.png"
)

IMPORTANCE_FILE = (
    MODEL_DIR
    / "feature_importance.csv"
)


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    "elevation",
    "slope",
    "aspect",
    "twi",
]

TARGET = "label"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("AASHRAY LANDSLIDE SUSCEPTIBILITY MODEL")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    print()
    print("Loading susceptibility dataset...")

    df = pd.read_csv(
        DATA_FILE
    )

    print(
        f"Samples: {len(df)}"
    )

    print(
        f"Features: {FEATURES}"
    )

    # --------------------------------------------------------
    # FEATURES / TARGET
    # --------------------------------------------------------

    X = df[
        FEATURES
    ]

    y = df[
        TARGET
    ]

    print()
    print("Class distribution:")

    print(
        y.value_counts()
        .sort_index()
        .to_string()
    )

    # --------------------------------------------------------
    # TRAIN / TEST SPLIT
    # --------------------------------------------------------

    print()
    print("Creating train/test split...")

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=42,
            stratify=y,
        )
    )

    print(
        f"Training samples: {len(X_train)}"
    )

    print(
        f"Testing samples: {len(X_test)}"
    )

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    print()
    print("Training Random Forest...")

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        X_train,
        y_train
    )

    print(
        "Training completed."
    )

    # --------------------------------------------------------
    # PREDICTION
    # --------------------------------------------------------

    y_pred = model.predict(
        X_test
    )

    y_probability = model.predict_proba(
        X_test
    )[:, 1]

    # --------------------------------------------------------
    # CONFUSION MATRIX
    # --------------------------------------------------------

    cm = confusion_matrix(
        y_test,
        y_pred
    )

    print()
    print("=" * 70)
    print("CONFUSION MATRIX")
    print("=" * 70)

    print(cm)

    # --------------------------------------------------------
    # CLASSIFICATION REPORT
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("CLASSIFICATION REPORT")
    print("=" * 70)

    print(
        classification_report(
            y_test,
            y_pred,
            digits=4
        )
    )

    # --------------------------------------------------------
    # ROC-AUC
    # --------------------------------------------------------

    auc = roc_auc_score(
        y_test,
        y_probability
    )

    print(
        f"ROC-AUC: {auc:.4f}"
    )

    # --------------------------------------------------------
    # FEATURE IMPORTANCE
    # --------------------------------------------------------

    importance = pd.DataFrame(
        {
            "feature": FEATURES,
            "importance": model.feature_importances_,
        }
    )

    importance = importance.sort_values(
        "importance",
        ascending=False
    )

    print()
    print("=" * 70)
    print("FEATURE IMPORTANCE")
    print("=" * 70)

    print(
        importance.to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # SAVE MODEL
    # --------------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(
        model,
        MODEL_FILE
    )

    print()
    print(
        f"Model saved to:\n"
        f"{MODEL_FILE.resolve()}"
    )

    # --------------------------------------------------------
    # SAVE IMPORTANCE
    # --------------------------------------------------------

    importance.to_csv(
        IMPORTANCE_FILE,
        index=False
    )

    print(
        f"Feature importance saved to:\n"
        f"{IMPORTANCE_FILE.resolve()}"
    )

    # --------------------------------------------------------
    # ROC CURVE
    # --------------------------------------------------------

    fpr, tpr, _ = roc_curve(
        y_test,
        y_probability
    )

    plt.figure(
        figsize=(7, 6)
    )

    plt.plot(
        fpr,
        tpr,
        label=f"Random Forest (AUC = {auc:.3f})"
    )

    plt.plot(
        [0, 1],
        [0, 1],
        linestyle="--"
    )

    plt.xlabel(
        "False Positive Rate"
    )

    plt.ylabel(
        "True Positive Rate"
    )

    plt.title(
        "AASHRAY Susceptibility Model"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        ROC_FILE,
        dpi=200
    )

    plt.close()

    print(
        f"ROC curve saved to:\n"
        f"{ROC_FILE.resolve()}"
    )

    print()
    print("=" * 70)
    print("MODEL TRAINING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()