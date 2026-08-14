import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from governance.audit import AuditLogger


class AuditLoggerTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.log_path = Path(self._tmpdir.name) / "audit.log"
        self.logger = AuditLogger(self.log_path)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_record_creates_audit_entry_with_expected_fields(self):
        self.logger.record(user="user01", skill="campus", status="success", duration_ms=812.345)

        lines = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)

        entry = json.loads(lines[0])
        self.assertEqual(entry["user"], "user01")
        self.assertEqual(entry["skill"], "campus")
        self.assertEqual(entry["status"], "success")
        self.assertEqual(entry["duration_ms"], 812.35)
        self.assertIn("timestamp", entry)

    def test_record_never_stores_raw_message_content(self):
        record = self.logger.record(user="user01", skill="campus", status="blocked", duration_ms=0.0, detail="short reason")
        self.assertFalse(hasattr(record, "message"))
        self.assertNotIn("message", vars(record))

    def test_multiple_records_append_without_overwriting(self):
        self.logger.record(user="user01", skill="campus", status="success", duration_ms=1.0)
        self.logger.record(user="user01", skill="library", status="success", duration_ms=2.0)
        lines = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main()
