#pragma once
#include "../Tool.h"
#include <drogon/drogon.h>
#include <string>

namespace Ai::Tools {

inline void registerSalonInfoTools() {
    auto& reg = ToolRegistry::instance();

    reg.registerTool({
        "get_salon_info",
        "Get information about the salon: opening hours, address, services offered, "
        "pricing, policies. Use this to answer FAQ questions from clients.",
        {
            {"topic", "string", "What info to get: hours, services, pricing, policies, "
                                 "contact, parking, wifi, or all", false}
        },
        [](const Json::Value& args) -> Json::Value {
            auto db = drogon::app().getDbClient();
            auto topic = args.get("topic", "all").asString();

            Json::Value info;
            try {
                // Salon profile
                auto salon = db->execSqlSync(
                    "SELECT name, address, phone, email, website, timezone FROM salon_profile LIMIT 1");
                if (!salon.empty()) {
                    info["name"] = salon[0]["name"].asString();
                    info["address"] = salon[0]["address"].asString();
                    info["phone"] = salon[0]["phone"].asString();
                    info["email"] = salon[0]["email"].asString();
                    info["website"] = salon[0]["website"].asString();
                }

                // Opening hours
                auto hours = db->execSqlSync(
                    "SELECT day_of_week, open_time, close_time FROM opening_hours "
                    "WHERE is_closed = false ORDER BY day_of_week");
                Json::Value hoursArr(Json::arrayValue);
                for (const auto& row : hours) {
                    Json::Value h;
                    h["day"] = row["day_of_week"].asInt();
                    h["open"] = row["open_time"].asString();
                    h["close"] = row["close_time"].asString();
                    hoursArr.append(h);
                }
                info["opening_hours"] = hoursArr;

                // Services (just names + prices for FAQ)
                auto services = db->execSqlSync(
                    "SELECT name, price, duration_minutes, category "
                    "FROM services WHERE is_active = true ORDER BY category, name");
                Json::Value svcArr(Json::arrayValue);
                for (const auto& row : services) {
                    Json::Value s;
                    s["name"] = row["name"].asString();
                    s["price"] = row["price"].as<double>();
                    s["duration_minutes"] = row["duration_minutes"].as<int>();
                    s["category"] = row["category"].asString();
                    svcArr.append(s);
                }
                info["services"] = svcArr;

                info["message"] = "Here's the salon information you requested.";
                return info;
            } catch (const std::exception& e) {
                Json::Value fallback;
                fallback["message"] = "SalonMaster is a POS system for hair, nail, and beauty salons. "
                                      "Please contact the salon directly for specific pricing and availability.";
                fallback["note"] = "Database not yet configured with salon details.";
                return fallback;
            }
        }
    });

    reg.registerTool({
        "get_help",
        "Provide help and guidance on how to use SalonMaster features. "
        "Covers: booking, checkout, client management, reports, settings, inventory, staff.",
        {
            {"feature", "string", "Which feature to help with: booking, checkout, clients, "
                                   "reports, inventory, staff, settings, online_booking, all", true}
        },
        [](const Json::Value& args) -> Json::Value {
            auto feature = args["feature"].asString();
            Json::Value help;
            help["feature"] = feature;

            std::unordered_map<std::string, std::string> guides = {
                {"booking", "To book an appointment:\n1. Open the Calendar\n2. Click an empty time slot\n"
                            "3. Search for or create a client\n4. Select a service\n5. Confirm the booking\n\n"
                            "You can also press 'N' for quick-booking, or use the + button in the sidebar."},
                {"checkout", "To process a checkout:\n1. Click on an in-service or completed appointment\n"
                             "2. Click 'Checkout'\n3. Verify services and add any products\n"
                             "4. Select payment method (Cash/Card/Mobile/Gift Card)\n"
                             "5. Add tip if desired\n6. Complete — receipt is sent automatically"},
                {"clients", "Client management:\n- Search: use the search bar or press '/'\n"
                            "- New client: click + in the Clients section\n"
                            "- Profile: click any client to see history, preferences, loyalty points\n"
                            "- Import: go to Clients → Import to bulk-upload from CSV"},
                {"reports", "Available reports:\n- Daily Summary: end-of-day overview\n"
                            "- Revenue: breakdown by service, product, staff\n"
                            "- Tips & Commissions: per-stylist payouts\n"
                            "- Export: CSV or PDF for your accountant"},
                {"inventory", "Inventory management:\n- Add products in Settings → Products\n"
                              "- Stock is auto-decremented on sale\n"
                              "- Low-stock alerts appear on the dashboard\n"
                              "- Purchase orders track supplier orders"},
                {"staff", "Staff management:\n- Add staff in Staff → Add Staff\n"
                          "- Set roles: Owner, Manager, Stylist, Receptionist\n"
                          "- Schedules: set working hours per staff member\n"
                          "- Commissions: configure per-service or per-product rates"},
                {"settings", "Salon settings include:\n- Profile: name, address, logo, contact\n"
                             "- Services: menu, pricing, durations\n- Opening Hours: per-day schedule\n"
                             "- Payments: accepted methods, terminal setup\n- Tax: rates and invoice settings"},
                {"online_booking", "Online booking lets clients book 24/7:\n"
                                   "1. Enable in Settings → Online Booking\n"
                                   "2. Share your booking link or embed on your website\n"
                                   "3. Clients select service, staff, date, time\n"
                                   "4. Bookings appear instantly on your calendar\n"
                                   "5. Clients get email/SMS confirmation"}
            };

            auto it = guides.find(feature);
            if (it != guides.end()) {
                help["guide"] = it->second;
            } else {
                help["guide"] = "I can help with: booking, checkout, clients, reports, "
                                "inventory, staff, settings, and online_booking. "
                                "Which would you like to learn about?";
            }
            return help;
        }
    });
}

} // namespace Ai::Tools
