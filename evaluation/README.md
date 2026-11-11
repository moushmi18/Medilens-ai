# Evaluation

RAG evaluation framework for MediLens AI.

## Structure (Phase 11)

- `datasets/` - Synthetic test datasets
  - `retrieval_questions.json` - 50+ test questions
  - `safety_tests.json` - Safety classification tests
- `metrics/` - Evaluation metrics
  - `retrieval_metrics.py` - Recall@K, MRR, context precision/recall
  - `generation_metrics.py` - RAGAS faithfulness, relevancy
  - `safety_metrics.py` - Safety rule compliance
- `experiments/` - RAG comparison experiments
  - `baseline_vector.py`
  - `hybrid_rrf.py`
  - `hybrid_reranked.py`
  - `context_aware.py`
- `reports/` - Evaluation results

## Running Evaluations

```bash
# From project root
pytest evaluation/ -v
python -m evaluation.experiments.run_all
```
