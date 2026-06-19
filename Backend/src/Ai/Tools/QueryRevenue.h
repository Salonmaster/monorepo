#pragma once
#include "../Tool.h"
#include "../../Application/Globals.h"
#include <drogon/drogon.h>
#include <chrono>
#include <ctime>
#include <iomanip>
#include <sstream>

namespace Ai::Tools {

inline void registerRevenueTools() {
    auto& reg = ToolRegistry::instance();

    // Query revenue for today
    reg.registerTool({
        "query_revenue",
        "Get revenue for today or a specific date range",
        {
            {"period", "string", "One of: today, yesterday, this_week, last_week, this_month, last_month", true},
            {"staff_name", "string", "Optional — filter by staff member name", false}
        },
        [](const Json::Value& args) -> Json::Value {
            auto period = args.get("period", "today").asString();
            auto db = drogon::app().getDbClient();

            std::string dateFilter;
            if (period == "today") dateFilter = "CURRENT_DATE";
            else if (period == "yesterday") dateFilter = "CURRENT_DATE - 1";
            else if (period == "this_week") dateFilter = "date_trunc('week', CURRENT_DATE)";
            else if (period == "last_week") dateFilter = "date_trunc('week', CURRENT_DATE - 7)";
            else if (period == "this_month") dateFilter = "date_trunc('month', CURRENT_DATE)";
            else if (period == "last_month") dateFilter = "date_trunc('month', CURRENT_DATE) - interval '1 month'";
            else dateFilter = "CURRENT_DATE";

            std::string query = "SELECT COALESCE(SUM(total_amount), 0) as total, "
                                "COALESCE(SUM(tip_amount), 0) as tips, "
                                "COUNT(*) as transactions "
                                "FROM transactions WHERE created_at >= " + dateFilter;

            if (args.isMember("staff_name")) {
                query += " AND staff_name = $2";
            }

            try {
                auto result = db->execSqlSync(query);
                Json::Value response;
                response["revenue"] = result[0]["total"].as<double>();
                response["tips"] = result[0]["tips"].as<double>();
                response["transactions"] = result[0]["transactions"].as<int>();
                response["period"] = period;
                return response;
            } catch (const std::exception& e) {
                Json::Value err;
                err["error"] = std::string("Query failed: ") + e.what();
                return err;
            }
        }
    });

    // Query today's appointments
    reg.registerTool({
        "query_appointments",
        "Get today's appointments with status",
        {
            {"staff_name", "string", "Optional — filter by staff member", false},
            {"status", "string", "Optional — booked, checked_in, in_service, completed", false}
        },
        [](const Json::Value& args) -> Json::Value {
            auto db = drogon::app().getDbClient();
            std::string query =
                "SELECT a.id, c.first_name || ' ' || c.last_name as client_name, "
                "s.name as service_name, st.name as staff_name, "
                "a.start_time, a.end_time, a.status, s.price "
                "FROM appointments a "
                "JOIN clients c ON a.client_id = c.id "
                "JOIN services s ON a.service_id = s.id "
                "JOIN staff st ON a.staff_id = st.id "
                "WHERE a.start_time::date = CURRENT_DATE "
                "ORDER BY a.start_time";

            try {
                auto result = db->execSqlSync(query);
                Json::Value appointments(Json::arrayValue);
                for (const auto& row : result) {
                    Json::Value appt;
                    appt["id"] = row["id"].as<int>();
                    appt["client"] = row["client_name"].asString();
                    appt["service"] = row["service_name"].asString();
                    appt["staff"] = row["staff_name"].asString();
                    appt["start"] = row["start_time"].asString();
                    appt["status"] = row["status"].asString();
                    appt["price"] = row["price"].as<double>();
                    appointments.append(appt);
                }
                Json::Value response;
                response["appointments"] = appointments;
                response["count"] = static_cast<int>(appointments.size());
                return response;
            } catch (const std::exception& e) {
                Json::Value err;
                err["error"] = std::string("Query failed: ") + e.what();
                return err;
            }
        }
    });
}

} // namespace Ai::Tools
