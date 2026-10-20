import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from collection_state import activate_collection, read_active_collection
from retrieval import filter_by_max_distance, retrieve_context


class CollectionStateTests(unittest.TestCase):
    def test_activation_replaces_active_collection_pointer(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pointer = Path(temp_dir) / "active_collection"
            pointer.write_text("old_collection", encoding="utf-8")

            activate_collection("new_collection", pointer)

            self.assertEqual(read_active_collection("default", pointer), "new_collection")
            self.assertEqual(list(Path(temp_dir).iterdir()), [pointer])

    def test_missing_pointer_uses_configured_collection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pointer = Path(temp_dir) / "active_collection"

            self.assertEqual(read_active_collection("configured", pointer), "configured")


class RetrievalTests(unittest.TestCase):
    def test_filters_out_matches_beyond_maximum_distance(self):
        close = object()
        far = object()

        results = filter_by_max_distance([(close, 0.2), (far, 0.7)], 0.5)

        self.assertEqual(results, [(close, 0.2)])

    def test_invalid_distance_limit_is_rejected(self):
        with self.assertRaises(ValueError):
            filter_by_max_distance([], float("nan"))

    def test_retrieve_context_keeps_only_close_chunks(self):
        class VectorStore:
            def similarity_search_with_score(self, question, k):
                self.query = (question, k)
                return [(type("Document", (), {"page_content": "Relevant passage"})(), 0.2),
                        (type("Document", (), {"page_content": "Unrelated passage"})(), 0.8)]

        store = VectorStore()

        context = retrieve_context(store, "question", k=10, max_distance=0.5)

        self.assertEqual(context, "Relevant passage")
        self.assertEqual(store.query, ("question", 10))

    def test_retrieve_context_is_empty_when_no_chunk_passes_threshold(self):
        class VectorStore:
            def similarity_search_with_score(self, question, k):
                return [(type("Document", (), {"page_content": "Far passage"})(), 0.8)]

        self.assertEqual(retrieve_context(VectorStore(), "question", 10, 0.5), "")


if __name__ == "__main__":
    unittest.main()
