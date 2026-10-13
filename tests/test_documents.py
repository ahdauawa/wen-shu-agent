import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import Settings
from app.documents import load_documents, make_chunks
from app.knowledge import Knowledge
from app.main import create_app
from app.model import Model, NoEvidenceError


class DocumentTests(unittest.TestCase):
    def test_corpus_provenance_and_exact_coordinates(self):
        docs = load_documents(Path('knowledge/zulip'))
        self.assertEqual(len(docs), 27)
        self.assertFalse(any(d['modified_locally'] for d in docs))
        lookup = {d['id']: d for d in docs}
        chunks = make_chunks(docs)
        self.assertGreater(len(chunks), len(docs))
        for c in chunks:
            text = lookup[c['doc_id']]['text']
            self.assertEqual(c['answer'], text[c['char_start']:c['char_end']])
            self.assertLessEqual(len(c['answer']), 800)
            self.assertEqual(c['line_start'], text.count('\n', 0, c['char_start']) + 1)
            self.assertTrue(c['upstream_url'].startswith('https://github.com/zulip/zulip/blob/'))

    def test_document_changes_invalidate_index_and_remove_old_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'documents').mkdir()
            file = root / 'documents' / 'guide.md'
            file.write_text('# Guide\nreset password with email', encoding='utf-8')
            settings = Settings(_env_file=None, knowledge_dir=root, retrieval_mode='lexical', model_mode='offline')
            first = Knowledge(settings)
            file.write_text('# Guide\nreset password with administrator', encoding='utf-8')
            second = Knowledge(settings)
            self.assertNotEqual(first.fingerprint, second.fingerprint)
            (root / 'documents' / 'new.txt').write_text('notification policy', encoding='utf-8')
            file.unlink()
            third = Knowledge(settings)
            self.assertNotEqual(second.fingerprint, third.fingerprint)
            self.assertEqual(len(third.documents), 1)
            self.assertFalse(any('administrator' in c['answer'] for c in third.chunks))

    def test_no_duplicate_trailing_chunk_and_overlap(self):
        doc = dict(id='d', title='t', text='abcdefghijk', url='', upstream_url='', revision='', path='d.md')
        chunks = make_chunks([doc], size=6, overlap=2)
        self.assertEqual([c['answer'] for c in chunks], ['abcdef', 'efghij', 'ijk'])
        with self.assertRaises(ValueError):
            make_chunks([doc], size=2, overlap=2)

    def test_document_endpoints_require_auth_and_return_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            settings = Settings(_env_file=None, api_keys='document-test-key', db_path=Path(temp)/'db.sqlite',
                                retrieval_mode='lexical', model_mode='offline', knowledge_source='documents')
            with TestClient(create_app(settings)) as client:
                self.assertEqual(client.get('/knowledge/documents').status_code, 401)
                headers = {'X-API-Key': 'document-test-key'}
                docs = client.get('/knowledge/documents', headers=headers).json()
                self.assertEqual(docs['document_count'], 27)
                doc = client.get('/knowledge/documents/zulip-change-your-password', headers=headers).json()
                self.assertIn('Forgot your password', doc['text'])
                self.assertEqual(client.get('/knowledge/documents/missing', headers=headers).status_code, 404)

    def test_generation_rejects_missing_or_fabricated_citations(self):
        model = Model(Settings(_env_file=None, model_mode='openai', llm_api_key='test-only'))
        evidence = [{'id': 'doc:0-3', 'answer': 'abc'}]
        try:
            for ids in ([], ['invented-id']):
                with patch.object(model, 'completion', return_value={'content': json.dumps(
                        {'answerable': True, 'answer': 'answer', 'citations': ids})}):
                    with self.assertRaises(ValueError):
                        model.answer_grounded('question', [], evidence)
            with patch.object(model, 'completion', return_value={'content': json.dumps(
                    {'answerable': False, 'answer': '', 'citations': []})}):
                with self.assertRaises(NoEvidenceError):
                    model.answer_grounded('unsupported question', [], evidence)
            with patch.object(model, 'completion', return_value={'content': json.dumps(
                    {'answerable': True, 'answer': 'grounded', 'citations': ['doc:0-3']})}):
                self.assertEqual(model.answer_grounded('question', [], evidence)['cited_ids'], ['doc:0-3'])
        finally:
            model.close()
