# SalonMaster Roadmap 💈

> A lean POS for hair, nail & beauty salons — one C++ binary, one database, one VPS.  
> Target: €4/mo Hetzner CX22. Profit from salon ≥2.

---

## Legend

| Mark | Meaning |
|------|---------|
| ✅ | Done / shipped |
| 🔄 | In progress / partial / wired but not end-to-end |
| ⬜ | Todo / not started |

---

## ⚠️ Critical Blockers (must resolve first)

These are **not** just tasks — they are architectural contradictions or dead-end code that block everything else:

| Blocker | Impact | Action Required |
|---------|--------|----------------|
| **Keycloak is still the auth backend** | Architecture doc says "built-in JWT, drop Keycloak" but `Authentication.cpp`, `Keycloak.h`, `Globals.h`, both DB migrations, `SessionMiddleware`, Website `KeycloakProvider`, and K8s Keycloak chart all assume Keycloak. The two systems cannot coexist. The codebase is split on identity. | **Decide now.** Either (a) keep Keycloak and update all docs/plans, or (b) rip out Keycloak and implement built-in JWT. Current plan = (b). Until resolved, no auth-related task is meaningful. |
| **Database has zero business tables** | Only 2 Alembic migrations exist: `code_verifiers` (Keycloak PKCE) and `sessions` (Keycloak tokens). The AI tools in `BookAppointment.h`, `ClientTools.h`, `QueryRevenue.h`, `SalonInfo.h` all query tables (`clients`, `services`, `staff`, `appointments`, `transactions`, `salon_profile`, `opening_hours`) that **do not exist**. The tools compile but cannot pass an integration test. | Database schema migration is the #1 coding priority. Nothing works without it. |
| **Stale product docs contradict architecture** | `Docs/docs/product/plan.md` references "Python REST-API", "RabbitMQ + Dramatiq", "AWS Aurora", and "Keycloak". `Docs/docs/product/modules.md` says the same. These are from an earlier design and contradict the current "C++ Drogon monolith + built-in JWT + in-process jobs + self-hosted PG" decision. | Rewrite product docs to match architecture — or they mislead every new contributor. |
| **Flutter app is the default counter template** | `Client/lib/main.dart` is Flutter's `flutter create` output. Zero SalonMaster code. No login, no dashboard, no state management choice. Even the `Client/README.md` is the Flutter default. | The client is a greenfield. Re-scope Phase 1 Flutter goals aggressively. |

---

## Phase 1: MVP — First Paying Salon (Q3 2026)

Goal: One salon can run their full day on SalonMaster. Book → Serve → Checkout → Report.

### 0. Foundation (pre-requisite — week 1-2)

Before any feature work, fix the blockers:

| Task | Status | Description |
|------|--------|-------------|
| **Resolve auth architecture** | 🔄 | Decide Keycloak vs built-in JWT. **If built-in JWT:** remove Keycloak code from Backend, Website, K8s, Globals. Implement `/register`, `/login`, `/refresh`, `/reset` with bcrypt + JWT. Replace `SessionMiddleware` with JWT verification. Drop `code_verifiers` + `sessions` migrations, create `users` + `refresh_tokens` migrations. |
| **Design & create full DB schema** | ⬜ | Alembic migrations for all Phase 1 tables: `salons`, `users`, `staff`, `clients`, `services`, `service_categories`, `appointments`, `appointment_services`, `transactions`, `payments`, `products`, `product_categories`, `inventory_movements`, `salon_settings`, `opening_hours`. Row-level `tenant_id` isolation (schema-per-tenant is Phase 2). |
| **Rewrite stale product docs** | ⬜ | Update `plan.md`, `modules.md` to reflect C++ Drogon monolith + built-in JWT + no message queue + self-hosted PG. Remove all references to Python REST-API, RabbitMQ, Dramatiq, Aurora, Keycloak. |
| **Seed Flutter project structure** | ⬜ | Choose state management (Riverpod or Bloc). Set up routing (go_router), theme, API client (dio), WebSocket client, folder structure (`screens/`, `models/`, `services/`, `widgets/`). Delete the counter. |
| **Agree on API contract** | ⬜ | Document all REST + WS endpoints in one OpenAPI spec. Share between Backend, Website, and Flutter. Generate types where possible. |

### 1.1 Backend Core

| Task | Status | Description |
|------|--------|-------------|
| **Salon CRUD** | ⬜ | Create/read/update salon — name, address, phone, logo URL, currency, tax rate default, timezone. Single-tenant mode (no schema switching yet; `tenant_id` column prep for Phase 2). |
| **Staff CRUD** | ⬜ | Add/edit/remove staff. Name, role (owner/stylist/receptionist), email, phone, commission_rate, active flag. Each staff links to a `users` row for login. |
| **Service catalog CRUD** | ⬜ | Services: name, duration_minutes, price, category, color, active. Categories: name, sort_order. |
| **Client CRUD** | ⬜ | Name, email, phone, birthday, notes, tags[], consent_marketing (GDPR), created_at. Search by name/email/phone. CSV import endpoint. |
| **Appointment booking** | ⬜ | Create/edit/cancel. Client + N services + staff + start_time. Conflict detection (staff double-book, overlapping times). Status flow: booked → confirmed → checked_in → in_service → completed / no_show / cancelled. |
| **Checkout / POS** | ⬜ | Select appointment → add services + products → subtotal → discount (% or fixed) → tax → total → payment (cash, card, mobile, gift_card, invoice) → tip. Generates transaction rows. |
| **Daily revenue report** | ⬜ | `GET /api/v1/reports/daily?date=YYYY-MM-DD`. Revenue, tips, transaction count, payment method breakdown, per-staff breakdown, top services, top products. |
| **Basic inventory** | ⬜ | Products: name, SKU, cost_price, retail_price, stock_qty, min_stock, category. Auto-decrement on sale. Low-stock threshold alert. |
| **Health endpoint** | ✅ | `GET /health` — returns 200 + DB connectivity status. |
| **Metrics endpoint** | ✅ | `GET /metrics` — Prometheus exporter. App metrics: request count, latency, active WebSocket connections. |
| **API error standardization** | ⬜ | Consistent JSON error shape `{"error": "...", "code": "...", "details": {...}}`. HTTP status code mapping. Validation error format. |

### 1.2 Authentication & Security

| Task | Status | Description |
|------|--------|-------------|
| **Built-in JWT auth** | ⬜ | Replace Keycloak entirely. `POST /auth/register` (email + password → user + verification), `POST /auth/login` (email + password → access + refresh tokens), `POST /auth/refresh`, `POST /auth/forgot-password`, `POST /auth/reset-password`. Access token: 15min, refresh: 7 days. |
| **JWT middleware** | ⬜ | Replace `SessionMiddleware` with JWT verification middleware. Read `Authorization: Bearer <token>`, validate signature + expiry, attach user + role to request context. |
| **Staff login** | ⬜ | Staff login via email/password → JWT with role claim → role-based route guards. |
| **PIN quick-auth** | ⬜ | Optional 4-digit PIN stored hashed on `staff` table. `POST /auth/pin` for fast desk switching. Logs PIN-based auth separately. |
| **API key auth** | ⬜ | Server-to-server auth. `X-API-Key` header. For Website → Backend and future integrations. Scoped by permission. |
| **Role-based access** | ⬜ | Owner (full), Manager (reports + staff mgmt), Stylist (own schedule + clients), Receptionist (booking + checkout). Enforced in middleware per-route. |
| **CORS** | ⬜ | Strict CORS config: allow Website origin + Flutter app origin only. |
| **Rate limiting** | ⬜ | Per-IP + per-user limits on auth endpoints (5 attempts/5min on login). Per-endpoint limits on heavy queries. |

### 1.3 AI Integration

AI is a differentiator, not an afterthought. The module structure already exists — wire it to real data.

| Task | Status | Description |
|------|--------|-------------|
| **AI module structure** | ✅ | `AiAssistant`, `ToolRegistry`, `DeepSeekProvider`, `ConversationManager`, WS + REST handlers — all built. |
| **Wire AI tools to real DB** | 🔄 | `BookAppointment`, `ClientTools`, `QueryRevenue`, `SalonInfo` all have correct logic but query non-existent tables. Update SQL to match the new schema, then integration-test each tool end-to-end. |
| **AI booking flow** | ⬜ | "Book Sasha for a haircut on Friday at 2pm with Anna" → AI resolves names → checks availability → confirms → creates appointment. End-to-end test required. |
| **AI revenue queries** | ⬜ | "How much did we make today?" → AI calls `query_revenue` → returns formatted answer. "Break that down by stylist" → follow-up query. |
| **AI conversation persistence** | ⬜ | Currently in-memory with 24h TTL (`ConversationManager`). Store conversation summaries in `ai_conversations` table. Client can resume from any device. |
| **AI client-facing chatbot** | ⬜ | Website floating chat bubble → `POST /api/v1/chat` → AI answers booking questions, service info, hours, pricing. No auth required for FAQ; auth required for booking actions. |

### 1.4 Website (Laravel)

| Task | Status | Description |
|------|--------|-------------|
| **Marketing homepage** | 🔄 | Template exists (SB UI Kit) but has lorem ipsum and "SB UI Kit Pro" brand. Replace with: hero (headline + CTA → "Try SalonMaster free"), features (3 key), pricing (solo €29/mo), testimonials (placeholder), footer with links. |
| **Online booking page** | ⬜ | Public page: select service → select staff → pick date/time → fill name/email/phone → confirm. Calls backend API. No login required. Shows confirmation + calendar invite option. |
| **Client self-service portal** | ⬜ | Client login (or magic link) → upcoming appointments → book new → cancel → view history. |
| **AI chatbot widget** | ⬜ | Floating chat on booking page. Calls `POST /api/v1/chat` with `salon_id`. Answers FAQ + can book appointments conversationally. |
| **Salon backend dashboard** | 🔄 | Livewire scaffold exists (Dutch, generic metrics). Replace with: today's stats (appointments, revenue, new clients), upcoming appointments list, quick actions (new booking, checkout), low-stock alerts. |
| **Backend: calendar & appointments** | ⬜ | Day/week calendar view (FullCalendar or custom). Click slot → book. Click appointment → details + actions. Filter by staff. |
| **Backend: client management** | ⬜ | Table with search, pagination. Click row → profile (history, notes, upcoming). Add/edit client. Import CSV. |
| **Backend: reports** | ⬜ | Daily summary, revenue charts (Chart.js), export to PDF/CSV. Date range picker. |
| **Backend: settings** | ⬜ | Salon profile, services catalog, staff list, opening hours, tax rate, payment methods. |
| **SEO & meta** | ⬜ | Title tags, meta descriptions, OG images, structured data (LocalBusiness), sitemap.xml. |
| **GDPR compliance** | ⬜ | Cookie consent banner, privacy policy page, data export/deletion request flow, consent checkboxes on booking. |

### 1.5 Client (Flutter)

Scope aggressively. The Flutter app is for salon staff at the desk, not clients browsing. Focus on the terminal.

| Task | Status | Description |
|------|--------|-------------|
| **Project structure & setup** | ⬜ | Riverpod or Bloc state management. go_router navigation. Dio HTTP client with JWT interceptor. WebSocket connection manager. Folder: `lib/{screens,models,services,widgets,config}`. Flavor for dev/staging/prod. |
| **Login + PIN screen** | ⬜ | Email + password → store JWT in secure storage. PIN option after first login. "Remember me" toggle. |
| **Today dashboard** | ⬜ | Today's appointments (timeline), revenue counter, pending checkouts, low-stock indicator. Pull-to-refresh. WebSocket for live updates. |
| **Calendar (day view)** | ⬜ | Scrollable timeline, colored appointment blocks by service category. Tap → detail. Long-press → move. "+" FAB → quick-book. Swipe left/right for next/prev day. |
| **Quick booking flow** | ⬜ | Client search (typeahead) → service select → staff select → time pick → confirm. Target: <10 seconds. |
| **Checkout flow** | ⬜ | Tap appointment → "Checkout" → services summary + add products → discount → payment method → tip → complete. Receipt preview. |
| **Client search & profile** | ⬜ | Typeahead search by name/phone. Profile: contact, visit history, upcoming, notes, preferences. "Book again" one-tap. |
| **AI chat panel** | ⬜ | WebSocket to `/chat/ws`. Chat bubble UI. Streaming text. Context-aware: includes current salon/staff. |
| **Local SQLite cache** | ⬜ | Offline-first: cache today's appointments, service catalog, client list. Queue writes. Sync when online. WatermelonDB or drift. |
| **Push notifications** | ⬜ | FCM for appointment reminders, new booking alerts, low-stock. Tap notification → deep link to relevant screen. |

### 1.6 Docs

| Task | Status | Description |
|------|--------|-------------|
| **Tech docs** | ✅ | Architecture, deployment, monitoring, CI/CD — all exist. |
| **Update product docs** | ⬜ | Rewrite `plan.md`, `modules.md` to match current architecture. Delete Python/RabbitMQ/Aurora/Keycloak references. |
| **User docs: Getting Started** | 🔄 | Quick Start ✅, Setup ✅, Staff ✅. First Appointment is stub. |
| **User docs: Appointments** | 🔄 | Calendar ✅. Booking, Waitlist, Online Booking are stubs. |
| **User docs: POS** | 🔄 | Checkout ✅. Payments, Refunds, Gift Cards are stubs. |
| **User docs: Dashboard** | ✅ | Overview fully written. |
| **User docs: Clients** | ⬜ | All pages stubs. |
| **User docs: Inventory** | ⬜ | All pages stubs. |
| **User docs: Staff** | ⬜ | All pages stubs. |
| **User docs: Reports** | ⬜ | All pages stubs. |
| **User docs: Settings** | ⬜ | All pages stubs. |
| **User docs: AI Assistant** | ✅ | Written. |
| **Screenshots & GIFs** | ⬜ | Blocked on working UI. Add as features ship. |
| **API reference** | ⬜ | OpenAPI spec as source of truth. Generate docs from it. |

### 1.7 DevOps & Deploy

| Task | Status | Description |
|------|--------|-------------|
| **Docker Compose dev** | ✅ | Backend + Website + PostgreSQL + Mailpit. Working. |
| **Production docker-compose** | ⬜ | `docker-compose.prod.yml`: backend + website + postgres. No dev tools. Resource limits. Health checks. |
| **SSL & reverse proxy** | ⬜ | Caddy auto-SSL via Let's Encrypt. Route: `app.salonmaster.dev` → backend:8080, `www.salonmaster.dev` → website:8080. |
| **VPS setup script** | ⬜ | Single `./deploy.sh` that: installs Docker + docker-compose, clones repo, sets env vars, pulls images, starts services, sets up crontab for backups. |
| **Database backups** | ⬜ | Nightly `pg_dump` → gzip → rclone to Proton Drive. Retention: 30 daily + 12 monthly. Backup verification script. |
| **Logging & rotation** | ⬜ | Structured JSON logs. journald or logrotate. Keep 30 days. |
| **Uptime monitoring** | ⬜ | External health check (cron-job.org or UptimeRobot) pings `GET /health` every 5 min. Alert to email on 3 consecutive failures. |
| **CI/CD pipeline** | ⬜ | GitHub Actions: on push → build Docker images → run unit tests + lint → push to registry → SSH deploy. Faster than full Jenkins. |
| **Firewall** | ⬜ | ufw: allow 22, 80, 443. Drop everything else. Fail2ban for SSH. |

---

## Phase 2: Growth — Multi-Salon, Polish, Marketing (Q4 2026)

Goal: 10+ paying salons. Smooth UX. Salon owners tell other salon owners.

### 2.1 Multi-Tenancy

| Task | Status | Description |
|------|--------|-------------|
| **Schema-per-tenant** | ⬜ | Each salon gets its own PostgreSQL schema. Migrations run per-tenant. Connection pool resolves schema from `public.salons`. |
| **Tenant routing** | ⬜ | `{slug}.salonmaster.dev` → subdomain resolves tenant. Middleware sets schema. Fallback: path-based like `salonmaster.dev/s/salon-name`. |
| **Shared auth table** | ⬜ | `public.users` for login. `{tenant}.staff` for salon roles. One user → multiple salons possible. |
| **Super-admin panel** | ⬜ | Owner-operators view: all salons, usage stats, subscription status. Impersonate salon for support. |
| **Salon signup flow** | ⬜ | Self-serve: signup → choose subdomain → create salon → onboarding wizard → payment → live. Free trial (14 days, no CC required). |

### 2.2 Advanced Features

| Task | Status | Description |
|------|--------|-------------|
| **Online booking embed** | ⬜ | `<script>` widget salons embed on their own site. Configurable: colors, services filter, staff filter. iframe-free. |
| **SMS/email reminders** | ⬜ | Automated 24h-before reminders via Twilio/SendGrid. Configurable timing. Client can reply to confirm/cancel. |
| **Loyalty program** | ⬜ | Points per visit or spend. Rewards (free service, discount). Auto-suggest at checkout. |
| **Gift cards** | ⬜ | Sell physical + digital. Redeem at checkout. Track balance. Expiry date. |
| **Waitlist** | ⬜ | Walk-in queue. Estimated wait time. Notify via SMS when spot opens. |
| **Staff scheduling** | ⬜ | Working hours per staff. Time-off requests. Shift swapping. Overtime alerts. |
| **Commission tracking** | ⬜ | Per-service % or flat. Per-product %. Payout report per pay period. |
| **Purchase orders** | ⬜ | Create PO, receive stock, track supplier costs. Auto-suggest reorder based on min_stock. |
| **Receipts: print + email** | ⬜ | ESC/POS thermal printer support. Branded HTML email receipts with salon logo. |
| **Multi-language (i18n)** | ⬜ | English, Dutch, German, French, Spanish. Flutter `.arb` files. Laravel lang files. Backend error messages. |

### 2.3 Analytics & Insights

| Task | Status | Description |
|------|--------|-------------|
| **Revenue dashboards** | ⬜ | Daily/weekly/monthly. By service, product, staff. Year-over-year. Forecast. |
| **Client insights** | ⬜ | Retention rate, average spend, visit frequency, churn risk, rebooking rate. "At-risk" client flag. |
| **Staff performance** | ⬜ | Utilization %, revenue generated, client satisfaction (optional rating), rebooking rate. |
| **Export** | ⬜ | CSV, PDF. Tax-ready reports. Accountant format. Scheduled email delivery. |

### 2.4 Integrations

| Task | Status | Description |
|------|--------|-------------|
| **Payment terminals** | ⬜ | SumUp Air integration. Auto-reconcile. Stripe Terminal as alternative. |
| **Accounting export** | ⬜ | CSV format for Exact, QuickBooks. SnelStart (Dutch) format. |
| **Calendar sync** | ⬜ | Staff can sync their appointments to Google/Apple Calendar via CalDAV or API. Read-only or two-way. |
| **Client social login** | ⬜ | "Book with Google/Apple" on online booking page. Reduces friction for new clients. |
| **Mailchimp / mailing** | ⬜ | Export segmented client list. Sync opt-in status. Birthday automations. |

### 2.5 Website Polishing

| Task | Status | Description |
|------|--------|-------------|
| **Salon directory** | ⬜ | Public directory of salons using SalonMaster (opt-in). SEO boost. Schema.org markup for each listing. |
| **Blog** | ⬜ | Content marketing: salon tips, industry trends, product updates. Static site or Laravel blog. |
| **Pricing page** | ⬜ | Solo (€29/mo), Team (€59/mo), Enterprise (custom). Feature comparison table. FAQ section. |
| **Onboarding wizard** | ⬜ | 5-step guided setup: salon info → services → staff → hours → first booking. Pre-fills from AI if available. |
| **Landing page optimization** | ⬜ | A/B test headlines. Social proof ("X salons trust SalonMaster"). Demo video. |

---

## Phase 3: Scale — Platform, Ecosystem, AI-First (2027)

Goal: 100+ salons. AI becomes the default interface. Platform for third-party developers.

### 3.1 Platform

| Task | Status | Description |
|------|--------|-------------|
| **Public REST API** | ⬜ | Full REST API with API keys, rate limiting, OpenAPI docs, versioning (`/api/v1/`). |
| **Webhook system** | ⬜ | Event-driven: `appointment.created`, `payment.completed`, `client.registered`. Retry with backoff. Dashboard to manage. |
| **App marketplace** | ⬜ | Third-party extensions. e.g., specialized reporting, niche integrations. Review process. |
| **White-label** | ⬜ | Salon's own domain + branding + colors. CNAME support. Custom CSS. |

### 3.2 AI-First Experience

| Task | Status | Description |
|------|--------|-------------|
| **AI voice assistant** | ⬜ | "Hey SalonMaster, book my next client" — hands-free for stylists. STT → AI → TTS. Flutter plugin for voice. |
| **AI proactive insights** | ⬜ | Daily briefing: "3 no-shows this week. Send rebooking offers?" Proactive, not reactive. |
| **AI marketing assistant** | ⬜ | "5 clients haven't visited in 6 weeks. Draft a 'we miss you' email." AI generates, owner approves, sends. |
| **AI onboarding concierge** | ⬜ | New salons talk to AI. It sets up their services, staff, hours, and pricing conversationally. |
| **AI client booking assistant** | ⬜ | "I need a haircut next week, preferably Tuesday afternoon with someone good with curly hair" → AI finds slot. |
| **AI report narration** | ⬜ | "How was this month?" → AI narrates trends, highlights, warning signs in plain language. |

### 3.3 Scale Infrastructure

| Task | Status | Description |
|------|--------|-------------|
| **K8s deployment** | 🔄 | Helm charts, Stylist CLI, ArgoCD, CNPG, Vault all exist in `Kubernetes/`. Needs: end-to-end deployment test, HA PostgreSQL setup, load balancer config, documented migration path from docker-compose. |
| **Read replicas** | ⬜ | PostgreSQL read replicas for reports + client lookups. PgBouncer for connection pooling. |
| **Caching layer** | ⬜ | Redis for session cache, service catalog, frequent queries. Invalidate on write. |
| **CDN** | ⬜ | Cloudflare CDN for static assets, image optimization, DDoS protection. |
| **Load testing** | ⬜ | k6 or Locust. Target: 50 concurrent salons on CX22. Profile + optimize bottlenecks. |
| **Horizontal scaling** | ⬜ | Multiple backend instances behind nginx/HAProxy. Sticky sessions for WebSockets or migrate to Redis-backed WS. |

### 3.4 Mobile Excellence

| Task | Status | Description |
|------|--------|-------------|
| **App Store publishing** | ⬜ | iOS App Store + Google Play. Screenshots, descriptions, privacy policy. TestFlight beta. |
| **Full offline capability** | ⬜ | Book, checkout, client lookup all work without internet. Conflict resolution on sync. |
| **Tablet layout** | ⬜ | iPad/Android tablet split-view: calendar left, detail right. Landscape + portrait. |
| **Biometric auth** | ⬜ | Face ID / fingerprint for instant staff login. Fallback to PIN. |
| **Widget homescreen** | ⬜ | Android/iOS widget: today's appointment count + next up + daily revenue. |

---

## Summary

| Phase | Timeline | Salons | Revenue (est.) | Core Deliverable |
|-------|----------|--------|-----------------|------------------|
| **Phase 1 — MVP** | Q3 2026 | 1–3 | €87–€117/mo | Full daily workflow: book → serve → checkout → report |
| **Phase 2 — Growth** | Q4 2026 | 10+ | €290/mo+ | Multi-tenant, polish, online booking, referrals |
| **Phase 3 — Scale** | 2027 | 100+ | €2,900/mo+ | Platform, AI-first, ecosystem |

---

## Immediate Next Actions (Week 1–2)

These are sequenced. Each blocks the next.

| # | Action | Why Now |
|---|--------|---------|
| 1 | **Decide auth architecture** | Keycloak vs built-in JWT. Code is split. Choose, document, then execute. No auth = no features. |
| 2 | **Design & migrate full DB schema** | Zero business tables exist. AI tools can't run. All features blocked. |
| 3 | **Rewrite stale product docs** | `plan.md` and `modules.md` are misleading. Fix before they confuse more work. |
| 4 | **Seed Flutter project properly** | It's a counter app. Choose stack, set up structure, so feature work can begin. |
| 5 | **API contract (OpenAPI spec)** | Backend, Website, and Flutter need a shared truth before they diverge. |
| 6 | **Wire AI tools to real DB** | Tools exist. Tables don't. After #2, test BookAppointment end-to-end. |
| 7 | **Production VPS deploy** | Get one real server live with SSL + backups before feature work. Deploy early, deploy often. |

---

## Cost Reality Check

| Item | Monthly Cost |
|------|-------------|
| Hetzner CX22 (2GB, 1 vCPU) | €3.99 |
| Domain (salonmaster.dev) | ~€1.00 |
| DeepSeek API (moderate use) | ~€5.00 |
| SendGrid (email) | Free tier |
| Twilio (SMS — Phase 2) | ~€10.00 |
| **Total infra cost per salon** | **<€1.00** |
| **Recommended pricing: Solo tier** | **€29/mo** |

At €29/mo per salon with €5/mo total infra cost (shared), breakeven is 1 salon on a CX22. Every salon beyond that is ~85% margin before time.

---

_Last updated: 2026-06-20 — Reviewed against full codebase._
