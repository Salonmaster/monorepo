# Data Model

Core entities and relationships for the salon management system.

## Entity Overview

```
Client ──┐
         ├── Appointment ── Service
Staff ───┘        │
                  ├── Product (via CheckoutItem)
                  └── Payment

Service ── ServiceCategory
Product ── ProductCategory ── Supplier
Staff ── StaffRole ── Commission
Payment ── PaymentMethod
```

## Core Tables

### Client

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | text | Required |
| email | text | Optional, unique |
| phone | text | Optional |
| birthday | date | Optional |
| notes | text | Internal notes |
| tags | text[] | VIP, regular, etc. |
| consent_marketing | bool | GDPR |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### Appointment

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| client_id | UUID | FK → Client |
| staff_id | UUID | FK → Staff |
| status | enum | booked/confirmed/in_progress/completed/cancelled/no_show |
| start_time | timestamptz | |
| end_time | timestamptz | Calculated from services |
| notes | text | |
| tenant_id | UUID | Multi-tenant isolation |

### AppointmentService (join)

| Field | Type | Notes |
|---|---|---|
| appointment_id | UUID | FK → Appointment |
| service_id | UUID | FK → Service |
| price | decimal | Price at time of booking |
| staff_id | UUID | FK → Staff (who performed) |

### Service

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | text | "Women's Cut & Style" |
| category_id | UUID | FK → ServiceCategory |
| duration | int | Minutes |
| price | decimal | Base price |
| color | text | Calendar display |
| active | bool | Soft delete |

### Staff

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK → User (auth) |
| name | text | |
| role | enum | owner/stylist/receptionist |
| phone | text | |
| commission_type | enum | percentage/flat/none |
| commission_value | decimal | |
| active | bool | |

### Product (Inventory)

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| sku | text | Unique |
| name | text | |
| category_id | UUID | FK → ProductCategory |
| cost_price | decimal | |
| retail_price | decimal | |
| stock_qty | int | |
| min_stock | int | Low-stock threshold |
| supplier_id | UUID | FK → Supplier |

### Payment

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| appointment_id | UUID | FK → Appointment |
| method | enum | cash/card/invoice/gift_card |
| amount | decimal | |
| tip | decimal | |
| external_ref | text | Terminal transaction ID |
| created_at | timestamptz | |

### Transaction

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| appointment_id | UUID | FK → Appointment |
| payment_id | UUID | FK → Payment (nullable) |
| type | enum | service/product/discount/tax/tip |
| description | text | |
| amount | decimal | |
| quantity | int | |

## Multi-Tenant Isolation

All core tables include `tenant_id` with schema-per-tenant PostgreSQL isolation, matching the existing Salonmaster tenancy model.
