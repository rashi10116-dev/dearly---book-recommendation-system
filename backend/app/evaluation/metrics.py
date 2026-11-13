"""
DEARLY Scientific Recommendation Evaluation Metrics
Implements standard Information Retrieval and Recommender Systems metrics:
1. Precision@K: Fraction of top-K recommended items that are relevant.
2. Recall@K: Fraction of relevant items that appear in the top-K recommendations.
3. NDCG@K (Normalized Discounted Cumulative Gain): Position-weighted relevance metric.
4. Intra-List Diversity (ILD@K): Mean pairwise distance among recommended items.
5. Expected Popularity Complement (EPC@K): Novelty metric measuring reduction of popularity bias.
"""

import math
from typing import List, Set, Dict, Optional, Any
import numpy as np

def precision_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
    """
    Precision@K = |recommended[:k] ∩ relevant| / k
    """
    if k <= 0:
        return 0.0
    rec_k = recommended[:k]
    hits = sum(1 for item in rec_k if item in relevant)
    return hits / float(k)

def recall_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
    """
    Recall@K = |recommended[:k] ∩ relevant| / |relevant|
    Returns 0.0 if relevant set is empty.
    """
    if k <= 0 or not relevant:
        return 0.0
    rec_k = recommended[:k]
    hits = sum(1 for item in rec_k if item in relevant)
    return hits / float(len(relevant))

def dcg_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
    """
    Discounted Cumulative Gain at K with binary relevance:
    DCG@K = sum_{i=1}^k [ rel_i / log2(i + 1) ]
    where rel_i = 1 if recommended[i-1] in relevant else 0.
    """
    if k <= 0:
        return 0.0
    dcg = 0.0
    for i, item in enumerate(recommended[:k], 1):
        if item in relevant:
            dcg += 1.0 / math.log2(i + 1)
    return dcg

def ndcg_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
    """
    Normalized Discounted Cumulative Gain at K:
    NDCG@K = DCG@K / IDCG@K
    where IDCG@K is the ideal DCG if all relevant items were ranked first.
    Returns 0.0 if IDCG is 0.
    """
    if k <= 0 or not relevant:
        return 0.0
    
    actual_dcg = dcg_at_k(recommended, relevant, k)
    
    # Ideal DCG: top min(k, len(relevant)) slots are filled with relevant items
    ideal_count = min(k, len(relevant))
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_count + 1))
    
    if idcg == 0.0:
        return 0.0
    return actual_dcg / idcg

def intra_list_diversity(
    recommended: List[int],
    item_vectors: Dict[int, np.ndarray],
    k: int
) -> float:
    """
    Intra-List Diversity (ILD@K):
    Measures the average pairwise cosine distance (1 - cosine_similarity)
    between all pairs of distinct items in the top-K recommendations:
    ILD = [2 / (k * (k - 1))] * sum_{i < j} (1 - cos(v_i, v_j))
    Returns 0.0 if k < 2 or insufficient valid vectors.
    """
    if k < 2:
        return 0.0
    
    items = [item for item in recommended[:k] if item in item_vectors]
    n = len(items)
    if n < 2:
        return 0.0
    
    total_distance = 0.0
    pair_count = 0
    
    for i in range(n):
        v_i = item_vectors[items[i]]
        norm_i = np.linalg.norm(v_i)
        if norm_i == 0:
            continue
            
        for j in range(i + 1, n):
            v_j = item_vectors[items[j]]
            norm_j = np.linalg.norm(v_j)
            if norm_j == 0:
                continue
                
            cos_sim = float(np.dot(v_i, v_j) / (norm_i * norm_j))
            cos_sim = max(-1.0, min(1.0, cos_sim))
            distance = 1.0 - cos_sim
            total_distance += distance
            pair_count += 1
            
    if pair_count == 0:
        return 0.0
    return total_distance / float(pair_count)

def expected_popularity_complement(
    recommended: List[int],
    item_popularity: Dict[int, float],
    k: int
) -> float:
    """
    Expected Popularity Complement (EPC@K):
    Measures the degree of novelty by penalizing popular mainstream items:
    EPC@K = (1 / k) * sum_{i=1}^k [ 1 - pop(rec_i) ]
    where pop(rec_i) is the item's normalized popularity score in [0, 1].
    Higher EPC indicates higher novelty and lower popularity bias.
    """
    if k <= 0:
        return 0.0
    
    rec_k = recommended[:k]
    if not rec_k:
        return 0.0
        
    novelty_sum = 0.0
    for item in rec_k:
        # Normalized popularity: assume scale 0-100 if > 1.0, else [0, 1]
        raw_pop = item_popularity.get(item, 50.0)
        norm_pop = raw_pop / 100.0 if raw_pop > 1.0 else raw_pop
        norm_pop = max(0.0, min(1.0, norm_pop))
        novelty_sum += (1.0 - norm_pop)
        
    return novelty_sum / float(len(rec_k))

