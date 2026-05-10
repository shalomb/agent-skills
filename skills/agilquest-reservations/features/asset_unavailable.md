# Asset Unavailable Behaviour

## When does this happen?

When SUBMIT is clicked for a date/time slot where the asset is already
reserved by someone else (or otherwise blocked), Agilquest rejects the
submission and stays on the asset page.

## What Agilquest returns

The page stays at `/asset/{id}` (no redirect to `/home`). An error element
appears directly on the asset page — the same class as the picker error but
rendered outside the popup:

```
div.error-message.font-error (on the asset page, not inside .popup):
"This Asset is not available for the Dates/Times requested.
 HINT: Try to Check In to the Reservation without changing the Start Time."
```

## How `book_reservation.py` detects this

After each SUBMIT attempt the script checks for `.error-message.font-error`
on the page **before** testing for success signals. If found, it returns
immediately with:

```json
{
  "status": "asset_unavailable",
  "asset_id": "343",
  "target_date": "2026-05-15",
  "when_value": "MAY 15, 2026 - 09:00 AM - 06:00 PM GMT+2",
  "attempts": 1,
  "message": "This Asset is not available for the Dates/Times requested. HINT: Try to Check In to the Reservation without changing the Start Time.",
  "url": "https://login.agilquest.com/asset/343"
}
```

Exit code is **1** — this is a genuine failure, not expected behaviour.

## Implications for agents

- `asset_unavailable` means someone else has the slot. There is no automatic
  retry or alternative — a human needs to decide what to do.
- The HINT in the message is Agilquest's suggestion to check in to an
  *existing* reservation; it is not relevant to the booking automation.
- `ensure_reservation.py` at 14:00 will surface this status if the midnight
  booking failed for this reason.

## Observed in testing

Tested by attempting to book May 15 2026 (5 days ahead, within window) when
the asset was already taken:

```
SUBMIT attempt 1/3 at 20:24:53...
Asset unavailable: This Asset is not available for the Dates/Times requested...
{"status": "asset_unavailable", ...}
# exit code: 1
```
