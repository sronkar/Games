---
name: codenames-board
description: Turn two photos of a Codenames game (the 5x5 word board and the spymasters' secret key card) into two interactive phone boards. One is a plain board for the players, where tapping a word marks it red, blue, bystander or assassin. The other is a colored key for the spymasters, where tapping a word flips it face down. Use when someone wants to play Codenames on phones because the table is blocked, the group is too big, or some players are remote, or when they share photos of a Codenames board or key card.
---

# Codenames phone boards

You receive two photos and produce two interactive pages:

| Page | Who gets it | Shows | Tap does |
|---|---|---|---|
| `public.html` (Field Board) | Everyone | 25 words on plain cards | Opens a picker: Red agent, Blue agent, Bystander, Assassin. The assassin ends the game. |
| `spymaster.html` (Spymaster Key) | The two spymasters only | 25 words in their key colors | Flips the card face down. The color stays and the word is hidden. Tap again to flip it back. |

Both pages show how many agents each team still has to find, have Undo and Clear, keep their state if the page reloads, and try to keep the phone screen on.

The public page never contains the key. `scripts/build_boards.py` puts only the words, the team totals and the starting team into it.

## Steps

### 1. Get both photos

You need:
1. **Board photo**: the 25 word cards in a 5x5 grid.
2. **Key card photo**: the small square card with a 5x5 grid of red, blue, beige/yellow and black squares.

If only one arrives, ask for the other. Tell the user once that the key card photo is secret. The person running this should be a spymaster or someone who is not playing.

### 2. Read the words

- Read the grid row by row, top-left to bottom-right, as the board appears in the photo.
- Each Codenames card prints its word twice, once upside-down. Read the copy that is upright in the photo.
- If a word is blurred, covered by glare or cut off, ask the user. Do not guess, because a wrong word breaks the game.
- Keep multi-word cards as they are printed (for example `ICE CREAM`, `LOCH NESS`, `בית-ספר`).
- Any language works. For right-to-left editions (Hebrew, Arabic), still list each row **left to right as the cards lie in the photo**, because the key card maps physical positions and not reading order. The pages keep that layout and show each word in its own direction.

### 3. Read the key card

- Read the 25 squares row by row, in the same order as the words:
  `R` red agent, `B` blue agent, `N` bystander (beige/yellow), `A` assassin (black).
- Ignore the colored lights along the card's border. They show the starting team, which is the team with 9 agents. Record that color as `starting_team` so the script can cross-check it.
- **Orientation matters.** The key must be read the way it lines up with the board. The top row of the key goes with the top row of the board photo. Unless the user says otherwise, assume both photos were taken from the same side of the table with the key card upright as it sits in its stand. If the user says the key was photographed turned, fix the order with `--rotate-key 90|180|270` (clockwise) rather than re-typing it.

A standard key has 9 of the starting color, 8 of the other, 7 bystanders and 1 assassin. The script rejects any other count, and a rejection almost always means a misread square. Look at the photo again before reaching for `--allow-nonstandard`, which is meant for house variants.

### 4. Write the game file and build

Write `game.json` (see `examples/game.json`):

```json
{
  "words": ["AGENT", "BERLIN", "CASINO", "DIAMOND", "EAGLE", "...25 in total"],
  "key": ["RBNRB", "NRABR", "NBRNB", "RNBRN", "BRNBR"],
  "starting_team": "red"
}
```

Run:

```bash
python3 scripts/build_boards.py game.json --out <dir>             # full HTML files
python3 scripts/build_boards.py game.json --out <dir> --artifact  # for claude.ai Artifacts
```

To fix a misread word or color after the boards are shared, rebuild with `--game-id <id>` using the id the first build printed, and republish to the same links. Phones then keep the marks already made.

The script prints the board as a text grid with each word's letter (`AGENT [R]`). Check it against both photos. If the user is the spymaster or game host, you can show them the word list to confirm before they share anything.

### 5. Deliver

- **If you can publish Artifacts** (claude.ai, Claude Code with the Artifact tool): build with `--artifact` and publish the two files as **separate** artifacts: `public.html` titled "Codenames Field Board" and `spymaster.html` titled "Codenames Spymaster Key". Give the user both links and say clearly which one to send to everyone and which one goes only to the two spymasters.
- **Otherwise**: build without `--artifact` and hand over the two `.html` files. Each is a single self-contained file that opens in any phone browser, can be sent over a messaging app or AirDrop, and needs no internet apart from the optional web fonts.

When only the host has Claude, tell them how the others get in:
- **Easiest:** open each artifact's **Share** menu and turn on a public link. Anyone with the link can open it in a phone browser, with no Claude account needed. Send the players' link to the group and the spymasters' link privately to the two spymasters.
- **No links:** also build without `--artifact` and send the two `.html` files. Android opens them in Chrome. On iPhone, the preview inside a chat app often doesn't run the page, so save the file to Files and open it from there in Safari.
- Each phone keeps its own marks, and the boards don't sync between phones. Pick one person to mark the players' board and show it to the table or share their screen on the call. Each spymaster flips cards on their own copy.

Tell the user in one line how to play with them:
- Players' board: after each guess, tap the word and pick the color the spymaster calls.
- Spymasters' board: tap the word that was just guessed to flip it face down.

### Without code execution

If you cannot run Python, build the pages by hand from `assets/board_template.html`:
1. Replace `__TITLE__` with the page title.
2. Replace `/*__DATA__*/null` with a JSON object:
   - public: `{"mode":"public","id":"<random>","words":[25 words],"starting":"red","totals":{"red":9,"blue":8}}`
   - spymaster: the same plus `"mode":"spymaster"` and `"key":[25 of "red","blue","neutral","assassin"]`
3. For Artifacts, remove the `<!--BODY-->` marker line. For a standalone file, wrap everything before the marker in `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">…</head>` and everything after it in `<body>…</body></html>`.
4. Never put `key` into the public page. Check the counts yourself (9/8/7/1).

## Files

- `scripts/build_boards.py`: validates the game file and writes both pages. Run it with `--help` for the options.
- `assets/board_template.html`: the single template for both pages. The mode comes from the data.
- `examples/game.json`: a sample game file.
