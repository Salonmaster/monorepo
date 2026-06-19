# Function Modules

## 1. Appointment Management

- Calendar view (day/week) with drag-and-drop
- Create/edit/cancel appointments
- Staff assignment (auto or manual)
- Duration auto-calculation from services
- Buffer time between appointments
- Recurring appointments
- SMS/email reminders
- Status: booked → confirmed → in_progress → completed → cancelled

## 2. Client CRM

- Client profile (name, contact, birthday, notes)
- Full visit history with services, products, totals
- Service preferences (stylist, colors, allergies)
- Client tags (VIP, regular, new)
- Marketing consent tracking (GDPR)

## 3. POS / Checkout

- Service selection from catalog
- Product add-on scanning
- Discount application (% or fixed)
- Multiple payment methods (cash, card, invoice)
- Receipt generation (print, email, SMS)
- Split payment
- Tip handling

## 4. Service Catalog

- Categories (hair, nails, facial, massage)
- Per service: name, duration, base price, color code
- Staff-service assignment matrix
- Resource requirements
- Variant pricing (long hair surcharge, senior stylist)

## 5. Staff Management

- Staff profiles with roles (owner, stylist, receptionist)
- Working hours and shift assignment
- Commission structure (% or flat per service)
- Performance metrics (services done, revenue)

## 6. Inventory

- Product catalog (SKU, cost, retail, supplier)
- Stock tracking with low-stock alerts
- Purchase order generation
- Product integration with POS checkout

## 7. Reporting

- Daily revenue with breakdowns
- Service popularity ranking
- Staff performance metrics
- Client trends (new vs returning, average spend)
- Export to CSV/PDF

## Implementation Architecture

| Layer | Technology |
|---|---|
| Frontend | Flutter (cross-platform) |
| API Gateway | C++ Drogon backend |
| REST Services | Python REST-API |
| Auth | Keycloak (JWT tokens) |
| Database | PostgreSQL (Aurora) |
| Async Tasks | RabbitMQ + Dramatiq |
| Real-time | WebSocket via Drogon |
