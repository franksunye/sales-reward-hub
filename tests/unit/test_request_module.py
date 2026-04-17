import unittest
from unittest.mock import MagicMock, patch

from modules.request_module import _send_request_with_session, send_request_with_managed_session


class RequestModuleTest(unittest.TestCase):
    def test_send_request_accepts_status_200(self):
        fake_response = MagicMock(status_code=200)
        fake_response.json.return_value = {"data": {"rows": []}}

        with patch("modules.request_module.requests.post", return_value=fake_response):
            result = _send_request_with_session("session-id", "http://example.com/api/card/123/query")

        self.assertEqual(result, {"data": {"rows": []}})

    def test_send_request_with_managed_session_uses_valid_session(self):
        fake_response = MagicMock(status_code=200)
        fake_response.json.return_value = {"data": {"rows": []}}

        with patch("modules.request_module.get_valid_session", return_value="session-id"), patch(
            "modules.request_module.requests.post", return_value=fake_response
        ):
            result = send_request_with_managed_session("http://example.com/api/card/123/query")

        self.assertEqual(result, {"data": {"rows": []}})


if __name__ == "__main__":
    unittest.main()
