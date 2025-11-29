from unittest.mock import MagicMock


def create_mock_firestore():
    """Create a mock Firestore client for testing."""
    mock = MagicMock()
    mock_collection = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = False
    mock_doc.to_dict.return_value = {}

    mock.collection.return_value = mock_collection
    mock_collection.document.return_value.get.return_value = mock_doc
    mock_collection.stream.return_value = []

    return mock


def create_mock_firebase_user(
    uid="test-user-123", email="test@example.com", email_verified=True
):
    """Create a mock Firebase user claims dict."""
    return {
        "uid": uid,
        "email": email,
        "email_verified": email_verified,
    }
