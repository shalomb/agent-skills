# Booking Window Behaviour

## Policy

Asset 343 (SK-BRA-06.01.W1024, Bratislava ICC) enforces a **maximum 7 days in
advance** booking policy. The window opens at **midnight Europe/Bratislava
(CEST, UTC+2)** on the day exactly 7 days before the target date.

## What happens when booking outside the window (8+ days ahead)

Agilquest enforces this client-side in a non-obvious way:

1. The calendar day cells for out-of-window dates render as `rdtDay` — **no
   visual disabled state** (`rdtDisabled` is absent).
2. Clicking an out-of-window day cell **silently does nothing** — the `#resv_form_when`
   input value does not update.
3. Clicking **APPLY** with no valid date selected causes the popup to **refuse
   to close** — it stays open with no error message or toast.
4. There is no server-side rejection — the form never reaches SUBMIT.

## How `book_reservation.py` detects this

After clicking APPLY, the script waits up to 5 seconds for `.when-popup` to
become hidden. If it times out (popup stayed open), the error message is
prefixed with `booking_window_closed:` and the exit status is:

```json
{
  "status": "booking_window_closed",
  "message": "booking_window_closed: 2026-05-18 is not yet bookable (booking window opens at midnight exactly 7 days before)"
}
```

Exit code is **0** (not an error — this is expected before midnight).

## Cron design implication

This is why `book_reservation.py --prestage` is scheduled at **23:57**:

- Before midnight it will hit `booking_window_closed` if run early enough to
  stage but the window hasn't opened yet.
- The `--prestage` path sleeps until **23:59:58**, by which point the window
  has been open for 7 days exactly and the day cell click will register.
- If somehow the stage step ran before midnight opened the window, APPLY would
  fail and the script would exit with `booking_window_closed` — the 14:00
  `ensure_reservation.py` would then catch and rebook.

## Observed in testing

```
Clicking APPLY...
Error: booking_window_closed: 2026-05-18 is not yet bookable
{"status": "booking_window_closed", "message": "..."}
# exit code: 0
```
