"""
DEARLY Evaluation Recommendation Models
Defines the three comparison baselines:
1. PopularityRecommender: Pure popularity-based baseline.
2. StandardContentBasedRecommender: TF-IDF cosine similarity without MMR or anti-popularity.
3. DearlyRecommender: Full DEARLY model with TF-IDF taste vector, MMR diversity reranking, and anti-popularity bonus.
"""

from typing import List, Dict, Set, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class PopularityRecommender:
    """Baseline 1: Ranks candidate items solely by global popularity."""
    def __init__(self, items: List[Any]):
        self.items = sorted(items, key=lambda x: x.popularity, reverse=True)

    def recommend(self, user_data: Dict[str, Any], top_k: int = 10) -> List[int]:
        excluded = user_data["train_item_ids"]
        recs = [item.id for item in self.items if item.id not in excluded]
        return recs[:top_k]

class StandardContentBasedRecommender:
    """Baseline 2: Content-based TF-IDF cosine similarity without MMR or anti-popularity adjustments."""
    def __init__(self, items: List[Any]):
        self.items = items
        self.item_ids = [item.id for item in items]
        self.item_id_to_idx = {item.id: idx for idx, item in enumerate(items)}
        
        # Build text corpus
        corpus = [
            f"{item.title} {item.author} {item.genre} {' '.join(item.tropes)} {item.description}"
            for item in items
        ]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def recommend(self, user_data: Dict[str, Any], top_k: int = 10) -> List[int]:
        excluded = user_data["train_item_ids"]
        train_interactions = user_data["train_interactions"]
        
        # User profile = average vector of training items with positive rating (>= 4.0)
        pos_indices = [
            self.item_id_to_idx[b_id]
            for b_id, r in train_interactions
            if r >= 4.0 and b_id in self.item_id_to_idx
        ]
        
        if pos_indices:
            user_vec = np.asarray(self.tfidf_matrix[pos_indices].mean(axis=0)).reshape(1, -1)
        else:
            # Fallback to genres text
            query = " ".join(user_data.get("fav_genres", []))
            user_vec = self.vectorizer.transform([query]).toarray()

        sim_scores = cosine_similarity(user_vec, self.tfidf_matrix)[0]

        # Rank all unread items strictly by similarity
        candidates = [
            (item.id, sim_scores[idx])
            for idx, item in enumerate(self.items)
            if item.id not in excluded
        ]
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [cid for cid, _ in candidates[:top_k]]

class DearlyRecommender:
    """Model 3: DEARLY Content-based system with Taste Profile, MMR diversity reranking, and Anti-Popularity scoring."""
    def __init__(self, items: List[Any]):
        self.items = items
        self.item_ids = [item.id for item in items]
        self.item_id_to_idx = {item.id: idx for idx, item in enumerate(items)}
        self.item_id_to_item = {item.id: item for item in items}

        corpus = [
            f"{item.title} {item.author} {item.genre} {' '.join(item.tropes * 2)} {item.description}"
            for item in items
        ]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def recommend(self, user_data: Dict[str, Any], top_k: int = 10, lambda_param: float = 0.70) -> List[int]:
        excluded = user_data["train_item_ids"]
        fav_genres = user_data.get("fav_genres", [])
        fav_tropes = set(user_data.get("fav_tropes", []))

        # 1. Base query from onboarding taste profile
        query_parts = list(fav_genres * 2) + (list(fav_tropes) * 2)
        query_text = " ".join(query_parts)
        if query_text:
            user_vec = self.vectorizer.transform([query_text]).toarray()[0]
        else:
            user_vec = np.zeros(self.tfidf_matrix.shape[1])

        # 2. Add feedback from training reading history
        for b_id, rating in user_data["train_interactions"]:
            if b_id in self.item_id_to_idx:
                idx = self.item_id_to_idx[b_id]
                book_vec = self.tfidf_matrix[idx].toarray()[0]
                weight = 1.2 if rating >= 4.5 else (0.8 if rating >= 4.0 else -0.8)
                user_vec += weight * book_vec

        norm = np.linalg.norm(user_vec)
        if norm > 0:
            user_vec = user_vec / norm

        # 3. Compute cosine similarities
        sim_scores = cosine_similarity(user_vec.reshape(1, -1), self.tfidf_matrix)[0]

        # 4. Score candidates with trope overlap and anti-popularity bonus
        scored = []
        for idx, item in enumerate(self.items):
            if item.id in excluded:
                continue
            base_sim = float(sim_scores[idx])
            
            # Narrative trope multiplier
            matched_tropes = len(set(item.tropes).intersection(fav_tropes))
            trope_mult = 1.0 + (0.15 * matched_tropes)
            
            # Anti-popularity bonus for lesser-circulated books (popularity < 70)
            pop = item.popularity
            novelty_mult = 1.0 + max(0.0, (70.0 - pop) / 100.0)

            final_score = base_sim * trope_mult * novelty_mult
            scored.append({
                "id": item.id,
                "idx": idx,
                "score": final_score
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        if not scored:
            return []

        # 5. Maximal Marginal Relevance (MMR) diversity reranking
        selected_indices = [scored[0]["idx"]]
        remaining = list(scored[1:])

        while len(selected_indices) < min(top_k, len(scored)) and remaining:
            best_mmr = -float("inf")
            best_cand = None

            for cand in remaining:
                c_idx = cand["idx"]
                rel = cand["score"]
                
                # Max similarity to currently selected
                cand_v = self.tfidf_matrix[c_idx]
                selected_v = self.tfidf_matrix[selected_indices]
                intra_sim = cosine_similarity(cand_v, selected_v).max()

                mmr = lambda_param * rel - (1.0 - lambda_param) * intra_sim
                if mmr > best_mmr:
                    best_mmr = mmr
                    best_cand = cand

            if best_cand is not None:
                selected_indices.append(best_cand["idx"])
                remaining.remove(best_cand)
            else:
                break

        return [self.item_ids[idx] for idx in selected_indices]
