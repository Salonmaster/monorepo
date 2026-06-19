#pragma once
#include "../Tool.h"
#include <drogon/drogon.h>

namespace Ai::Tools {

inline void registerClientTools() {
    auto& reg = ToolRegistry::instance();

    reg.registerTool({
        "lookup_client",
        "Find a client by name, email, or phone. Returns profile, history, and preferences.",
        {
            {"query", "string", "Name, email, or phone number to search for", true}
        },
        [](const Json::Value& args) -> Json::Value {
            auto db = drogon::app().getDbClient();
            auto q = "%" + args["query"].asString() + "%";

            try {
                auto result = db->execSqlSync(
                    "SELECT c.id, c.first_name, c.last_name, c.email, c.phone, "
                    "c.total_visits, c.total_spent, c.loyalty_points, c.notes, "
                    "c.last_visit, c.preferences "
                    "FROM clients c "
                    "WHERE c.first_name || ' ' || c.last_name ILIKE $1 "
                    "   OR c.email ILIKE $1 OR c.phone ILIKE $1 "
                    "ORDER BY c.total_visits DESC LIMIT 5",
                    q);

                Json::Value clients(Json::arrayValue);
                for (const auto& row : result) {
                    Json::Value c;
                    c["id"] = row["id"].as<int>();
                    c["name"] = row["first_name"].asString() + " " + row["last_name"].asString();
                    c["email"] = row["email"].asString();
                    c["phone"] = row["phone"].isNull() ? "" : row["phone"].asString();
                    c["visits"] = row["total_visits"].as<int>();
                    c["total_spent"] = row["total_spent"].as<double>();
                    c["loyalty_points"] = row["loyalty_points"].as<int>();
                    c["last_visit"] = row["last_visit"].isNull() ? "never" : row["last_visit"].asString();
                    c["notes"] = row["notes"].isNull() ? "" : row["notes"].asString();
                    clients.append(c);
                }

                Json::Value response;
                response["clients"] = clients;
                response["found"] = static_cast<int>(clients.size());
                return response;
            } catch (const std::exception& e) {
                Json::Value err;
                err["error"] = std::string("Lookup failed: ") + e.what();
                return err;
            }
        }
    });

    reg.registerTool({
        "get_staff_schedule",
        "Get a staff member's schedule for today or a specific date",
        {
            {"staff_name", "string", "Staff member name (or 'all' for everyone)", true},
            {"date", "string", "Date in YYYY-MM-DD format (defaults to today)", false}
        },
        [](const Json::Value& args) -> Json::Value {
            auto db = drogon::app().getDbClient();
            auto staffName = args["staff_name"].asString();
            auto date = args.get("date", "CURRENT_DATE").asString();

            std::string query =
                "SELECT st.name as staff, s.name as service, "
                "c.first_name || ' ' || c.last_name as client, "
                "a.start_time, a.end_time, a.status "
                "FROM appointments a "
                "JOIN staff st ON a.staff_id = st.id "
                "JOIN services s ON a.service_id = s.id "
                "JOIN clients c ON a.client_id = c.id "
                "WHERE a.start_time::date = $1::date";
            if (staffName != "all") {
                query += " AND st.name ILIKE $2";
            }
            query += " ORDER BY st.name, a.start_time";

            try {
                drogon::orm::Result result;
                if (staffName != "all") {
                    result = db->execSqlSync(query, date, "%" + staffName + "%");
                } else {
                    result = db->execSqlSync(query, date);
                }

                Json::Value schedule(Json::arrayValue);
                for (const auto& row : result) {
                    Json::Value slot;
                    slot["staff"] = row["staff"].asString();
                    slot["service"] = row["service"].asString();
                    slot["client"] = row["client"].asString();
                    slot["start"] = row["start_time"].asString();
                    slot["end"] = row["end_time"].asString();
                    slot["status"] = row["status"].asString();
                    schedule.append(slot);
                }

                Json::Value response;
                response["schedule"] = schedule;
                response["count"] = static_cast<int>(schedule.size());
                response["date"] = date;
                return response;
            } catch (const std::exception& e) {
                Json::Value err;
                err["error"] = std::string("Schedule query failed: ") + e.what();
                return err;
            }
        }
    });
}

} // namespace Ai::Tools
