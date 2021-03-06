from unittest import TestCase
from mock import MagicMock, patch

import frontend.api.controllers.search as api_search


class TestApiSearch(TestCase):

    def setUp(self):
        self.old_file_web_schema = api_search.file_web_schema
        self.old_request = api_search.request
        self.file_web_schema = MagicMock()
        self.request = MagicMock()
        self.db = MagicMock()
        api_search.file_web_schema = self.file_web_schema
        api_search.request = self.request

    def tearDown(self):
        api_search.file_web_schema = self.old_file_web_schema
        api_search.request = self.old_request
        del self.file_web_schema
        del self.request

    def test001_files_raise_none_None(self):
        with patch("frontend.api.controllers.search.process_error") as mock:
            api_search.files("whatever")
            self.assertTrue(mock.called)
            self.assertIsInstance(mock.call_args[0][0], ValueError)
            self.assertEqual(str(mock.call_args[0][0]),
                             "Can't find using both name and hash")

    def test002_files_raise_h_type_None(self):
        self.request.query.name = None
        with patch("frontend.api.controllers.search.process_error") as mock:
            api_search.files("whatever")
            self.assertTrue(mock.called)
            self.assertIsInstance(mock.call_args[0][0], ValueError)
            self.assertEqual(str(mock.call_args[0][0]), "Hash not supported")
