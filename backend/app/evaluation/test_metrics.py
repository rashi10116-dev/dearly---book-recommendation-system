"""
Unit tests for Scientific Recommendation Metrics
Tests Precision@K, Recall@K, NDCG@K, ILD@K, and EPC@K on manually verifiable examples.
"""

import math
import numpy as np

from .metrics import (
    precision_at_k,
    recall_at_k,
    dcg_at_k,
    ndcg_at_k,
    intra_list_diversity,
    expected_popularity_complement
)

def test_precision_at_k():
    recommended = [101, 102, 103, 104, 105, 106]
    relevant = {101, 103, 108}

    # At K=2: items [101, 102] -> hits = 1 (101) -> 1/2 = 0.5
    assert precision_at_k(recommended, relevant, k=2) == 0.5

    # At K=5: items [101, 102, 103, 104, 105] -> hits = 2 (101, 103) -> 2/5 = 0.4
    assert precision_at_k(recommended, relevant, k=5) == 0.4

    # At K=0: 0.0
    assert precision_at_k(recommended, relevant, k=0) == 0.0

    # No hits:
    assert precision_at_k([999, 998], relevant, k=2) == 0.0

def test_recall_at_k():
    recommended = [101, 102, 103, 104, 105]
    relevant = {101, 103, 108, 109} # 4 relevant items in total

    # At K=3: items [101, 102, 103] -> hits = 2 -> 2/4 = 0.5
    assert recall_at_k(recommended, relevant, k=3) == 0.5

    # At K=5: items [101, 102, 103, 104, 105] -> hits = 2 -> 2/4 = 0.5
    assert recall_at_k(recommended, relevant, k=5) == 0.5

    # Empty relevant:
    assert recall_at_k(recommended, set(), k=5) == 0.0

def test_dcg_and_ndcg_at_k():
    recommended = [1, 2, 3, 4, 5]
    relevant = {1, 3}

    # DCG@3:
    # rank 1: item 1 in relevant -> 1 / log2(2) = 1.0
    # rank 2: item 2 not in relevant -> 0
    # rank 3: item 3 in relevant -> 1 / log2(4) = 0.5
    # Actual DCG@3 = 1.0 + 0 + 0.5 = 1.5
    assert math.isclose(dcg_at_k(recommended, relevant, k=3), 1.5, rel_tol=1e-5)

    # Ideal ranking for K=3: relevant items at rank 1 and 2
    # IDCG@3 = 1 / log2(2) + 1 / log2(3) = 1.0 + 0.63092975 = 1.63092975
    # NDCG@3 = 1.5 / 1.63092975 = 0.91972
    expected_ndcg = 1.5 / (1.0 + 1.0 / math.log2(3))
    assert math.isclose(ndcg_at_k(recommended, relevant, k=3), expected_ndcg, rel_tol=1e-5)

    # Perfect ranking NDCG@K should be exactly 1.0
    perfect_rec = [1, 3, 2, 4, 5]
    assert math.isclose(ndcg_at_k(perfect_rec, relevant, k=2), 1.0, rel_tol=1e-5)

def test_intra_list_diversity():
    # 3 items with known orthogonal vectors
    vectors = {
        1: np.array([1.0, 0.0, 0.0]),
        2: np.array([0.0, 1.0, 0.0]),
        3: np.array([0.0, 0.0, 1.0])
    }
    # All pairwise cosine similarities are 0, so distances are (1 - 0) = 1.0
    # Mean ILD should be exactly 1.0 (maximum possible diversity)
    ild_orthogonal = intra_list_diversity([1, 2, 3], vectors, k=3)
    assert math.isclose(ild_orthogonal, 1.0, rel_tol=1e-5)

    # Identical vectors: cosine similarity = 1.0, distance = 0.0
    identical_vectors = {
        1: np.array([1.0, 2.0]),
        2: np.array([1.0, 2.0]),
        3: np.array([2.0, 4.0]) # same direction
    }
    ild_identical = intra_list_diversity([1, 2, 3], identical_vectors, k=3)
    assert math.isclose(ild_identical, 0.0, abs_tol=1e-5)

def test_expected_popularity_complement():
    # Popularity scores in [0, 100]
    popularities = {
        1: 90.0, # pop = 0.90 -> novelty = 0.10
        2: 80.0, # pop = 0.80 -> novelty = 0.20
        3: 30.0, # pop = 0.30 -> novelty = 0.70
        4: 20.0  # pop = 0.20 -> novelty = 0.80
    }

    # Popular items [1, 2]: mean novelty = (0.10 + 0.20) / 2 = 0.15
    assert math.isclose(expected_popularity_complement([1, 2], popularities, k=2), 0.15, rel_tol=1e-5)

    # Niche items [3, 4]: mean novelty = (0.70 + 0.80) / 2 = 0.75
    assert math.isclose(expected_popularity_complement([3, 4], popularities, k=2), 0.75, rel_tol=1e-5)

if __name__ == "__main__":
    test_precision_at_k()
    test_recall_at_k()
    test_dcg_and_ndcg_at_k()
    test_intra_list_diversity()
    test_expected_popularity_complement()
    print("All unit tests for recommendation metrics PASSED!")
