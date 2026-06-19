# Checkout Flow

The checkout is where appointments become revenue. SalonMaster is designed to get you from chair to paid in under 30 seconds.

---

## Opening Checkout

From an appointment:
1. Click the appointment → **Checkout**
2. Or select from the **Active Clients** list
3. Or press `C` and search for a client

---

## The Checkout Screen

```
┌──────────────────────────────────────────┐
│  CHECKOUT — Sarah M.                      │
│  Stylist: Emma                            │
│                                           │
│  Services:                                │
│  ✅ Balayage                   €95.00    │
│  ✅ Olaplex Treatment          €25.00    │
│                                           │
│  Products:                                │
│  + Add Product                            │
│                                           │
│  ───────────────────────────────────────  │
│  Subtotal                     €120.00    │
│  Discount (10% loyalty)       -€12.00    │
│  Tax (21% VAT)                 €18.97    │
│  ───────────────────────────────────────  │
│  TOTAL                        €126.97    │
│                                           │
│  [💵 Cash] [💳 Card] [📱 Mobile]         │
│  [🎁 Gift Card] [🏦 Invoice]             │
│                                           │
│  Tip: [€____]  or  [10%] [15%] [20%]    │
│                                           │
└──────────────────────────────────────────┘
```

---

## Adding Services

If the client decides to add a service:
1. Click **+ Add Service**
2. Search and select
3. It appends to the bill

Services from the appointment are pre-filled.

---

## Adding Products

Sold retail products during the visit?

1. Click **+ Add Product**
2. Scan barcode or search by name
3. Quantity auto-decrements from inventory

---

## Discounts

Apply discounts before payment:

| Discount Type | How |
|---|---|
| **Percentage** | e.g., 10% off (loyalty, promotion) |
| **Fixed amount** | e.g., €5 off (coupon) |
| **Service comp** | Zero out a specific service (owner discretion) |
| **Loyalty reward** | Auto-applied if client has enough points |

Discounts require a reason (selected from dropdown) for reporting.

---

## Payment

### Cash
Enter amount tendered → system calculates change.

### Card
If terminal is connected: click **Card** → terminal prompts client → auto-confirms.
Manual: enter last 4 digits + approval code.

### Mobile (Apple Pay / Google Pay)
Same as card — terminal handles it.

### Split Payment
Client wants to pay €50 cash + rest on card? Click **Split** → enter amounts per method.

### Gift Card
Enter gift card code → balance auto-deducted. Remaining balance shown.

### Invoice
For business clients: generates PDF invoice, marks as unpaid. Track in **Reports → Accounts Receivable**.

---

## Tips

Tips can be added:
- **Before payment** — client adds tip to total
- **After payment** — on card terminal prompt
- **Manual** — cash tips entered by staff

Tips are tracked per stylist for commission reports. See [Tips & Commissions →](../reports/tips.md)

---

## Receipt

After payment:

- **Print** — if receipt printer connected
- **Email** — sends PDF to client's email
- **SMS** — texts a link to digital receipt
- **Skip** — no receipt (cash, quick walk-in)

Receipt includes: salon logo, services, products, payment breakdown, tax, tip, and a "Thank you!" message.

---

## After Checkout

The appointment status moves to ✅ Completed. The client stays in history. Revenue updates on the dashboard in real-time.

Next client! 💈
