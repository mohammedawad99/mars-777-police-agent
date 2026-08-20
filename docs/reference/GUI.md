# Graphical user interface — group MaRs-777

**Status: CURRENT.** Added at Stage 9A-2B.

Two windows over one drawing model: a **live** view of a match this process is
playing, and a **replay** view of a finished sub-game and its verification.
Both are read-only. Neither can move an agent, place a barrier, answer a capture
question, change a verdict or advance the protocol.

## 1. What the source requires

| ID | Requirement | Source | Where it is met |
|---|---|---|---|
| `GUI-001` (MUST, App E rule 8) | the live interface shows **local truth only** — own position, sensed scent, received hints, belief heatmap | PDF p.70–71, 143 | `app/live_view_values.py`, `gui/live_layout.py` |
| `GUI-002` (**MUST NOT**, App E rule 9) | never display the full objective board state live; sanction is disqualification for an illegal advantage | PDF p.71, 143 | the live snapshot has **no field** an opponent cell could arrive in |
| `GUI-003` (MUST) | belief-map heatmap and a turn-state banner; belief-map screenshots are a submission requirement | PDF p.71–72, 97, 136 | `gui/live_layout.py`, `docs/evidence/gui/` |
| `PRD07-FR-023` | replay **after the audit point** may show both agents' true paths — "this is not permission for the live GUI to do so" | PRD-07 | `gui/replay_layout.py` only |
| `DOC-001` component (5) | two screenshots: a live belief map and a replay verification result | PDF p.97, 134, 148 | `docs/evidence/gui/` |

## 2. Running it

```bash
# step through a finished sub-game, with a window
uv run python -m mars777_police.gui_main replay \
    --log    artifacts/police/log_<game_id>_g01.json \
    --config artifacts/police/config_<game_id>_g01.json

# the same picture as a file, on a machine with no display at all
uv run python -m mars777_police.gui_main replay \
    --log <log> --config <config> --step 5 --png shot.png

# watch this agent play a counted series
uv run python -m mars777_police.gui_main live --launch <launch document>
```

| Option | Mode | Meaning |
|---|---|---|
| `--log`, `--config`, `--root` | `replay` | the same evidence arguments the replay command takes |
| `--step N` | `replay` | which step to draw; the first by default |
| `--png PATH` | `replay` | write the picture instead of opening a window |
| `--launch` | `live` | this side's launch document, exactly as the counted entrypoint takes it |

Exit status follows the replay viewer's: `0` verified and complete, `2`
unreadable evidence, a failed series, or a machine with no window toolkit, `3` a
finding, `4` an incomplete audit.

### Keys, in the replay window

| Key | Effect |
|---|---|
| `→` | next step |
| `←` | previous step |
| `Home` | first step |
| `End` | last step |

There is no other control, in either window, because there is nothing else a
viewer is allowed to do.

## 3. Why the live view cannot leak an advantage

The live picture is projected from `Observation` — **the value the strategy
itself is restricted to**. That value has four members (board, own position,
quota, scent belief) and, by construction, no field an opponent position, a peer
nonce, a reveal or a final-audit trajectory could arrive in.

So the guarantee is structural rather than procedural: *if the window shows
exactly what the agent may decide from, it cannot show an advantage the agent
does not already lawfully hold.* `tests/gui/test_gui_privacy.py` holds that line
in the source, by symbol rather than by prose, and
`tests/gui/test_live_projection.py` holds it in the value.

The belief map is drawn as a heatmap **and** labelled: every heated cell carries
its own number, and the panel says `belief (estimate) - not a sighting` and
`opponent position: never shown`. `PRD07-FR-005` requires belief to be
identifiable as belief; a warm square with no words attached would not be.

## 4. Why the GUI cannot affect a match

| Concern | How it is prevented |
|---|---|
| the window slows the game | the runtime leaves a snapshot in a **one-slot** box and walks away; publishing is constant time and never blocks |
| the window crashes | every publication goes through `GuardedSink`, which counts failures and re-raises nothing |
| the window is never opened | the default sink is `NO_VIEWER`, one call that discards |
| the window falls behind | the channel is **lossy by design**: latest wins, and a missed frame is an older picture rather than a delayed turn |
| the window decides something | `gui/` imports no strategy, turn service, protocol, transport or infrastructure module, and no key is bound to anything but navigation |

`tests/gui/test_live_driver_isolation.py` proves the strongest form of this: two
real agents play a whole sub-game with the viewer deliberately raising on every
snapshot, and reach the same terminal in the same number of rounds as they do
with nobody watching.

## 5. Why there are two renderers

Layout is arithmetic; rendering is a toolkit. Every layout decision produces a
`Frame` — plain rectangles and text — and two thin adapters draw it:

* `gui/window.py` (`tkinter`, standard library) for the interactive window;
* `gui/image_renderer.py` (Pillow) for an **offscreen** raster.

CI has no display, so the offscreen path is what makes the graphical output
provable on Linux and Windows alike, and it is what produced the screenshots in
`docs/evidence/gui/`. The interactive window is proved twice: against recording
doubles everywhere, and against the genuine toolkit wherever a display exists
(`tests/gui/test_gui_toolkit.py`, skipped rather than failed without one).

`tkinter` appears in exactly one module and Pillow in exactly one module, and
`tests/gui/test_gui_architecture.py` fails if either spreads.

### The toolkit may simply be absent, and that is not an error

`tkinter` is in the standard library but is **packaged separately** on Debian and
Ubuntu, so a perfectly ordinary Python 3.12 can lack it — including the
interpreter this project's own Linux CI runs. It is therefore obtained through
`gui/toolkit.py` **when a window is actually built**, never at import time, so:

* importing `mars777_police.gui` works everywhere;
* every layout, the offscreen renderer and `--png` work everywhere;
* asking for a window on such a machine exits `2` with a sentence naming the
  remedy — `sudo apt install python3-tk` — and pointing at `--png`.

A structural test fails if any module in the package imports the toolkit at
module scope, and the whole graphical suite is run against an interpreter where
`tkinter` is genuinely unimportable.

## 6. The screenshots

| File | What it is |
|---|---|
| `docs/evidence/gui/live_belief_map.png` | the live window at step 35 of a real sub-game: own cell, the folded belief heatmap with per-cell values, the turn-state banner, and the two statements that no opponent position is shown |
| `docs/evidence/gui/replay_verified.png` | the replay window at step 5 of the **same** sub-game: both agents' true cells, `Verified OK` for both sides with its `[OK]` glyph, `CONSISTENT`, and `audit complete yes` |

Both are produced by the real renderer from one thirty-five-round sub-game two
composed agents actually played here — not drawn, not mocked, and not a diagram
of an application. `tests/gui/test_gui_evidence.py` regenerates them on demand:

```bash
MARS777_WRITE_GUI_EVIDENCE=1 uv run pytest tests/gui/test_gui_evidence.py
```

Without that variable the same test asserts the pictures without writing a byte,
so an ordinary run never touches committed evidence.

**The identities in the pictures are development identities**
(`MaRs-777-vs-GROUP-XY`, `mars777-vs-groupx-2026w1-uid0001`). They are not a
tournament match and are not presented as one; no counted match against another
group has been played.

## 7. Colour is never the only signal

Every verification word is drawn as a colour **and** a glyph **and** the word
itself, so a reader who cannot separate two hues can still tell them apart.

| Word | Glyph |
|---|---|
| `Verified OK` | `[OK]` |
| `TAMPERED` | `[!!]` |
| `NOT_CHECKABLE` | `[??]` |
| `NOT_APPLICABLE` | `[--]` |

A cell holding both agents is drawn in its own third colour with the mark `P+T`,
because stacking two rectangles would silently hide one of them.

## 8. What the GUI is not

* not a second game engine — it renders values other modules produced;
* not a second auditor — the verification words come from `ReplaySession` and
  `audit_complete`, unchanged;
* not a network surface — nothing here opens a port, and the live view is an
  in-process sink rather than a socket;
* not a remote page — no CDN, no remote script, no web font, no analytics, no
  external image host; the only font is the one shipped with Pillow.
