from django.test import TestCase
from unittest.mock import patch
from api.tests.firestore_mocks import create_mock_firestore, create_mock_firebase_user
import responses


class FirestoreTestCase(TestCase):
    """Base test class with Firestore mocking."""

    def setUp(self):
        super().setUp()
        self.mock_firestore = create_mock_firestore()
        self.firestore_patcher = patch(
            "api.firestore_client.FirestoreClient.get_client",
            return_value=self.mock_firestore,
        )
        self.firestore_patcher.start()

    def tearDown(self):
        self.firestore_patcher.stop()
        super().tearDown()


class FirebaseAuthTestCase(FirestoreTestCase):
    """Base test class with Firebase Auth mocking."""

    def setUp(self):
        super().setUp()

        # Mock Firebase Admin SDK
        self.mock_user = create_mock_firebase_user()
        self.auth_patcher = patch("api.firebase_auth.auth.verify_id_token")
        self.mock_verify = self.auth_patcher.start()
        self.mock_verify.return_value = self.mock_user

    def tearDown(self):
        self.auth_patcher.stop()
        super().tearDown()


class MockedAPITestCase(TestCase):
    """Base test case that automatically mocks all HTTP requests"""

    def setUp(self):
        super().setUp()
        # Start responses - this will catch all requests.get/post/etc calls
        responses.start()

    def tearDown(self):
        # Stop and reset responses
        responses.stop()
        responses.reset()
        super().tearDown()


class FullMockedTestCase(MockedAPITestCase, FirebaseAuthTestCase):
    """Base test class with all mocking: HTTP, Firestore, Firebase Auth."""

    pass
