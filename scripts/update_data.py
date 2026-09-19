#!/usr/bin/env python3
"""Refresh the static dashboard from official South Atlantic Conference pages.

The updater is deliberately conservative: a failed or ambiguous scrape keeps the
last verified value instead of replacing it with incomplete data.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "season.json"
SCHEDULE_URL = "https://thesac.com/schedule.aspx?schedule=2504"
STANDINGS_URL = "https://thesac.com/standings.aspx?path=msoc"
STATS_URL = "https://thesac.com/stats.aspx?path=msoc&year=2026"
EH_SCHEDULE_URL = "https://www.gowasps.com/sports/msoc/2026-27/schedule"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
SAC_TEAMS = {
    "anderson", "carson-newman", "catawba", "coker", "lenoir-rhyne",
    "lincoln memorial", "mars hill", "newberry", "tusculum", "wingate",
}


def fetch(url: str) -> BeautifulSoup:
    headers = dict(HEADERS)
    if "gowasps.com" in url:
        headers["Referer"] = EH_SCHEDULE_URL
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def cells(row) -> list[str]:
    return [" ".join(cell.get_text(" ", strip=True).split()) for cell in row.select("th,td")]


def normalized_team(name: str) -> str:
    return re.sub(r"\s+(university|college)$", "", name.lower()).strip()


def parse_schedule(existing: list[dict]) -> list[dict]:
    soup = fetch(SCHEDULE_URL)
    table = soup.select_one("table.sidearm-schedule-table")
    if not table:
        raise ValueError("Official schedule table not found")

    previous = {match["date"]: match for match in existing}
    parsed = []
    for row in table.select("tbody tr"):
        values = cells(row)
        if len(values) < 4:
            continue
        try:
            date = datetime.strptime(values[0], "%m/%d/%Y").date().isoformat()
        except ValueError:
            continue

        raw_opponent = values[1]
        site = "away" if raw_opponent.lower().startswith("at ") else "home"
        opponent = re.sub(r"^(at|vs\.?)\s+", "", raw_opponent, flags=re.I).strip()
        result_text, location = values[2], values[3]
        status_text = values[4] if len(values) > 4 else ""
        result_match = re.search(r"\b([WLT])\s+(\d+)\s*[-–]\s*(\d+)", result_text)
        conference = normalized_team(opponent) in SAC_TEAMS
        item = {
            "date": date,
            "opponent": opponent,
            "site": site,
            "location": location,
            "conference": conference,
            "status": "final" if result_match else "scheduled",
        }
        if result_match:
            item.update({
                "result": "D" if result_match.group(1) == "T" else result_match.group(1),
                "for": int(result_match.group(2)),
                "against": int(result_match.group(3)),
            })
        else:
            item["time"] = status_text or previous.get(date, {}).get("time", "TBA")

        box_link = row.find("a", string=re.compile("box score", re.I))
        if box_link and box_link.get("href"):
            item["boxScoreUrl"] = urljoin(SCHEDULE_URL, box_link["href"])
        elif previous.get(date, {}).get("boxScoreUrl"):
            item["boxScoreUrl"] = previous[date]["boxScoreUrl"]
        parsed.append(item)

    if len(parsed) < 10:
        raise ValueError(f"Only {len(parsed)} schedule rows parsed")
    return parsed


def add_eh_box_scores(matches: list[dict]) -> list[dict]:
    """Attach official E&H box scores once a scheduled game becomes final."""
    soup = fetch(EH_SCHEDULE_URL)
    links_by_date = {}
    for link in soup.select('a[href*="/boxscores/"]'):
        if "box score" not in link.get_text(" ", strip=True).lower():
            continue
        match = re.search(r"/(20\d{6})_", link.get("href", ""))
        if not match:
            continue
        raw = match.group(1)
        date = f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
        links_by_date[date] = urljoin(EH_SCHEDULE_URL, link["href"])

    for match in matches:
        if match["status"] == "final" and match["date"] in links_by_date:
            match["boxScoreUrl"] = links_by_date[match["date"]]
    return matches


def parse_standings(existing: list[dict]) -> list[dict]:
    soup = fetch(STANDINGS_URL)
    table = soup.select_one("table.sidearm-standings-table")
    if not table:
        raise ValueError("Official standings table not found")
    parsed = []
    for row in table.select("tbody tr"):
        values = cells(row)
        if len(values) < 7:
            continue
        # SIDEARM emits duplicated responsive team/record cells on this table.
        if len(values) >= 10 and values[0] == values[1]:
            team_name, conference, points, overall, form = values[0], values[2], values[5], values[7], values[9]
        else:
            team_name, conference, points, overall, form = values[0], values[1], values[2], values[4], values[6]
        parsed.append({
            "team": team_name,
            "conference": conference,
            "points": int(points),
            "overall": overall,
            "form": form,
        })
    if len(parsed) < 8:
        raise ValueError(f"Only {len(parsed)} standings rows parsed")
    return parsed


def parse_team_stats(existing: dict, matches: list[dict], standings: list[dict]) -> dict:
    soup = fetch(STATS_URL)
    table = soup.select_one("table.sidearm-table")
    if not table:
        raise ValueError("Official team statistics table not found")

    team = dict(existing)
    for row in table.select("tbody tr"):
        values = cells(row)
        if len(values) >= 14 and "Emory & Henry" in values[1]:
            team.update({
                "games": int(values[2]),
                "goalsFor": int(values[3]),
                "goalsAgainst": int(values[4]),
                "shots": int(values[10]),
                "corners": int(values[13]),
            })
            break

    eh_row = next((row for row in standings if "Emory & Henry" in row["team"]), None)
    if eh_row:
        team["overall"] = eh_row["overall"]
        team["conference"] = eh_row["conference"]

    unbeaten = 0
    for match in reversed([m for m in matches if m["status"] == "final"]):
        if match["result"] == "L":
            break
        unbeaten += 1
    team["unbeatenRun"] = unbeaten
    return team


def parse_player_box(url: str, match: dict) -> dict | None:
    soup = fetch(url)
    candidates = [row for row in soup.select("tr") if re.search(r"\bBorck\b", row.get_text(" ", strip=True), re.I)]
    for row in candidates:
        values = cells(row)
        table = row.find_parent("table")
        headers = cells(table.select_one("thead tr")) if table and table.select_one("thead tr") else []
        if not values or not headers:
            continue
        mapping = {re.sub(r"[^a-z]", "", key.lower()): value for key, value in zip(headers[-len(values):], values)}
        name = " ".join(values)
        if "Borck" not in name:
            continue
        minute_value = next((mapping[key] for key in ("min", "minutes", "mp") if key in mapping), None)
        shot_value = next((mapping[key] for key in ("sh", "shots") if key in mapping), "0")
        sog_value = next((mapping[key] for key in ("sog", "shotsongoal") if key in mapping), "0")
        goal_value = mapping.get("g", "0")
        assist_value = mapping.get("a", "0")
        if minute_value and minute_value.isdigit():
            context = table.get_text(" ", strip=True).lower()
            return {
                "date": match["date"],
                "opponent": match["opponent"],
                "site": match["site"],
                "role": "Sub" if "substitute" in context else "Start",
                "minutes": int(minute_value),
                "goals": int(goal_value) if goal_value.isdigit() else 0,
                "assists": int(assist_value) if assist_value.isdigit() else 0,
                "shots": int(shot_value) if shot_value.isdigit() else 0,
                "shotsOnGoal": int(sog_value) if sog_value.isdigit() else 0,
                "url": url,
            }

    # PrestoSports box scores list SH/SOG/G/A in the player table and all
    # substitutions in the play-by-play. The latter allows verified minutes.
    for row in soup.select("tr"):
        values = cells(row)
        table = row.find_parent("table")
        caption = table.find("caption") if table else None
        if (
            len(values) < 5
            or "Borck" not in values[0]
            or not caption
            or "Emory & Henry" not in caption.get_text(" ", strip=True)
        ):
            continue

        events = []
        for event_row in soup.select("tr"):
            event_values = cells(event_row)
            if len(event_values) < 2 or "substitution" not in " ".join(event_values).lower():
                continue
            text = " ".join(event_values[1:])
            if "Borck, Niklas" not in text:
                continue
            time_match = re.fullmatch(r"(\d+):(\d{2})", event_values[0])
            if not time_match:
                continue
            elapsed = int(time_match.group(1)) + int(time_match.group(2)) / 60
            action = "enter" if re.search(r"Borck, Niklas\s+for\b", text) else "exit"
            events.append((elapsed, action))

        events.sort()
        starts = bool(events and events[0][1] == "exit")
        on_field = starts
        entered_at = 0.0 if starts else None
        played = 0.0
        for elapsed, action in events:
            if action == "enter" and not on_field:
                on_field, entered_at = True, elapsed
            elif action == "exit" and on_field and entered_at is not None:
                played += max(0, elapsed - entered_at)
                on_field, entered_at = False, None
        if on_field and entered_at is not None:
            played += max(0, 90 - entered_at)

        return {
            "date": match["date"],
            "opponent": match["opponent"],
            "site": match["site"],
            "role": "Start" if starts else "Sub",
            "minutes": int(played + 0.5),
            "goals": int(values[-2]) if values[-2].isdigit() else 0,
            "assists": int(values[-1]) if values[-1].isdigit() else 0,
            "shots": int(values[-4]) if values[-4].isdigit() else 0,
            "shotsOnGoal": int(values[-3]) if values[-3].isdigit() else 0,
            "url": url,
        }
    return None


def update_player(existing: dict, matches: list[dict]) -> dict:
    player = dict(existing)
    logs = {entry["date"]: entry for entry in existing.get("log", [])}
    for match in matches:
        url = match.get("boxScoreUrl")
        if match["status"] != "final" or not url or match["date"] in logs:
            continue
        try:
            entry = parse_player_box(url, match)
            if entry:
                logs[entry["date"]] = entry
        except Exception as error:
            print(f"Player sheet skipped for {match['date']}: {error}")

    ordered = sorted(logs.values(), key=lambda item: item["date"])
    player.update({
        "log": ordered,
        "minutes": sum(item.get("minutes", 0) for item in ordered),
        "starts": sum(item.get("role") == "Start" for item in ordered),
        "appearances": len(ordered),
        "goals": sum(item.get("goals", 0) for item in ordered),
        "assists": sum(item.get("assists", 0) for item in ordered),
        "shots": sum(item.get("shots", 0) for item in ordered),
        "shotsOnGoal": sum(item.get("shotsOnGoal", 0) for item in ordered),
        "verifiedThrough": ordered[-1]["date"] if ordered else existing.get("verifiedThrough"),
    })
    return player


def main() -> None:
    data = json.loads(DATA_FILE.read_text())
    before = json.dumps(
        {key: value for key, value in data.items() if key != "updatedAt"},
        sort_keys=True,
    )
    successes = 0
    try:
        data["matches"] = parse_schedule(data["matches"])
        data["matches"] = add_eh_box_scores(data["matches"])
        successes += 1
    except Exception as error:
        print(f"Schedule kept from prior update: {error}")
    try:
        data["standings"] = parse_standings(data["standings"])
        successes += 1
    except Exception as error:
        print(f"Standings kept from prior update: {error}")
    try:
        data["team"] = parse_team_stats(data["team"], data["matches"], data["standings"])
        successes += 1
    except Exception as error:
        print(f"Team totals kept from prior update: {error}")

    data["player"] = update_player(data["player"], data["matches"])
    after = json.dumps(
        {key: value for key, value in data.items() if key != "updatedAt"},
        sort_keys=True,
    )
    if successes and after != before:
        data["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Update complete: {successes}/3 official SAC datasets refreshed")


if __name__ == "__main__":
    main()
