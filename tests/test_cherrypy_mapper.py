__author__ = 'omarsubhiabdelhafith'

import unittest
from mockpy.core.cherrypy_mapper import *
from mockpy.utils import log
from mockpy.status.status import Status
from mock import Mock
import os


class StatusTests(unittest.TestCase):

    def test_gets_status_correctly(self):
        self.assertEqual(Status.is_status("http://127.0.0.1/status"), True)
        self.assertEqual(Status.is_status("http://localhost/status"), True)
        self.assertEqual(Status.is_status("http://localhost123/status"), False)
        self.assertEqual(Status.is_status("http://1.1.1.1/status/123"), False)
        self.assertEqual(Status.is_status("http://1.1.1.1/sanotus"), False)

    def test_return_correct_body_for_multiple_response(self):
        item1 = Mock(file_name="file1")
        item1.request = "request1"

        item2 = Mock(file_name="file2")
        item2.request = "request2"
        # item2.title = Mock(return_value="title2")

        mapper = CherryPyMapper()
        mapper.cherrypy = Mock()
        mapper.cherrypy.url = Mock(return_value="some url")

        body = log.log_multiple_matches([item1, item2])
        self.assertEqual(body, "Matched 2 items, choosing the first one\n- file1\nrequest1\n\n- file2\nrequest2\n")


