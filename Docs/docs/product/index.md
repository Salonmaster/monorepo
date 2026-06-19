# 💈 Salonmaster Product

A lean Point of Sale and management platform for hair, nail, and beauty salons.

---

## Fast Facts

| | |
|---|---|
| **Target** | Hair, nail & beauty salons |
| **Backend** | C++23 Drogon (single binary monolith) |
| **Database** | PostgreSQL (self-hosted on same VPS) |
| **Auth** | Built-in JWT (no external auth server) |
| **Client** | Flutter (iOS, Android, macOS, Linux) |
| **Website** | Laravel (marketing + online booking) |
| **Hosting** | €4/mo Hetzner VPS |

---

## Product Principles

1. **Speed at the desk** — check-in to checkout under 30 seconds
2. **Offline-capable** — salon Wi-Fi fails, POS keeps working (Flutter local SQLite + sync)
3. **Multi-terminal** — front desk + stylist stations stay in sync via WebSocket
4. **Low price** — flat monthly fee, no per-seat pricing, €4 hosting base
5. **Data ownership** — salon exports everything, no vendor lock-in
