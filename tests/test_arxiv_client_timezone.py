from __future__ import annotations

from datetime import date
import unittest

from hunter_agent.arxiv.client import ArxivClient


class TestArxivClientTimezone(unittest.TestCase):
    def test_build_submitted_date_range_for_hong_kong(self) -> None:
        client = ArxivClient(local_timezone="Asia/Hong_Kong")
        # Local day 2026-02-27 should map to UTC 2026-02-26 16:00 ~ 2026-02-27 15:59.
        submitted_range = client.build_submitted_date_range(date(2026, 2, 27))
        self.assertEqual(
            submitted_range,
            "submittedDate:[202602261600 TO 202602271559]",
        )


if __name__ == "__main__":
    unittest.main()
