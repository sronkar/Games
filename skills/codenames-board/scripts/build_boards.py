#!/usr/bin/env python3
"""Build the two Codenames phone boards from a game file.

Reads a JSON game file (the words from the board photo and the colors from the
key card photo), checks it against the standard Codenames key card, and writes:

  public.html     - every word on a plain card, for the players (no key inside)
  spymaster.html  - every word in its key color, for the spymasters only

Usage:
  python3 build_boards.py game.json --out DIR [--artifact] [--rotate-key 90]
                                            [--allow-nonstandard]

Game file:
  {
    "words": ["AGENT", "BERLIN", ...],     # 25 words, row by row, top-left first
                                           # (or 5 lists of 5)
    "key":   ["RBNRB", "NRABR", ...],      # 5 strings of 5 letters, same order
                                           # (or 25 tokens, or 5 lists of 5)
    "starting_team": "red"                 # optional; checked against the key
  }

Key letters: R = red agent, B = blue agent, N or Y = bystander (neutral/yellow),
A, K or X = assassin (black). Full names ("red", "bystander", "black", ...)
are accepted too.
"""

import argparse
import html
import json
import secrets
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "board_template.html"

ALIASES = {
    "red": {"r", "red"},
    "blue": {"b", "blue"},
    "neutral": {"n", "y", "neutral", "yellow", "bystander", "beige", "tan", "innocent"},
    "assassin": {"a", "k", "x", "assassin", "black"},
}
TOKEN = {alias: role for role, names in ALIASES.items() for alias in names}
LETTER = {"red": "R", "blue": "B", "neutral": "N", "assassin": "A"}


class GameError(Exception):
    pass


def flatten_words(words):
    if isinstance(words, list) and len(words) == 5 and all(isinstance(r, list) for r in words):
        words = [w for row in words for w in row]
    if not isinstance(words, list) or len(words) != 25:
        n = len(words) if isinstance(words, list) else "?"
        raise GameError(f"'words' needs 25 entries (5 rows of 5); got {n}.")
    out = []
    for i, w in enumerate(words):
        w = " ".join(str(w).split()).upper()
        if not w:
            raise GameError(f"Word {i + 1} (row {i // 5 + 1}, column {i % 5 + 1}) is empty.")
        out.append(w)
    return out


def flatten_key(key):
    cells = []
    if isinstance(key, str):
        key = key.split()
    if not isinstance(key, list):
        raise GameError("'key' must be a list.")
    if len(key) == 5 and all(isinstance(r, str) and len(r.replace(" ", "")) == 5 for r in key):
        for row in key:
            cells.extend(row.replace(" ", ""))
    elif len(key) == 5 and all(isinstance(r, list) for r in key):
        cells = [c for row in key for c in row]
    else:
        cells = list(key)
    if len(cells) != 25:
        raise GameError(f"'key' needs 25 cells (5 rows of 5); got {len(cells)}.")
    roles = []
    for i, c in enumerate(cells):
        role = TOKEN.get(str(c).strip().lower())
        if not role:
            raise GameError(
                f"Key cell {i + 1} (row {i // 5 + 1}, column {i % 5 + 1}) is '{c}'. "
                "Use R, B, N (or Y) and A (or K/X)."
            )
        roles.append(role)
    return roles


def rotate_clockwise(cells, turns):
    grid = [cells[r * 5:(r + 1) * 5] for r in range(5)]
    for _ in range(turns % 4):
        grid = [list(row) for row in zip(*grid[::-1])]
    return [c for row in grid for c in row]


def check_counts(roles, starting, allow_nonstandard):
    c = Counter(roles)
    red, blue, neutral, assassin = c["red"], c["blue"], c["neutral"], c["assassin"]
    standard = assassin == 1 and neutral == 7 and {red, blue} == {8, 9}
    if standard:
        by_count = "red" if red == 9 else "blue"
        if starting and starting != by_count:
            raise GameError(
                f"The key has 9 {by_count} agents, so {by_count} starts, but starting_team says "
                f"{starting}. Re-check the key card colors or the border lights."
            )
        return by_count, None
    msg = (f"The key has {red} red, {blue} blue, {neutral} bystanders and {assassin} assassin. "
           "A standard key card has 9 + 8 agents, 7 bystanders and 1 assassin.")
    if not allow_nonstandard:
        raise GameError(msg + " Re-read the key card photo, or pass --allow-nonstandard for a house variant.")
    if assassin < 1:
        raise GameError(msg + " A board needs at least one assassin.")
    if not starting:
        starting = "red" if red >= blue else "blue"
    return starting, msg


def render(template, data, title, artifact):
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    blob = blob.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    page = template.replace("__TITLE__", html.escape(title)).replace("/*__DATA__*/null", blob)
    head, body = page.split("<!--BODY-->", 1)
    if artifact:
        # The artifact host supplies doctype, head and body around the content.
        return head + body
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        + head + "</head>\n<body>\n" + body + "</body>\n</html>\n"
    )


def preview(words, roles):
    width = max(len(w) for w in words) + 4
    lines = []
    for r in range(5):
        cells = [f"{words[i]} [{LETTER[roles[i]]}]".ljust(width) for i in range(r * 5, r * 5 + 5)]
        lines.append("  ".join(cells).rstrip())
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build Codenames public and spymaster boards.")
    ap.add_argument("game", help="game JSON file")
    ap.add_argument("--out", default=".", help="output directory (default: current)")
    ap.add_argument("--artifact", action="store_true",
                    help="write page content only, for hosts that wrap it in their own <html> (claude.ai Artifacts)")
    ap.add_argument("--rotate-key", type=int, default=0, choices=[0, 90, 180, 270],
                    help="rotate the key grid clockwise so it matches the board's orientation")
    ap.add_argument("--allow-nonstandard", action="store_true",
                    help="accept key counts other than 9/8/7/1")
    ap.add_argument("--game-id", help="reuse the id printed by an earlier build so phones keep their marks after a rebuild")
    args = ap.parse_args(argv)

    try:
        game = json.loads(Path(args.game).read_text(encoding="utf-8"))
        words = flatten_words(game.get("words"))
        roles = rotate_clockwise(flatten_key(game.get("key")), args.rotate_key // 90)
        starting = game.get("starting_team")
        if starting is not None:
            starting = TOKEN.get(str(starting).strip().lower())
            if starting not in ("red", "blue"):
                raise GameError("starting_team must be 'red' or 'blue'.")
        starting, warning = check_counts(roles, starting, args.allow_nonstandard)
    except (GameError, json.JSONDecodeError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    c = Counter(roles)
    totals = {"red": c["red"], "blue": c["blue"]}
    game_id = args.game_id or secrets.token_hex(5)
    template = TEMPLATE.read_text(encoding="utf-8")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # The public page gets words, totals and the starting team only. Never the key.
    public = {"mode": "public", "id": game_id, "words": words, "starting": starting, "totals": totals}
    spymaster = dict(public, mode="spymaster", key=roles)

    (out / "public.html").write_text(render(template, public, "Codenames Field Board", args.artifact), encoding="utf-8")
    (out / "spymaster.html").write_text(render(template, spymaster, "Codenames Spymaster Key", args.artifact), encoding="utf-8")

    dupes = [w for w, n in Counter(words).items() if n > 1]
    if warning:
        print(f"warning: {warning}")
    if dupes:
        print(f"warning: repeated word(s) {', '.join(dupes)}; check the board photo.")
    print(f"{starting.capitalize()} starts: {totals['red']} red, {totals['blue']} blue, "
          f"{c['neutral']} bystanders, {c['assassin']} assassin.")
    print(preview(words, roles))
    print(f"wrote {out / 'public.html'}")
    print(f"wrote {out / 'spymaster.html'}")
    print(f"game id {game_id} (pass --game-id {game_id} to rebuild without clearing marks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
