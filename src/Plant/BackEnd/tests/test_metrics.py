import time
import unittest
from prometheus_client import CollectorRegistry
from core.metrics import record_request, REQUEST_COUNT, REQUEST_LATENCY, ERROR_COUNT

class TestMetrics(unittest.TestCase):

    def setUp(self):
        self.registry = CollectorRegistry()

    def test_record_request_success(self):
        start_time = time.time()
        record_request(latency=time.time() - start_time, success=True)
        self.assertEqual(REQUEST_COUNT._get_samples()[0].value, 1)
        self.assertGreater(REQUEST_LATENCY._get_samples()[0].value, 0)

    def test_record_request_failure(self):
        start_time = time.time()
        record_request(latency=time.time() - start_time, success=False)
        self.assertEqual(ERROR_COUNT._get_samples()[0].value, 1)

if __name__ == '__main__':
    unittest.main()
