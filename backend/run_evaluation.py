import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.evaluation.evaluator import run_scientific_evaluation

if __name__ == "__main__":
    print("=" * 60)
    print("Running DEARLY Scientific Recommendation Evaluation...")
    print("=" * 60)
    report = run_scientific_evaluation()
    print("\nSummary of Results:")
    for model, m in report["results"].items():
        print(f"\n{model}:")
        print(f"  Precision@5: {m['p@5']:.4f} | Recall@5: {m['r@5']:.4f} | NDCG@5: {m['ndcg@5']:.4f}")
        print(f"  ILD@5 (Diversity): {m['ild@5']:.4f} | EPC@5 (Novelty): {m['epc@5']:.4f}")
        print(f"  Precision@10: {m['p@10']:.4f} | Recall@10: {m['r@10']:.4f} | NDCG@10: {m['ndcg@10']:.4f}")
        print(f"  ILD@10 (Diversity): {m['ild@10']:.4f} | EPC@10 (Novelty): {m['epc@10']:.4f}")

