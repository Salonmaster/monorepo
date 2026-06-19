# Setting Up Your Salon

Configure SalonMaster to match how your salon actually works.

---

## Salon Profile

Go to **Settings → Salon Profile** to set:

| Setting | What it's for |
|---|---|
| **Salon Name** | Shown on invoices, receipts, online booking page |
| **Logo** | Appears on receipts and booking page (PNG, max 2MB) |
| **Address** | For invoices and map on booking page |
| **Phone** | Client-facing contact number |
| **Email** | Booking confirmations and receipts come from here |
| **Website** | Link on your booking page |
| **Currency** | EUR, USD, GBP — can't be changed after first transaction |
| **Tax Rate** | Default VAT/sales tax (can override per service) |
| **Timezone** | Affects appointment times, reports, and reminders |

---

## Opening Hours

Set when your salon is open. This controls:

- Which time slots show on the booking calendar
- When online bookings are accepted
- Staff schedule validation

Go to **Settings → Opening Hours**:

1. Set open/close times for each day
2. Leave a day blank if you're closed
3. Add **breaks** (e.g., lunch 12:00–13:00) — these block bookings
4. Set **holidays** — closed dates for the year

!!! example "Example: Tuesday–Saturday Salon"
    | Day | Open | Close |
    |---|---|---|
    | Monday | Closed | |
    | Tuesday | 09:00 | 18:00 |
    | Wednesday | 09:00 | 18:00 |
    | Thursday | 09:00 | 20:00 (late night) |
    | Friday | 09:00 | 18:00 |
    | Saturday | 08:00 | 16:00 |
    | Sunday | Closed | |

---

## Services & Pricing

Go to **Settings → Services**. Each service has:

- **Name** — "Women's Cut & Blow Dry"
- **Duration** — how long it blocks the calendar
- **Price** — base price before tax
- **Category** — groups services in reports
- **Color** — shows on calendar for quick visual scanning
- **Online bookable** — toggle if clients can book this service themselves
- **Buffer time** — extra minutes after the service (for cleanup)

### Service Categories

Create categories that make sense for your salon:

| Category | Example Services |
|---|---|
| 💇 Hair | Cut, Color, Blow Dry, Balayage, Extensions |
| 💅 Nails | Manicure, Pedicure, Gel, Acrylic, Nail Art |
| 💆 Beauty | Facial, Waxing, Makeup, Lashes, Brows |
| ✂️ Barber | Cut, Beard Trim, Hot Towel Shave |

---

## Payment Methods

Go to **Settings → Payments** to enable what you accept:

- 💵 Cash
- 💳 Card (terminal integration or manual entry)
- 📱 Mobile (Apple Pay, Google Pay)
- 🎁 Gift Cards
- 🏦 Invoice (for business clients)

!!! tip "Card Terminal"
    SalonMaster integrates with SumUp, Square, and Stripe terminals. See [Payment Integrations](../settings/integrations.md).

---

## Tax Configuration

Go to **Settings → Tax**:

- **Default tax rate** — applied to all services unless overridden
- **Tax number** — your VAT ID (appears on invoices)
- **Invoice prefix** — e.g., "INV-" → "INV-2026-0001"
- **Receipt footer** — custom text like your return policy

---

## Importing Clients

If you're switching from another system, you can import clients:

1. Go to **Clients → Import**
2. Download the CSV template
3. Fill in: name, email, phone, notes (optional)
4. Upload. Duplicates are detected by email/phone.

[View template format →](../clients/profiles.md#bulk-import)

---

## Next: Add Your Staff

Now [add your team →](staff.md)
