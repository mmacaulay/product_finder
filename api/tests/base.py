from django.test import TestCase
import responses


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
