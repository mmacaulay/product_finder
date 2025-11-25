import unittest
from unittest.mock import MagicMock, patch
from api.firestore_models import ProductDAO, LLMPromptDAO

class TestProductDAO(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_client.collection.return_value = self.mock_collection
        
        # Patch FirestoreClient.get_client to return our mock
        self.patcher = patch('api.firestore_models.FirestoreClient.get_client', return_value=self.mock_client)
        self.patcher.start()
        
        self.dao = ProductDAO()

    def tearDown(self):
        self.patcher.stop()

    def test_create_product(self):
        # Setup mock
        mock_doc_ref = MagicMock()
        self.mock_collection.document.return_value = mock_doc_ref
        mock_doc_ref.get.return_value.exists = False
        
        # Call create
        self.dao.create(
            upc_code='123456789012',
            name='Test Product',
            brand='Test Brand'
        )
        
        # Verify
        self.mock_collection.document.assert_called_with('123456789012')
        mock_doc_ref.set.assert_called()
        call_args = mock_doc_ref.set.call_args[0][0]
        self.assertEqual(call_args['upc_code'], '123456789012')
        self.assertEqual(call_args['name'], 'Test Product')

    def test_create_duplicate_product(self):
        # Setup mock to simulate existing product
        mock_doc_ref = MagicMock()
        self.mock_collection.document.return_value = mock_doc_ref
        mock_doc_ref.get.return_value.exists = True
        
        # Verify raises ValueError
        with self.assertRaises(ValueError):
            self.dao.create(
                upc_code='123456789012',
                name='Test Product'
            )

    def test_get_by_upc(self):
        # Setup mock
        mock_doc_ref = MagicMock()
        self.mock_collection.document.return_value = mock_doc_ref
        mock_snapshot = MagicMock()
        mock_doc_ref.get.return_value = mock_snapshot
        mock_snapshot.exists = True
        mock_snapshot.to_dict.return_value = {
            'upc_code': '123456789012',
            'name': 'Test Product'
        }
        mock_snapshot.id = '123456789012'
        
        # Call get
        result = self.dao.get_by_upc('123456789012')
        
        # Verify
        self.assertEqual(result['upc_code'], '123456789012')
        self.assertEqual(result['name'], 'Test Product')


class TestLLMPromptDAO(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_client.collection.return_value = self.mock_collection
        
        self.patcher = patch('api.firestore_models.FirestoreClient.get_client', return_value=self.mock_client)
        self.patcher.start()
        
        self.dao = LLMPromptDAO()

    def tearDown(self):
        self.patcher.stop()

    def test_create_prompt(self):
        mock_doc_ref = MagicMock()
        self.mock_collection.document.return_value = mock_doc_ref
        
        self.dao.create(
            name='test_prompt',
            query_type='test',
            prompt_template='Hello {name}'
        )
        
        self.mock_collection.document.assert_called_with('test_prompt')
        mock_doc_ref.set.assert_called()
        call_args = mock_doc_ref.set.call_args[0][0]
        self.assertEqual(call_args['name'], 'test_prompt')
        self.assertEqual(call_args['prompt_template'], 'Hello {name}')
