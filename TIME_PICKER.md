# Reverse Dotline time/date picker

## Goal
Replace the brittle `prompt()` input for Reverse Dotline event times with a modal picker that supports:

- HH:MM time input
- A slider for quick offsets from -6 h to +6 h (step 15 min)
- A separate ± offset field that formats values as `30 min`, `1 h`, `2 h 15 min`
- A native `<input type="date">` wrapped in a styled button so the calendar opens in the right place on desktop and mobile
- Editing existing events through the same modal
- A separate duration picker for intervals between events (whole hours only, ±6 h)
- Dates displayed as `14:30 · Jul 8` when not on the anchor day

## Storage model

Reverse Dotline events now store absolute timestamps instead of minutes-of-day:

- `node.time` — event time as **milliseconds since Unix epoch**
- `links[i].duration` — interval between events in **milliseconds**

The first event (anchor) is created at the current time (`Date.now()`). All later
events are counted forward from that anchor using link durations.

### Migration
`load()` runs `migrateReverseTimes()` on every startup:

- If `node.time` is between `0` and `1439`, it is treated as minutes-of-day and converted to `todayMidnight + time * 60000`.
- If `link.duration` is between `-1439` and `1439`, it is treated as minutes and converted to milliseconds.

This is a best-effort migration; old notes without a stored anchor date are assumed to belong to today.

## UI entry points

- **Add event** — clicking the ghost "+" dot at the bottom opens the time picker.
- **Edit event** — clicking the time alias to the left of an existing dot opens the time picker pre-filled with that event's time.
- **Change interval** — clicking the read-only duration label between two dots opens the duration picker.

The dot still supports swipe-to-delete and short-click toggles `done`.

## Time picker logic

```text
selectedDay   = date chosen in the date picker (defaults to the event's current day)
selectedMin   = minutes since midnight from the time input
offsetMs      = slider/offset value in hours * 60 * 60000
resultTime    = selectedDay + selectedMin * 60000 + offsetMs
duration      = resultTime - previousEventTime
```

- For the **anchor** event, `previousEventTime` equals the anchor time, so duration is `0` and only the absolute time/date changes.
- For **new** events, `previousEventTime` is the last event's time.
- For **editing**, `previousEventTime` is the preceding event (or anchor for index 0).

After apply:

1. `node.time` is set to `resultTime`.
2. The preceding link's `duration` is set to `duration`.
3. `updateReverseTimes()` recalculates all following event times from the changed link durations.

## Duration picker logic

```text
durationMs = slider value in hours * 60 * 60000
nextTime   = previousEventTime + durationMs
```

The slider is limited to whole hours between -6 and +6. After apply, the link's
duration is updated and `updateReverseTimes()` shifts all later events.

## "Today" definition

In Reverse Dotline, **"Today" means the anchor day** — the day of the first event (`n.nodes[0].time`).

- Events on the anchor day render as `14:30`.
- Events on any other day render as `14:30 · Jul 8`.
- The date picker label shows "Today" when the selected date equals the anchor day.

## Clock faces

Reverse timeline dots show an analog clock face drawn with `div` elements:

- `.clock-hand.hour` and `.clock-hand.minute` rotate from the dot center.
- `.clock-cap` marks the center.
- `setClockHands(dot, timestamp)` updates the rotation.

Using div-based hands avoids SVG `transform-origin` quirks across browsers and scales cleanly with the dot size.

## Formatting helpers

| Function | Purpose |
|---|---|
| `startOfDay(ts)` | Local midnight for a timestamp |
| `minutesSinceMidnight(ts)` | Local hour/minute as minutes |
| `formatTimeInput(min)` | `HH:MM` for `<input type="time">` |
| `formatDateInput(ts)` | `YYYY-MM-DD` for `<input type="date">` |
| `formatTime(ts, anchorDay)` | Display time, with `· MMM d` when not anchor day |
| `formatDuration(ms)` | Human readable duration (`2 h 30 min`) |
| `parseDuration(s)` | Parse strings like `1h 30m`, `90 min`, `90` → ms |

## Styling

The modal uses `.tp-*` CSS classes. It is a fixed centered overlay (`z-index: 200`) with a subtle fade-in/pop animation and respects the existing light/dark theme variables. The date picker is an invisible `<input type="date">` stretched over a styled `.tp-date-button`, so the native calendar pops up next to the button on both desktop and mobile.

## Files

- `prototype.html` — source of truth for the app body
- `index.html` — deployed page (wraps `prototype.html` with `<!doctype>`, head, and `<body>`)
- `TIME_PICKER.md` — this document
