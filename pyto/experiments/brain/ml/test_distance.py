import unittest

import numpy as np
from scipy.spatial import distance as sp_distance

from . import calcs, core, distance


def rows_of(seed=111, n=40, d=3):
    data = calcs.call("synthetic_blobs", {"seed": seed, "n": n, "k": 3, "d": d, "spread": 0.7})
    return [row[:-1] for row in core.as_rows(data)]


class TheFacade(unittest.TestCase):
    def setUp(self):
        self.a = rows_of()
        self.b = rows_of(seed=112, n=15)

    def reference(self, metric="euclidean"):
        """the oracle: scipy's cdist, which none of the five spellings calls except one."""
        name = {"euclidean": "euclidean", "manhattan": "cityblock"}[metric]
        return sp_distance.cdist(np.asarray(self.a), np.asarray(self.b), metric=name).tolist()

    def test_every_spelling_gives_the_same_matrix(self):
        for backend in distance.BACKENDS:
            got = distance.pairwise(self.a, self.b, "euclidean", backend)
            self.assertTrue(core.close(got, self.reference(), 1e-9), backend)

    def test_manhattan_too(self):
        for backend in distance.BACKENDS:
            got = distance.pairwise(self.a, self.b, "manhattan", backend)
            self.assertTrue(core.close(got, self.reference("manhattan"), 1e-9), backend)

    def test_a_matrix_against_itself_is_symmetric_with_a_zero_diagonal(self):
        got = distance.pairwise(self.a, backend="gram")
        for i in range(len(got)):
            self.assertAlmostEqual(got[i][i], 0.0, places=9)
            for j in range(len(got)):
                self.assertAlmostEqual(got[i][j], got[j][i], places=9)

    def test_squared_is_the_square(self):
        plain = distance.pairwise(self.a, self.b, backend="np")
        squared = distance.squared(self.a, self.b, backend="np")
        self.assertTrue(core.close(squared, [[v * v for v in row] for row in plain], 1e-9))

    def test_an_unknown_backend_or_metric_is_refused(self):
        with self.assertRaises(ValueError):
            distance.backend_of({"backend": "cuda"})
        with self.assertRaises(ValueError):
            distance.pairwise(self.a, metric="cosine")

    def test_the_backend_vertical_really_is_the_one_being_called(self):
        module = distance.ops()
        self.assertIsNotNone(module, "fn.brain.backend.pairwise should be importable here")
        self.assertIn("pairwise", module.ops())
        self.assertIn("np", module.engines_of("pairwise"))

    def test_the_calculation_returns_a_part(self):
        got = calcs.call("pairwise", {"a": {"values": self.a}, "b": {"values": self.b},
                                       "backend": "backend_sp"})
        self.assertEqual(got["shape"], [len(self.a), len(self.b)])
        self.assertTrue(core.close(got["values"], self.reference(), 1e-9))
        self.assertTrue(got["for"])


class TheFourCalculationsAgreeAcrossSpellings(unittest.TestCase):
    """routing a calculation through a different spelling of the same matrix must not move it."""

    def setUp(self):
        self.data = calcs.call("synthetic_blobs", {"seed": 113, "n": 90, "k": 3, "d": 3, "spread": 0.6})
        self.features = core.dataset("the features alone", core.columns_of(self.data)[:-1],
                                     [row[:-1] for row in core.as_rows(self.data)])
        self.labels = [int(row[-1]) for row in core.as_rows(self.data)]

    def test_kmeans(self):
        answers = {b: calcs.call("kmeans", {"data": self.features, "k": 3, "seed": 113, "backend": b})
                   for b in distance.BACKENDS}
        first = answers["py"]
        for backend, got in answers.items():
            self.assertEqual(got["labels"], first["labels"], backend)
            self.assertTrue(core.close(got["inertia"], first["inertia"], 1e-9), backend)

    def test_silhouette(self):
        answers = {b: calcs.call("silhouette", {"data": self.features, "labels": self.labels, "backend": b})
                   for b in distance.BACKENDS}
        for backend, got in answers.items():
            self.assertTrue(core.close(got["scores"], answers["py"]["scores"], 1e-9), backend)

    def test_knn(self):
        classification = calcs.call("synthetic_classification",
                                    {"seed": 114, "n": 80, "d": 3, "k": 2, "spread": 1.2})
        model = calcs.call("knn_fit", {"data": classification, "target": "label", "k": 5})
        answers = {b: calcs.call("knn_predict", {"model": model, "data": classification, "backend": b})
                   for b in distance.BACKENDS}
        for backend, got in answers.items():
            self.assertEqual(got["labels"], answers["py"]["labels"], backend)

    def test_dbscan(self):
        answers = {b: calcs.call("dbscan", {"data": self.features, "eps": 1.4, "min_samples": 4, "backend": b})
                   for b in distance.BACKENDS}
        for backend, got in answers.items():
            self.assertEqual(got["labels"], answers["py"]["labels"], backend)
            self.assertEqual(got["core_points"], answers["py"]["core_points"], backend)
