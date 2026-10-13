"""Small authored Chinese cross-language retrieval set; not production accuracy."""
import argparse
import hashlib
import json
import time
from pathlib import Path

from app.config import Settings
from app.knowledge import Knowledge
from app.model import Model, NoEvidenceError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-llm', action='store_true')
    parser.add_argument('--output', default='reports/document-evaluation.json')
    args = parser.parse_args()
    started = time.perf_counter()
    raw = Path('tests/fixtures/document_queries.json').read_bytes()
    dataset = json.loads(raw)
    settings = Settings(model_mode='openai' if args.with_llm else 'offline', retrieval_mode='chroma', knowledge_source='documents')
    knowledge = Knowledge(settings)
    rows = []
    for case in dataset['cases']:
        hits = knowledge.search(case['query'], threshold=0)
        ranks = [i+1 for i, h in enumerate(hits) if h['doc_id'] in case['expected_docs']]
        rows.append({**case, 'raw_hit_at_5': bool(ranks), 'reciprocal_rank': 1/min(ranks) if ranks else 0,
                     'hits': [{'id': h['id'], 'doc_id': h['doc_id'], 'score': h['score']} for h in hits]})
        print(f"Retrieved {case['id']}", flush=True)
    calibration = [r for r in rows if r['split'] == 'calibration']
    # Threshold chosen only on calibration queries; tie-break toward greater precision.
    def balanced_accuracy(t):
        pos = [r for r in calibration if r['expected_docs']]
        neg = [r for r in calibration if not r['expected_docs']]
        return (sum(bool(r['hits']) and r['hits'][0]['score'] >= t for r in pos)/len(pos)
                + sum(not r['hits'] or r['hits'][0]['score'] < t for r in neg)/len(neg))/2
    threshold = max((i/100 for i in range(10, 81)), key=lambda t: (balanced_accuracy(t), t))
    test = [r for r in rows if r['split'] == 'test']
    pos = [r for r in test if r['expected_docs']]
    neg = [r for r in test if not r['expected_docs']]
    for row in rows:
        row['accepted'] = bool(row['hits']) and row['hits'][0]['score'] >= threshold
        row['filtered_hit_at_5'] = any(h['doc_id'] in row['expected_docs'] and h['score'] >= threshold for h in row['hits'])
    report = {'corpus': {k: v for k, v in knowledge.inventory().items() if k != 'documents'},
              'embedding_model': settings.embedding_model, 'dataset_sha256': hashlib.sha256(raw).hexdigest(),
              'calibration_count': len(calibration), 'test_positive_count': len(pos), 'test_negative_count': len(neg),
              'threshold': threshold, 'threshold_method': 'max balanced accuracy on calibration only; higher threshold breaks ties',
              'raw_document_recall_at_5': sum(r['raw_hit_at_5'] for r in pos)/len(pos),
              'filtered_document_recall_at_5': sum(r['filtered_hit_at_5'] for r in pos)/len(pos),
              'mrr_at_5': sum(r['reciprocal_rank'] for r in pos)/len(pos),
              'negative_false_accept_count': sum(r['accepted'] for r in neg),
              'positive_rejection_count': sum(not r['accepted'] for r in pos), 'cases': rows,
              'limitations': 'Hand-authored small corpus-specific set. Document hits do not establish answer correctness or evidence sufficiency. No production claims.',
              'llm_examples': []}
    if args.with_llm:
        model = Model(settings)
        try:
            for case in [c for c in dataset['cases'] if c.get('llm_check')]:
                hits = knowledge.search(case['query'], threshold=threshold)
                example = {'id': case['id'], 'query': case['query'], 'expected_answerable': bool(case['expected_docs'])}
                try:
                    example.update(model.answer_grounded(case['query'], [], hits))
                    example['status'] = 'answered'
                except NoEvidenceError:
                    example['status'] = 'abstained'
                except Exception as exc:
                    example['status'] = 'failed'
                    example['error_type'] = type(exc).__name__
                report['llm_examples'].append(example)
        finally:
            model.close()
    report['elapsed_seconds'] = round(time.perf_counter()-started, 2)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('cases', 'llm_examples')}, ensure_ascii=False, indent=2))
    print(f'LLM examples: {len(report["llm_examples"])}; report: {output}')


if __name__ == '__main__':
    main()
