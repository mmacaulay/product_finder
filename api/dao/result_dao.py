from google.cloud import firestore
from django.utils import timezone
from datetime import timedelta
from api.firestore_client import FirestoreClient


class LLMQueryResultDAO:
    COLLECTION = "llm_query_results"

    def __init__(self):
        self.db = FirestoreClient.get_client()
        self.collection = self.db.collection(self.COLLECTION)

    def _make_id(self, product_upc: str, prompt_name: str, provider: str) -> str:
        """Create composite document ID."""
        return f"{product_upc}_{prompt_name}_{provider}"

    def create_or_update(
        self,
        product_upc: str,
        prompt_name: str,
        provider: str,
        query_input: str,
        result: dict,
        metadata: dict = None,
        schema_version: str = "1.0",
        parse_attempts: int = 1,
        parse_strategy: str = None,
    ) -> dict:
        """Create or update a cached result."""
        doc_id = self._make_id(product_upc, prompt_name, provider)
        doc_ref = self.collection.document(doc_id)

        data = {
            "product_upc": product_upc,
            "prompt_name": prompt_name,
            "provider": provider,
            "query_input": query_input,
            "result": result,
            "metadata": metadata or {},
            "schema_version": schema_version,
            "parse_attempts": parse_attempts,
            "parse_strategy": parse_strategy,
            "is_stale": False,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        doc_ref.set(data)
        return self._doc_to_dict(doc_ref.get())

    def get(self, product_upc: str, prompt_name: str, provider: str) -> dict | None:
        """Get cached result by composite key."""
        doc_id = self._make_id(product_upc, prompt_name, provider)
        doc = self.collection.document(doc_id).get()
        return self._doc_to_dict(doc) if doc.exists else None

    def is_fresh(self, result: dict, ttl_days: int = 30) -> bool:
        """Check if a cached result is still fresh."""
        if result.get("is_stale"):
            return False

        created_at = result.get("created_at")
        if not created_at:
            return False

        age = timezone.now() - created_at
        return age < timedelta(days=ttl_days)

    def mark_stale(self, product_upc: str, prompt_name: str, provider: str) -> bool:
        """Mark a result as stale."""
        doc_id = self._make_id(product_upc, prompt_name, provider)
        doc_ref = self.collection.document(doc_id)

        if not doc_ref.get().exists:
            return False

        doc_ref.update({"is_stale": True, "updated_at": firestore.SERVER_TIMESTAMP})
        return True

    def get_by_product(self, product_upc: str) -> list[dict]:
        """Get all results for a product."""
        query = self.collection.where("product_upc", "==", product_upc)
        return [self._doc_to_dict(doc) for doc in query.stream()]

    def _doc_to_dict(self, doc) -> dict:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
