# SalonMaster Roadmap 💈

> A lean POS for hair, nail & beauty salons — one C++ binary, one database, one VPS.

---

## Legend

| Mark | Meaning |
|------|---------|
| ✅ | Done |
| 🔄 | In progress / partial |
| ⬜ | Todo |

---

## Phase 1: MVP — First Paying Salon (Q3 2026)

Goal: One salon can run their full day on SalonMaster. Book → Serve → Checkout → Report.

### 1.1 Backend Core

| Task | Status | Description |
|------|--------|-------------|
| **Database schema** | 🔄 | Alembic migrations exist but incomplete. Tables needed: `salons`, `users`, `staff`, `clients`, `services`, `appointments`, `transactions`, `products`, `inventory`, `loyalty_points` |
| **Salon tenant CRUD** | ⬜ | Create/read/update salon — name, address, phone, logo, opening hours, tax rate, currency. Schema-per-tenant or row-level? |
| **Staff CRUD** | ⬜ | Add/edit/remove staff. Name, role (owner/manager/stylist/receptionist), email, phone, working hours, commission rate |
| **Service catalog** | ⬜ | CRUD for services: name, duration, price, category, color, active flag, buffer time |
| **Client management** | ⬜ | CRUD clients. Name, email, phone, notes, preferences. Search. Import CSV |
| **Appointment booking** | ⬜ | Create/edit/cancel appointments. Client + service + staff + date/time. Conflict detection. Recurring appointments |
| **Appointment status flow** | ⬜ | State machine: booked → confirmed → checked_in → in_service → completed (or no_show / cancelled) |
| **Checkout / POS** | ⬜ | Add services + products → subtotal → discount → tax → total. Multiple payment methods (cash, card, mobile, gift card, invoice) |
| **Tip handling** | ⬜ | Tip per appointment, per-staff tracking, % or fixed amount |
| **Daily revenue report** | ⬜ | End-of-day: appointments, revenue, tips, products sold, payment breakdown. Per-staff breakdown |
| **Basic inventory** | ⬜ | Products: name, SKU, price, cost, stock_qty. Auto-decrement on sale. Low-stock alert |
| **Health endpoint** | ✅ | `GET /health` with DB check |
| **Metrics endpoint** | ✅ | `GET /metrics` via PromExporter plugin |

### 1.2 Authentication & Security

| Task | Status | Description |
|------|--------|-------------|
| **JWT auth (built-in)** | 🔄 | Keycloak code exists but architecture doc says drop Keycloak → built-in JWT. Needs: user registration, login, token refresh, password reset |
| **Staff login** | ⬜ | Staff authenticate via email/password → JWT → role-based access |
| **Pin-based quick auth** | ⬜ | Optional 4-digit PIN for fast staff switching at front desk |
| **API key auth** | ⬜ | For integrations and website backend → backend API calls |
| **Session middleware** | 🔄 | SessionMiddleware.h exists — wire to real auth |
| **Role-based permissions** | ⬜ | Owner (full), Manager (reports + manage), Stylist (own schedule), Receptionist (booking + checkout) |

### 1.3 Backend → AI Integration

| Task | Status | Description |
|------|--------|-------------|
| **AI module structure** | ✅ | Tool system, DeepSeek provider, conversation manager, WS + REST handlers |
| **AI natural language booking** | 🔄 | `BookAppointment` tool defined — needs real DB queries tested end-to-end |
| **AI revenue queries** | 🔄 | `QueryRevenue` tool defined — needs real DB tables |
| **AI client lookup** | 🔄 | `ClientTools` defined — needs real DB tables |
| **AI salon info / FAQ** | 🔄 | `SalonInfo` tool defined — needs salon data populated |
| **AI conversation persistence** | ⬜ | Currently in-memory (24h TTL). Store summaries in DB for long-term context |
| **AI voice interface** | ⬜ | "Hey SalonMaster" — speech-to-text → AI → text-to-speech (Flutter plugin) |

### 1.4 Website (Laravel)

| Task | Status | Description |
|------|--------|-------------|
| **Marketing homepage** | 🔄 | Frontend index exists, navbar. Needs: hero, features, pricing, testimonials, footer |
| **Online booking page** | ⬜ | Client selects service → staff → date/time → fills name/email/phone → books. Calls backend API |
| **Client self-service** | ⬜ | Client login → see upcoming appointments, book new, cancel, view history |
| **AI chatbot widget** | ⬜ | Floating chat bubble on booking page. Calls `POST /api/v1/chat` |
| **Salon backend dashboard** | 🔄 | Livewire dashboard scaffold. Needs: today's stats, appointments list, quick actions |
| **Backend: appointment management** | ⬜ | Salon staff view: calendar, book, manage appointments via web |
| **Backend: client management** | ⬜ | Search, view, edit clients via web |
| **Backend: reports** | ⬜ | Daily summary, revenue charts, export to PDF/CSV |
| **SEO & meta** | ⬜ | Title tags, descriptions, OG images, structured data, sitemap |

### 1.5 Client (Flutter)

| Task | Status | Description |
|------|--------|-------------|
| **App scaffold** | 🔄 | Bare `main.dart`. Needs: routing, theme, state management choice |
| **Login screen** | ⬜ | Email + password → JWT → persistent session |
| **Dashboard** | ⬜ | Today's appointments, revenue, quick-actions bar |
| **Calendar view** | ⬜ | Day/week view, colored appointment blocks, drag-to-move, tap-to-detail |
| **Quick booking** | ⬜ | Client search + service select + staff + time → book in <10 seconds |
| **Checkout flow** | ⬜ | Services + products → discount → payment → tip → receipt |
| **Client search** | ⬜ | Search by name/email/phone → profile with history |
| **AI chat panel** | ⬜ | WebSocket to `/chat/ws`, chat bubble UI, streaming text |
| **Offline mode** | ⬜ | SQLite local cache, queue actions, sync when online |
| **Push notifications** | ⬜ | Appointment reminders, booking alerts, low-stock warnings |

### 1.6 Docs

| Task | Status | Description |
|------|--------|-------------|
| **Tech docs** | ✅ | Architecture, deployment, monitoring, CI/CD — complete |
| **User docs: Getting Started** | 🔄 | Quick Start, Setup, Staff pages written. First Appointment is stub |
| **User docs: Appointments** | 🔄 | Calendar fully written. Booking, Waitlist, Online Booking are stubs |
| **User docs: POS** | 🔄 | Checkout fully written. Payments, Refunds, Gift Cards are stubs |
| **User docs: Dashboard** | ✅ | Overview fully written |
| **User docs: Clients** | ⬜ | All 3 pages are stubs |
| **User docs: Inventory** | ⬜ | All 3 pages are stubs |
| **User docs: Staff** | ⬜ | All 3 pages are stubs |
| **User docs: Reports** | ⬜ | All 4 pages are stubs |
| **User docs: Settings** | ⬜ | All 4 pages are stubs |
| **User docs: AI Assistant** | ✅ | Written |
| **Screenshots & GIFs** | ⬜ | All docs need real UI screenshots |
| **Video tutorials** | ⬜ | Quick Start walkthrough, booking demo, checkout demo |

### 1.7 DevOps & Deploy

| Task | Status | Description |
|------|--------|-------------|
| **Docker-compose dev** | ✅ | Backend + Website + PostgreSQL + Mailpit |
| **Production deploy** | ⬜ | Single VPS setup script. docker-compose.prod.yml. SSL via Caddy or nginx |
| **Database backups** | ⬜ | Automated pg_dump → rclone to Proton Drive |
| **CI/CD → auto-deploy** | ⬜ | Jenkins pipeline: on main push → build → test → push to Harbor → deploy to VPS |
| **Monitoring** | ⬜ | Uptime check, alert on `/health` failure, Prometheus + Grafana (optional) |

---

## Phase 2: Growth — Multi-Salon, Polish, Marketing (Q4 2026)

Goal: 10+ paying salons. Smooth UX. Salon owners love it and tell others.

### 2.1 Multi-Tenancy

| Task | Status | Description |
|------|--------|-------------|
| **Schema-per-tenant isolation** | ⬜ | Each salon gets its own PostgreSQL schema. Migrations run per-tenant. Connection pool per tenant |
| **Tenant-aware routing** | ⬜ | `*.salonmaster.dev` subdomain or path-based routing. Middleware resolves tenant from host |
| **Shared user table** | ⬜ | `public.users` for auth, `{tenant}.staff` for roles. One login → multiple salons |
| **Super-admin panel** | ⬜ | View all salons, usage stats, billing status, support access |

### 2.2 Advanced Features

| Task | Status | Description |
|------|--------|-------------|
| **Online booking embed** | ⬜ | JavaScript widget salons embed on their own website. Configurable colors, services filter |
| **SMS/email reminders** | ⬜ | Automated appointment reminders via Twilio/SendGrid. Configurable timing |
| **Loyalty program** | ⬜ | Points per visit/spend, rewards (free service, discount), auto-apply at checkout |
| **Gift cards** | ⬜ | Sell, redeem, track balance. Digital + printable |
| **Waitlist management** | ⬜ | Walk-ins queue, estimated wait time, notify when ready |
| **Staff scheduling** | ⬜ | Set working hours per staff, time-off requests, shift swapping |
| **Commission tracking** | ⬜ | Per-service and per-product commission rates. Payout reports per pay period |
| **Inventory: purchase orders** | ⬜ | Create POs, receive stock, track suppliers, cost tracking |
| **Receipts: print + email** | ⬜ | Thermal printer support (ESC/POS), branded HTML email receipts |
| **Multi-language** | ⬜ | i18n: English, Dutch, German, French, Spanish, Italian. Flutter + Website + Backend error messages |

### 2.3 Analytics & Insights

| Task | Status | Description |
|------|--------|-------------|
| **Revenue reports** | ⬜ | Daily/weekly/monthly breakdowns. By service, product, staff. Year-over-year comparison |
| **Client insights** | ⬜ | Retention rate, average spend, visit frequency, churn risk, rebooking rate |
| **Staff performance** | ⬜ | Utilization rate, revenue generated, client satisfaction, rebooking rate |
| **Export** | ⬜ | CSV, PDF. Tax-ready reports. Accountant export format |

### 2.4 Integrations

| Task | Status | Description |
|------|--------|-------------|
| **Payment terminals** | ⬜ | SumUp, Square, Stripe Terminal integration. Auto-reconcile |
| **Accounting** | ⬜ | Export to Exact, QuickBooks, Xero. Or just CSV for accountant |
| **Google Calendar sync** | ⬜ | Staff can sync their appointments to personal Google Calendar |
| **Social login for clients** | ⬜ | "Book with Google/Apple" on booking page |
| **Marketing: Mailchimp** | ⬜ | Export client list. Segment by last visit, spend, service type |

### 2.5 Website Enhancements

| Task | Status | Description |
|------|--------|-------------|
| **Salon directory** | ⬜ | Public directory page listing salons using SalonMaster (opt-in). SEO juice |
| **Blog** | ⬜ | Salon tips, industry trends, product updates. Content marketing engine |
| **Pricing page** | ⬜ | Tiered pricing: Solo (€29/mo), Team (€59/mo), Enterprise (custom) |
| **Onboarding wizard** | ⬜ | 5-step guided setup after signup: salon info → services → staff → hours → first booking |

---

## Phase 3: Scale — Platform, Ecosystem, AI-First (2025)

Goal: 100+ salons. Platform features. AI is the primary interface.

### 3.1 Platform

| Task | Status | Description |
|------|--------|-------------|
| **Public API** | ⬜ | RESTful API for third-party integrations. API keys, rate limiting, docs (OpenAPI) |
| **Webhook system** | ⬜ | Events fire webhooks: `appointment.created`, `payment.completed`, `client.registered` |
| **App marketplace** | ⬜ | Third-party extensions. e.g., specialized reporting, niche integrations |
| **White-label** | ⬜ | Salons can use their own domain, branding, colors. CNAME support |

### 3.2 AI-First Experience

| Task | Status | Description |
|------|--------|-------------|
| **AI voice assistant** | ⬜ | "Hey SalonMaster, book my next client" — hands-free operation for stylists |
| **AI-driven insights** | ⬜ | "You had 3 no-shows this week. Send them a rebooking offer?" |
| **AI marketing** | ⬜ | "5 clients haven't visited in 6 weeks. Want me to draft a 'we miss you' email?" |
| **AI onboarding concierge** | ⬜ | New salon owners talk to AI. It sets up services, staff, hours, and pricing conversationally |
| **AI booking assistant (client-facing)** | ⬜ | "I need a haircut next week, preferably Tuesday afternoon with someone who's good with curly hair" → AI finds the perfect slot |

### 3.3 Scale Infrastructure

| Task | Status | Description |
|------|--------|-------------|
| **K8s deployment** | 🔄 | Helm charts exist in `Kubernetes/`. ArgoCD, CNPG, Vault, Cloudflare tunnel. Needs testing & docs |
| **Read replicas** | ⬜ | PostgreSQL read replicas for read-heavy workloads (reports, client lookups) |
| **Caching layer** | ⬜ | Redis for session cache, service catalog, frequent queries |
| **CDN for Website** | ⬜ | Cloudflare CDN for static assets, image optimization |
| **Load testing** | ⬜ | Prove 50+ salons on a single VPS. Identify and fix bottlenecks |

### 3.4 Mobile Excellence

| Task | Status | Description |
|------|--------|-------------|
| **App Store publishing** | ⬜ | iOS App Store + Google Play. Screenshots, descriptions, privacy policy |
| **Offline-first architecture** | ⬜ | Full offline capability: book, checkout, client lookup all work without internet. Sync when connected |
| **Tablet optimizations** | ⬜ | iPad/Android tablet layouts. Split-view: calendar left, detail right |
| **Biometric auth** | ⬜ | Face ID / fingerprint for quick staff login |

---

## Summary

| Phase | Timeline | Salons | Core Deliverable |
|-------|----------|--------|------------------|
| **Phase 1 — MVP** | Q3 2026 | 1 | Full daily workflow: book → serve → checkout → report |
| **Phase 2 — Growth** | Q4 2026 | 10+ | Multi-tenant, polish, integrations, online booking |
| **Phase 3 — Scale** | 2027 | 100+ | Platform, AI-first, ecosystem |

---

## Immediate Next Actions (Priority Order)

1. ⬜ **Database schema** — Design and create migrations for all Phase 1 tables
2. ⬜ **Auth system** — Drop Keycloak, implement built-in JWT auth (register, login, refresh)
3. ⬜ **Staff + Services CRUD** — Core data models, endpoints, Flutter screens
4. ⬜ **Appointment booking** — Calendar endpoint + booking logic (conflict detection)
5. ⬜ **Checkout flow** — Payment processing, receipt generation
6. ⬜ **Flutter UI** — Login → Dashboard → Calendar → Checkout screens
7. ⬜ **Online booking page** — Website: service → staff → date/time → book
8. ⬜ **End-to-end walkthrough** — One real test: book → serve → checkout → report
9. ⬜ **Fill user doc stubs** — All 28 remaining pages
10. ⬜ **Production VPS deploy** — Hetzner CX22, SSL, backups, monitoring

---

_Last updated: 2026-06-20_
