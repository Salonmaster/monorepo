# Plan of Approach

## Phases

### Phase 1 — MVP (Core Salon Operations)

| Module | Scope |
|---|---|
| Appointments | Calendar, book/edit/cancel, staff assignment, duration-based |
| Client CRM | Profile, contact, visit history, preferences, notes |
| Service Catalog | Services menu with price + duration, categories |
| POS Checkout | Service selection, product add-on, payment, receipt |
| Staff Management | Staff list, working hours, service assignments |
| Auth | Keycloak integration, role-based access (owner, staff, receptionist) |

### Phase 2 — Growth

| Module | Scope |
|---|---|
| Inventory | Stock tracking, low-stock alerts, product-POS integration |
| Online Booking | Client-facing booking page, embeddable widget |
| Payments | Card terminal integration (Stripe Terminal / SumUp) |
| Reporting | Revenue breakdown, services, staff performance |
| Multi-location | Owner dashboard across multiple salon locations |

### Phase 3 — Scale

| Module | Scope |
|---|---|
| Marketing | Email/SMS campaigns, birthday offers, re-engagement |
| Loyalty | Points system, tiers, rewards |
| Accounting | Export to Exact/Moneybird/QuickBooks |
| Marketplace | Product ordering from suppliers |

## Timeline

| Weeks | Focus |
|---|---|
| 1-2 | Architecture & design finalization |
| 3-4 | Core database + Backend API (C++ Drogon) |
| 5-6 | REST-API endpoints + Flutter client shell |
| 7-8 | Appointments + Client CRM modules |
| 9-10 | POS Checkout + Staff Management |
| 11-12 | Testing, hardening, pilot deployment |
