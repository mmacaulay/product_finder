from google.cloud import firestore
from django.conf import settings
import os


class FirestoreClient:
    """Singleton Firestore client."""

    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            # Support emulator for local dev
            emulator = getattr(settings, "FIRESTORE_EMULATOR_HOST", None)
            if emulator:
                os.environ["FIRESTORE_EMULATOR_HOST"] = emulator

            project_id = getattr(settings, "FIRESTORE_PROJECT_ID", None)
            cls._client = firestore.Client(project=project_id)

        return cls._client
