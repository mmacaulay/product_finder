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

            # Cloud Run provides credentials automatically via Application Default Credentials (ADC)
            # No need to explicitly pass credentials - the service account configured in Terraform
            # (with roles/datastore.user permission) is automatically used
            project_id = getattr(settings, "FIRESTORE_PROJECT_ID", None)
            database = getattr(settings, "FIRESTORE_DATABASE", "(default)")
            cls._client = firestore.Client(project=project_id, database=database)

        return cls._client
