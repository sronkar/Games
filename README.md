# Games

## Codenames phone boards (`skills/codenames-board`)

An agent skill for playing Codenames on phones when the table is blocked, the group is too big, or some players are remote.

Give your AI agent two photos: the 5x5 word board and the spymasters' key card. It makes two interactive pages:

- **Field Board** for everyone. Every word sits on a plain card. After a guess, tap the word and mark it red, blue, bystander or assassin. The assassin ends the game.
- **Spymaster Key** for the two spymasters. Every word shows its key color. Tap a guessed word to flip it face down, and its color stays.

The players' page never contains the key.

### Install

- **Claude Code**: copy `skills/codenames-board` into `~/.claude/skills/` (for all projects) or into `.claude/skills/` in a project.
- **Claude apps (claude.ai / desktop / mobile)**: zip the folder (`cd skills && zip -r codenames-board.zip codenames-board`) and upload it under Settings → Capabilities → Skills.
- **Other agents**: point the agent at `skills/codenames-board/SKILL.md`. The build script needs only Python 3 and no packages.

### Try it without photos

```bash
python3 skills/codenames-board/scripts/build_boards.py skills/codenames-board/examples/game.json --out out
```

Then open `out/public.html` and `out/spymaster.html` in a browser.
