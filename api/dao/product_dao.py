from google.cloud import firestore
from api.firestore_client import FirestoreClient


class ProductDAO:
    COLLECTION = "products"

    def __init__(self):
        self.db = FirestoreClient.get_client()
        self.collection = self.db.collection(self.COLLECTION)

    def create(
        self,
        upc_code: str,
        current_provider: str = None,
        **provider_data_fields,
    ) -> dict:
        """
        Create a product. Uses UPC as document ID for uniqueness.

        Args:
            upc_code: The UPC code
            current_provider: The API provider currently reflected in top-level fields
            **provider_data_fields: Additional fields including provider-specific raw data
                                   (e.g., de_product_data={...}, barcodes_data_data={...})
        """
        doc_ref = self.collection.document(upc_code)

        # Check if exists
        if doc_ref.get().exists:
            raise ValueError(f"Product {upc_code} already exists")

        data = {
            "upc_code": upc_code,
            "current_provider": current_provider,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        # Add any additional fields (name, brand, image_url, provider data, etc.)
        data.update(provider_data_fields)

        doc_ref.set(data)
        return self._doc_to_dict(doc_ref.get())

    def get_by_upc(self, upc_code: str) -> dict | None:
        """Get product by UPC code."""
        doc = self.collection.document(upc_code).get()
        return self._doc_to_dict(doc) if doc.exists else None

    def get_all(self, limit: int = 100) -> list[dict]:
        """Get all products."""
        docs = self.collection.limit(limit).stream()
        return [self._doc_to_dict(doc) for doc in docs]

    def update(self, upc_code: str, **fields) -> dict | None:
        """Update product fields."""
        doc_ref = self.collection.document(upc_code)
        if not doc_ref.get().exists:
            return None

        fields["updated_at"] = firestore.SERVER_TIMESTAMP
        doc_ref.update(fields)
        return self._doc_to_dict(doc_ref.get())

    def delete(self, upc_code: str) -> bool:
        """Delete a product."""
        doc_ref = self.collection.document(upc_code)
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True

    def _doc_to_dict(self, doc) -> dict:
        """Convert Firestore document to dict with ID."""
        data = doc.to_dict()
        data["id"] = doc.id
        return data
