"""the ml vertical's calculations, one registry: name -> Calculation.

every address is fn.brain.ml.<name> and every function is pure over its one
mapping of inputs. a calculation that needs an effect would be oc. and take the
effects handle; the ml vertical has none -- its only non-determinism is a seed.
"""

from __future__ import annotations

from pyto import Calculation

from . import linear, metrics, resample, trees, unsup

_FUNCTIONS = {
    # supervised: linear
    "linreg_fit": linear.fit,
    "ridge_fit": linear.fit,
    "linreg_predict": linear.predict,
    # evaluation
    "regression_metrics": metrics.regression,
    "classification_metrics": metrics.classification,
    "confusion_matrix": metrics.confusion,
    "roc_auc": metrics.roc_auc,
    "roc_curve": metrics.roc_curve,
    "silhouette": metrics.silhouette,
    # resampling and data
    "train_test_split": resample.train_test_split,
    "kfold": resample.kfold,
    "subset": resample.subset,
    "column": resample.column,
    "synthetic_regression": resample.synthetic_regression,
    "synthetic_blobs": resample.synthetic_blobs,
    "synthetic_classification": resample.synthetic_classification,
    "synthetic_counts": resample.synthetic_counts,
    # supervised: trees
    "tree_fit": trees.tree_fit,
    "tree_predict": trees.tree_predict,
    "forest_fit": trees.forest_fit,
    "forest_predict": trees.forest_predict,
    "gbm_fit": trees.gbm_fit,
    "gbm_predict": trees.gbm_predict,
    "learning_curve": trees.learning_curve,
    # unsupervised
    "kmeans": unsup.kmeans,
    "kmeans_predict": unsup.kmeans_predict,
    "pca": unsup.pca,
    "hierarchical": unsup.hierarchical,
    "dbscan": unsup.dbscan,
}


def _register(functions):
    return {name: Calculation(f"fn.brain.ml.{name}", fn) for name, fn in functions.items()}


REGISTRY = _register(_FUNCTIONS)


def add(name, fn):
    """later slices of the vertical register their calculations here."""
    _FUNCTIONS[name] = fn
    REGISTRY[name] = Calculation(f"fn.brain.ml.{name}", fn)
    return REGISTRY[name]


def calc(name):
    return REGISTRY[name]


def call(name, args):
    """the calculation by name, run by hand (a test's shortcut; a PCR is the real thing)."""
    return REGISTRY[name](args)


def addresses():
    return tuple(sorted(c.address for c in REGISTRY.values()))
