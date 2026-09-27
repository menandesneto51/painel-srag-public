# -*- coding: utf-8 -*-
import json
import tempfile
import unittest
from pathlib import Path

from scripts.promote_snapshot import validate_candidate_approval_state


class SnapshotPromotionTests(unittest.TestCase):
    def setUp(self):
        self.approval = {
            "snapshot_id": "srag-mt-2026-test",
            "approver": "Reviewer",
            "approved_at": "2026-09-26T12:00:00-04:00",
        }

    def write_metadata(self, directory: Path, status: str, approval: dict | None = None):
        payload = {"publication_status": status}
        if approval is not None:
            payload["approval"] = approval
        (directory / "metadata_public.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def test_under_review_cannot_be_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_metadata(root, "under_review")
            with self.assertRaises(ValueError):
                validate_candidate_approval_state(root, self.approval)

    def test_embedded_approval_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            embedded = dict(self.approval)
            embedded["snapshot_id"] = "different"
            self.write_metadata(root, "validated", embedded)
            with self.assertRaises(ValueError):
                validate_candidate_approval_state(root, self.approval)

    def test_validated_matching_approval_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_metadata(root, "validated", self.approval)
            metadata = validate_candidate_approval_state(root, self.approval)
            self.assertEqual(metadata["publication_status"], "validated")


if __name__ == "__main__":
    unittest.main()
