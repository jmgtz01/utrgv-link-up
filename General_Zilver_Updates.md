## Available Computers (frontend template)
- Added modal-based flow for reservations and inline login prompt; markers now open a Bootstrap modal for slot selection or login.
- Added cancel-my-reservation alert with button; modal also offers cancel when an existing reservation blocks new bookings.
- Marker icons reduced ~15% (36px/32px), label tightened upward; auto-refresh every 60s; added login/cancel/reserve modals; maps still support admin edit/drag.

## Reservations (backend logic)
- Introduced `Reservation` model with resource_type/resource_id, user, start/end, and indexes.
- Added APIs: `api/slots/` (list today's half-hour start slots 8am-8pm), `api/reserve/` (create 1-hour slot), `api/cancel-reservation/` (clear active user reservations).
- Enforced one active reservation per user across computers/rooms; blocks repair/out_of_order.
- Cleanup of expired reservations/statuses on page render; statuses now computed from live reservations using local time.
- Icons now show reserved (for your slot) and occupied (for others) during active windows.

## Available Computers (view context)
- Supplies `user_active` reservation to show current booking banner and end time.
- Precomputes icons/status from Reservation table rather than static status fields.

## Login (members app)
- `login_user` now supports JSON/AJAX login responses for inline modal; still works with standard form post.

## DB and migrations
- Applied main-branch migrations; added `0011_reservation` for the new model.
- Fixed bad event.manager data blocking migrations; set to a valid user.
