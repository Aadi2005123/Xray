"""
Model evaluation and clinical metrics suite for multi-label chest X-ray classification.
Computes AUROC, AUPRC, Sensitivity, Specificity, Precision, Recall, and F1 per class.
Never relies on accuracy alone for imbalanced medical data.
"""

from __future__ import annotations
import numpy as np


def compute_multilabel_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    class_names: list[str],
    thresholds: list[float] | None = None,
) -> dict[str, dict[str, float]]:
    """
    Compute comprehensive clinical diagnostic evaluation metrics per pathology.

    Args:
        y_true: Binary ground truth array of shape (N, num_classes), {0, 1}
        y_prob: Predicted continuous probabilities of shape (N, num_classes), [0.0, 1.0]
        class_names: Names for each class index
        thresholds: Operating decision thresholds (defaults to 0.5 per class if None)

    Returns:
        Dict mapping class name to metrics:
          - auroc (trapezoidal approximation)
          - sensitivity (recall, true positive rate)
          - specificity (true negative rate)
          - precision (positive predictive value)
          - f1_score
    """
    num_classes = len(class_names)
    if thresholds is None:
        thresholds = [0.5] * num_classes

    results: dict[str, dict[str, float]] = {}

    for i, name in enumerate(class_names):
        true_col = y_true[:, i]
        prob_col = y_prob[:, i]
        thresh = thresholds[i]

        pred_bin = (prob_col >= thresh).astype(int)

        tp = int(np.sum((pred_bin == 1) & (true_col == 1)))
        fp = int(np.sum((pred_bin == 1) & (true_col == 0)))
        tn = int(np.sum((pred_bin == 0) & (true_col == 0)))
        fn = int(np.sum((pred_bin == 0) & (true_col == 1)))

        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = (
            2 * (precision * sensitivity) / (precision + sensitivity)
            if (precision + sensitivity) > 0
            else 0.0
        )

        # Simplified non-parametric ROC AUC approximation
        auroc = _fast_auroc(true_col, prob_col)

        results[name] = {
            "auroc": round(auroc, 4),
            "sensitivity": round(sensitivity, 4),
            "specificity": round(specificity, 4),
            "precision": round(precision, 4),
            "f1": round(f1, 4),
            "threshold": thresh,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
        }

    return results


def _fast_auroc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Calculates AUROC using the Wilcoxon-Mann-Whitney U statistic."""
    pos = y_score[y_true == 1]
    neg = y_score[y_true == 0]
    n_pos = len(pos)
    n_neg = len(neg)
    if n_pos == 0 or n_neg == 0:
        return 0.5  # Undefined/baseline

    # Vectorized U statistic
    u = np.sum(pos[:, None] > neg[None, :]) + 0.5 * np.sum(pos[:, None] == neg[None, :])
    return float(u / (n_pos * n_neg))
