import unittest

import numpy as np
from scipy.cluster import hierarchy
from scipy.spatial import distance

from . import calcs, core, unsup


def features_of(data):
    return core.dataset("the features alone", core.columns_of(data)[:-1],
                        [row[:-1] for row in core.as_rows(data)])


def blobs(seed=51, n=120, k=3, d=2, spread=0.5, separation=14.0):
    """far-apart blobs on purpose: a clustering test should fail on the clustering,
    not on a fixture whose classes were never separable in the first place."""
    return calcs.call("synthetic_blobs",
                      {"seed": seed, "n": n, "k": k, "d": d, "spread": spread, "separation": separation})


class KMeans(unittest.TestCase):
    def setUp(self):
        self.data = blobs()
        self.features = features_of(self.data)
        self.truth = [int(row[-1]) for row in core.as_rows(self.data)]

    def test_the_seed_is_the_whole_of_the_init(self):
        args = {"data": self.features, "k": 3, "seed": 9}
        self.assertEqual(calcs.call("kmeans", args), calcs.call("kmeans", args))
        other = calcs.call("kmeans", dict(args, seed=10))
        self.assertNotEqual(other["seeded_from"], calcs.call("kmeans", args)["seeded_from"])

    def test_every_backend_gives_the_same_clustering(self):
        args = {"data": self.features, "k": 3, "seed": 9}
        answers = {b: calcs.call("kmeans", dict(args, backend=b)) for b in ("py", "np", "gram")}
        self.assertEqual(answers["py"]["labels"], answers["np"]["labels"])
        self.assertEqual(answers["py"]["labels"], answers["gram"]["labels"])
        self.assertTrue(core.close(answers["py"]["inertia"], answers["gram"]["inertia"], 1e-9))
        self.assertTrue(core.close(answers["py"]["centres"], answers["np"]["centres"], 1e-12))

    def test_the_inertia_never_goes_up(self):
        got = calcs.call("kmeans", {"data": self.features, "k": 3, "seed": 9})
        for before, after in zip(got["history"], got["history"][1:]):
            self.assertLessEqual(after, before + 1e-9)

    def test_it_recovers_the_blobs_it_was_given(self):
        got = calcs.call("kmeans", {"data": self.features, "k": 3, "seed": 9, "backend": "np"})
        pairing = {}
        for label, truth in zip(got["labels"], self.truth):
            pairing.setdefault(label, []).append(truth)
        for members in pairing.values():
            self.assertEqual(len(set(members)), 1)

    def test_kmeans_plus_plus_does_not_pick_the_same_point_twice(self):
        rng = core.stream(3)
        rows = [[float(i), 0.0] for i in range(20)]
        _, picked = unsup.kmeans_plus_plus(rows, 4, rng)
        self.assertEqual(len(set(picked)), 4)

    def test_k_out_of_range_and_an_unknown_backend_are_refused(self):
        with self.assertRaises(ValueError):
            calcs.call("kmeans", {"data": self.features, "k": 0, "seed": 1})
        with self.assertRaises(ValueError):
            calcs.call("kmeans", {"data": self.features, "k": 3, "seed": 1, "backend": "cuda"})

    def test_predict_puts_new_rows_in_the_nearest_cluster(self):
        model = calcs.call("kmeans", {"data": self.features, "k": 3, "seed": 9, "backend": "np"})
        again = calcs.call("kmeans_predict", {"model": model, "data": self.features})
        self.assertEqual(again["labels"], model["labels"])

    def test_the_silhouette_of_the_found_clusters_is_high(self):
        model = calcs.call("kmeans", {"data": self.features, "k": 3, "seed": 9, "backend": "np"})
        scored = calcs.call("silhouette", {"data": self.features, "labels": model["labels"], "backend": "np"})
        self.assertGreater(scored["mean"], 0.7)


class Pca(unittest.TestCase):
    def setUp(self):
        self.data = features_of(blobs(seed=52, n=90, k=3, d=4, spread=0.8))
        self.rows = core.as_rows(self.data)

    def test_components_and_variance_against_numpy_svd(self):
        """the oracle: numpy's own svd of the centred matrix, read straight off."""
        got = calcs.call("pca", {"data": self.data, "n_components": 3})
        x = np.asarray(self.rows)
        centred = x - x.mean(0)
        _, s, vt = np.linalg.svd(centred, full_matrices=False)
        variance = (s**2) / (len(self.rows) - 1)
        self.assertTrue(core.close(got["explained_variance"], variance[:3].tolist(), 1e-10))
        for mine, theirs in zip(got["components"], vt[:3].tolist()):
            aligned = theirs if np.dot(mine, theirs) > 0 else [-v for v in theirs]
            self.assertTrue(core.close(mine, aligned, 1e-9))

    def test_the_python_backend_finds_the_same_subspace(self):
        a = calcs.call("pca", {"data": self.data, "n_components": 2, "backend": "np"})
        b = calcs.call("pca", {"data": self.data, "n_components": 2, "backend": "py"})
        self.assertTrue(core.close(a["explained_variance"], b["explained_variance"], 1e-6))
        for mine, theirs in zip(a["components"], b["components"]):
            self.assertTrue(core.close(mine, theirs, 1e-5) or core.close(mine, [-v for v in theirs], 1e-5))

    def test_the_ratios_sum_to_one_when_every_component_is_kept(self):
        got = calcs.call("pca", {"data": self.data})
        self.assertAlmostEqual(sum(got["explained_variance_ratio"]), 1.0, places=9)

    def test_the_components_are_orthonormal(self):
        got = calcs.call("pca", {"data": self.data, "n_components": 3})
        c = np.asarray(got["components"])
        self.assertTrue(core.close((c @ c.T).tolist(), np.eye(3).tolist(), 1e-9))

    def test_the_scores_reconstruct_the_rows(self):
        got = calcs.call("pca", {"data": self.data})
        rebuilt = (np.asarray(got["scores"]) @ np.asarray(got["components"])) + np.asarray(got["mean"])
        self.assertTrue(core.close(rebuilt.tolist(), [list(r) for r in self.rows], 1e-8))

    def test_the_sign_is_pinned_so_the_part_is_stable(self):
        a = calcs.call("pca", {"data": self.data, "n_components": 2})
        b = calcs.call("pca", {"data": self.data, "n_components": 2})
        self.assertEqual(a["components"], b["components"])
        for component in a["components"]:
            at = max(range(len(component)), key=lambda i: abs(component[i]))
            self.assertGreater(component[at], 0.0)


class Hierarchical(unittest.TestCase):
    def setUp(self):
        self.data = features_of(blobs(seed=53, n=24, k=3, d=2, spread=0.35))
        self.rows = [list(row) for row in core.as_rows(self.data)]

    def test_the_merge_heights_match_scipy(self):
        """the oracle: scipy's own linkage, whose merge heights are the same numbers."""
        for linkage in ("single", "complete", "average"):
            got = calcs.call("hierarchical", {"data": self.data, "linkage": linkage, "k": 3})
            theirs = hierarchy.linkage(distance.pdist(np.asarray(self.rows)), method=linkage)
            self.assertTrue(core.close(got["heights"], theirs[:, 2].tolist(), 1e-9), linkage)

    def test_the_heights_never_fall_under_complete_linkage(self):
        got = calcs.call("hierarchical", {"data": self.data, "linkage": "complete", "k": 2})
        for before, after in zip(got["heights"], got["heights"][1:]):
            self.assertLessEqual(before, after + 1e-12)

    def test_cutting_at_k_gives_k_clusters(self):
        for k in (2, 3, 5):
            got = calcs.call("hierarchical", {"data": self.data, "linkage": "complete", "k": k})
            self.assertEqual(len(set(got["labels"])), k)

    def test_an_unknown_linkage_is_refused(self):
        with self.assertRaises(ValueError):
            calcs.call("hierarchical", {"data": self.data, "linkage": "ward"})

    def test_single_linkage_finds_the_blobs_when_they_are_far_apart(self):
        data = blobs(seed=54, n=30, k=3, d=2, spread=0.2)
        got = calcs.call("hierarchical", {"data": features_of(data), "linkage": "single", "k": 3})
        pairing = {}
        for label, truth in zip(got["labels"], [int(r[-1]) for r in core.as_rows(data)]):
            pairing.setdefault(label, set()).add(truth)
        self.assertTrue(all(len(v) == 1 for v in pairing.values()))


class Dbscan(unittest.TestCase):
    def test_it_finds_two_clusters_and_calls_the_outlier_noise(self):
        rows = [[0.0, 0.0], [0.1, 0.0], [0.0, 0.1], [0.1, 0.1],
                [5.0, 5.0], [5.1, 5.0], [5.0, 5.1], [5.1, 5.1],
                [50.0, 50.0]]
        data = core.dataset("two tight groups and one stray", ["x0", "x1"], rows)
        got = calcs.call("dbscan", {"data": data, "eps": 0.5, "min_samples": 3})
        self.assertEqual(got["clusters"], 2)
        self.assertEqual(got["noise"], 1)
        self.assertEqual(got["labels"][-1], -1)
        self.assertEqual(len(set(got["labels"][:4])), 1)
        self.assertNotEqual(got["labels"][0], got["labels"][4])

    def test_backends_agree(self):
        data = features_of(blobs(seed=55, n=60, k=3, d=2, spread=0.4))
        a = calcs.call("dbscan", {"data": data, "eps": 1.2, "min_samples": 4, "backend": "py"})
        b = calcs.call("dbscan", {"data": data, "eps": 1.2, "min_samples": 4, "backend": "np"})
        self.assertEqual(a["labels"], b["labels"])
        self.assertEqual(a["core_points"], b["core_points"])

    def test_a_tiny_eps_makes_everything_noise(self):
        data = features_of(blobs(seed=56, n=30, k=2, d=2, spread=0.5))
        got = calcs.call("dbscan", {"data": data, "eps": 1e-6, "min_samples": 3})
        self.assertEqual(got["clusters"], 0)
        self.assertEqual(got["noise"], 30)

    def test_it_finds_the_blobs_without_being_told_how_many(self):
        data = blobs(seed=57, n=90, k=3, d=2, spread=0.3)
        got = calcs.call("dbscan", {"data": features_of(data), "eps": 2.0, "min_samples": 4})
        self.assertEqual(got["clusters"], 3)
        self.assertEqual(got["noise"], 0)
