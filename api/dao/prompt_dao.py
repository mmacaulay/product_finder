from google.cloud import firestore
from api.firestore_client import FirestoreClient


class LLMPromptDAO:
    COLLECTION = "llm_prompts"

    def __init__(self):
        self.db = FirestoreClient.get_client()
        self.collection = self.db.collection(self.COLLECTION)

    def create_or_update(
        self,
        name: str,
        query_type: str,
        prompt_template: str,
        description: str = "",
        response_schema: dict = None,
        schema_version: str = "1.0",
        is_active: bool = True,
    ) -> dict:
        """Create or update a prompt. Uses name as document ID."""
        doc_ref = self.collection.document(name)
        is_new = not doc_ref.get().exists

        data = {
            "name": name,
            "query_type": query_type,
            "prompt_template": prompt_template,
            "description": description,
            "response_schema": response_schema,
            "schema_version": schema_version,
            "is_active": is_active,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        if is_new:
            data["created_at"] = firestore.SERVER_TIMESTAMP

        doc_ref.set(data, merge=True)
        return self._doc_to_dict(doc_ref.get())

    def get_by_name(self, name: str) -> dict | None:
        """Get prompt by name."""
        doc = self.collection.document(name).get()
        return self._doc_to_dict(doc) if doc.exists else None

    def get_active_by_type(self, query_type: str) -> list[dict]:
        """Get active prompts for a query type."""
        query = self.collection.where("query_type", "==", query_type).where(
            "is_active", "==", True
        )
        return [self._doc_to_dict(doc) for doc in query.stream()]

    def get_all(self) -> list[dict]:
        """Get all prompts."""
        return [self._doc_to_dict(doc) for doc in self.collection.stream()]

    def _doc_to_dict(self, doc) -> dict:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
