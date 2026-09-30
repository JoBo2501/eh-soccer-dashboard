"""Regression tests for late official results and conservative updates."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup
import update_data as updater


class UpdaterTests(unittest.TestCase):
    def test_schedule_never_regresses_a_verified_final(self):
        rows = "".join(
            f"<tr><td>09/{day:02d}/2026</td><td>at Mars Hill University</td>"
            "<td>7:30 P.M.</td><td>Mars Hill</td><td>7:30 PM</td></tr>"
            for day in range(1, 11)
        )
        soup = BeautifulSoup(
            f'<table class="sidearm-schedule-table"><tbody>{rows}</tbody></table>',
            "html.parser",
        )
        verified = {"date": "2026-09-01", "status": "final", "for": 2,
                    "against": 0, "result": "W", "shots": 11}
        with patch.object(updater, "fetch", return_value=soup):
            result = updater.parse_schedule([verified])
        self.assertEqual(result[0]["status"], "final")
        self.assertEqual(result[0]["for"], 2)
        self.assertEqual(result[0]["shots"], 11)

    def test_host_score_requires_final_status_and_correct_teams(self):
        schedule = BeautifulSoup(
            '<div class="event-row" data-boxscore="/boxscores/20260929_game.xml">'
            '<span class="event-opponent-name">Emory &amp; Henry</span>'
            '<span class="status">Final</span></div>', "html.parser")
        box = BeautifulSoup(
            '<div class="linescore"><table>'
            '<tr><th class="name">Emory &amp; Henry</th><td class="total">2</td></tr>'
            '<tr><th class="name">Mars Hill</th><td class="total">0</td></tr>'
            '</table></div>', "html.parser")
        match = {"date": "2026-09-29", "opponent": "Mars Hill University", "status": "scheduled"}
        with patch.object(updater, "fetch", side_effect=[schedule, box]):
            updater.apply_host_schedules([match], {"hostSchedules": {
                "2026-09-29": "https://marshilllions.com/schedule"}})
        self.assertEqual((match["for"], match["against"], match["result"]), (2, 0, "W"))
        schedule.select_one(".status").string = "In progress"
        pending = {"date": "2026-09-29", "opponent": "Mars Hill University", "status": "scheduled"}
        with patch.object(updater, "fetch", return_value=schedule):
            updater.apply_host_schedules([pending], {"hostSchedules": {
                "2026-09-29": "https://marshilllions.com/schedule"}})
        self.assertEqual(pending["status"], "scheduled")

    def test_partial_verified_changes_are_saved_before_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "season.json"
            path.write_text(json.dumps({
                "matches": [{"date": "2020-01-01", "opponent": "Missing result", "status": "scheduled"}],
                "player": {}, "team": {}, "standings": [], "broadcasts": {},
            }))
            with patch.object(updater, "DATA_FILE", path), \
                 patch.object(updater, "parse_schedule", side_effect=RuntimeError("unavailable")), \
                 patch.object(updater, "add_eh_box_scores", side_effect=lambda m: m), \
                 patch.object(updater, "apply_sidearm_feeds", side_effect=lambda m, p, b: (m, p)), \
                 patch.object(updater, "apply_host_schedules"), \
                 patch.object(updater, "parse_standings", return_value=[]), \
                 patch.object(updater, "parse_team_stats", return_value={"games": 1}), \
                 patch.object(updater, "reconcile_team", side_effect=lambda t, m, s: (t, s)), \
                 patch.object(updater, "update_player", side_effect=lambda p, m: p):
                with self.assertRaises(RuntimeError):
                    updater.main()
            saved = json.loads(path.read_text())
            self.assertEqual(saved["team"]["games"], 1)
            self.assertEqual(saved["refreshHealth"]["status"], "awaiting-results")
            self.assertIn("checkedAt", saved)


if __name__ == "__main__":
    unittest.main()
