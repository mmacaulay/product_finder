import os
import logging
from google.cloud import firestore
from django.conf import settings
from django.utils import timezone
from google.api_core.exceptions import AlreadyExists

logger = logging.getLogger(__name__)

class FirestoreClient:
    _instance = None
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            project_id = settings.FIRESTORE_PROJECT_ID

            # Check for emulator
            emulator_host = settings.FIRESTORE_EMULATOR_HOST
            if emulator_host:
                os.environ["FIRESTORE_EMULATOR_HOST"] = emulator_host
                logger.info(f"Using Firestore Emulator at {emulator_host}")

            try:
                if settings.FIRESTORE_CREDENTIALS:
                    cls._client = firestore.Client.from_service_account_json(
                        settings.FIRESTORE_CREDENTIALS,
                        project=project_id
                    )
                else:
                    cls._client = firestore.Client(project=project_id)
            except Exception as e:
                logger.error(f"Failed to initialize Firestore client: {e}")
                raise

        return cls._client

class BaseDAO:
    collection_name = ''

    def __init__(self):
        self.client = FirestoreClient.get_client()
        self.collection = self.client.collection(self.collection_name)

    def _to_dict(self, doc):
        if not doc.exists:
            return None
        data = doc.to_dict()
        data['id'] = doc.id
        return data

class ProductDAO(BaseDAO):
    collection_name = 'products'

    def create(self, upc_code, name, brand=None, image_url=None, de_product_data=None):
        # Use UPC as document ID for easy lookup and uniqueness
        doc_ref = self.collection.document(upc_code)

        data = {
            'upc_code': upc_code,
            'name': name,
            'brand': brand,
            'image_url': image_url,
            'de_product_data': de_product_data,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }

        try:
            doc_ref.create(data)
        except AlreadyExists:
            raise ValueError(f"Product with UPC {upc_code} already exists")

        # Refetch to get actual server timestamps
        return self._to_dict(doc_ref.get())

    def get_by_upc(self, upc_code):
        doc = self.collection.document(upc_code).get()
        return self._to_dict(doc)

    def get_all(self):
        docs = self.collection.stream()
        return [self._to_dict(doc) for doc in docs]

    def update(self, upc_code, **kwargs):
        doc_ref = self.collection.document(upc_code)
        if not doc_ref.get().exists:
            return None

        kwargs['updated_at'] = firestore.SERVER_TIMESTAMP
        doc_ref.update(kwargs)
        return self._to_dict(doc_ref.get())

    def delete(self, upc_code):
        self.collection.document(upc_code).delete()

class LLMPromptDAO(BaseDAO):
    collection_name = 'llm_prompts'

    def create(self, name, query_type, prompt_template, description='', response_schema=None, schema_version='1.0', is_active=True):
        # Use name as document ID for uniqueness
        # Uses .set() for upsert behavior - allows seed command to update existing prompts
        doc_ref = self.collection.document(name)

        data = {
            'name': name,
            'query_type': query_type,
            'prompt_template': prompt_template,
            'description': description,
            'response_schema': response_schema,
            'schema_version': schema_version,
            'is_active': is_active,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        doc_ref.set(data)
        return self._to_dict(doc_ref.get())

    def get_by_name(self, name):
        doc = self.collection.document(name).get()
        return self._to_dict(doc)

    def get_active_by_type(self, query_type):
        query = self.collection.where('query_type', '==', query_type).where('is_active', '==', True)
        docs = query.stream()
        return [self._to_dict(doc) for doc in docs]

    def update(self, name, **kwargs):
        doc_ref = self.collection.document(name)
        if not doc_ref.get().exists:
            return None

        kwargs['updated_at'] = firestore.SERVER_TIMESTAMP
        doc_ref.update(kwargs)
        return self._to_dict(doc_ref.get())

class LLMQueryResultDAO(BaseDAO):
    collection_name = 'llm_query_results'

    def create(self, product_upc, prompt_name, provider, query_input, result, schema_version='1.0', parse_attempts=1, parse_strategy=None, metadata=None):
        # Create a composite ID or let Firestore generate one?
        # Let's use a composite ID for easy lookup: {product_upc}_{prompt_name}_{provider}
        # Note: Firestore IDs have limits, but these should be safe.
        doc_id = f"{product_upc}_{prompt_name}_{provider}"
        doc_ref = self.collection.document(doc_id)

        data = {
            'product_upc': product_upc, # Store reference by ID (UPC)
            'prompt_name': prompt_name, # Store reference by ID (name)
            'provider': provider,
            'query_input': query_input,
            'result': result,
            'schema_version': schema_version,
            'parse_attempts': parse_attempts,
            'parse_strategy': parse_strategy,
            'metadata': metadata or {},
            'is_stale': False,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        doc_ref.set(data)
        return self._to_dict(doc_ref)

    def get_by_composite_key(self, product_upc, prompt_name, provider):
        doc_id = f"{product_upc}_{prompt_name}_{provider}"
        doc = self.collection.document(doc_id).get()
        return self._to_dict(doc)

    def mark_stale(self, product_upc, prompt_name, provider):
        doc_id = f"{product_upc}_{prompt_name}_{provider}"
        doc_ref = self.collection.document(doc_id)
        if doc_ref.get().exists:
            doc_ref.update({'is_stale': True, 'updated_at': firestore.SERVER_TIMESTAMP})
