#pragma once
#include "../Tool.h"
#include <drogon/drogon.h>
#include <string>

namespace Ai::Tools {

inline void registerBookingTools() {
    auto& reg = ToolRegistry::instance();

    // Book an appointment
    reg.registerTool({
        "book_appointment",
        "Book an appointment for a client with a specific staff member at a given date and time",
        {
            {"client_name", "string", "Full name of the client", true},
            {"service_name", "string", "Service to book (e.g., 'Women\\'s Haircut', 'Balayage')", true},
            {"staff_name", "string", "Staff member name", true},
            {"date", "string", "Date in YYYY-MM-DD format", true},
            {"time", "string", "Time in HH:MM 24-hour format", true},
            {"notes", "string", "Optional notes for the appointment", false}
        },
        [](const Json::Value& args) -> Json::Value {
            auto db = drogon::app().getDbClient();
            auto clientName = args["client_name"].asString();
            auto serviceName = args["service_name"].asString();
            auto staffName = args["staff_name"].asString();
            auto date = args["date"].asString();
            auto time = args["time"].asString();
            auto notes = args.get("notes", "").asString();

            try {
                // Lookup or create client
                auto clientResult = db->execSqlSync(
                    "SELECT id FROM clients WHERE first_name || ' ' || last_name ILIKE $1",
                    "%" + clientName + "%");
                int clientId;
                if (clientResult.empty()) {
                    auto parts = drogon::utils::splitString(clientName, " ");
                    auto insert = db->execSqlSync(
                        "INSERT INTO clients (first_name, last_name) VALUES ($1, $2) RETURNING id",
                        parts.size() > 0 ? parts[0] : clientName,
                        parts.size() > 1 ? parts[1] : "");
                    clientId = insert[0]["id"].as<int>();
                } else {
                    clientId = clientResult[0]["id"].as<int>();
                }

                // Lookup service
                auto svcResult = db->execSqlSync(
                    "SELECT id, duration_minutes FROM services WHERE name ILIKE $1",
                    "%" + serviceName + "%");
                if (svcResult.empty()) {
                    Json::Value err;
                    err["error"] = "Service not found: " + serviceName;
                    err["suggestion"] = "Try checking the exact service name in Settings → Services";
                    return err;
                }
                int serviceId = svcResult[0]["id"].as<int>();
                int duration = svcResult[0]["duration_minutes"].as<int>();

                // Lookup staff
                auto staffResult = db->execSqlSync(
                    "SELECT id FROM staff WHERE name ILIKE $1", "%" + staffName + "%");
                if (staffResult.empty()) {
                    Json::Value err;
                    err["error"] = "Staff member not found: " + staffName;
                    return err;
                }
                int staffId = staffResult[0]["id"].as<int>();

                // Build timestamp
                std::string startTime = date + " " + time + ":00";

                // Insert appointment
                auto insert = db->execSqlSync(
                    "INSERT INTO appointments (client_id, service_id, staff_id, start_time, "
                    "end_time, status, notes, created_at) "
                    "VALUES ($1, $2, $3, $4::timestamp, $4::timestamp + interval '1 minute' * $5, "
                    "'booked', $6, NOW()) RETURNING id",
                    clientId, serviceId, staffId, startTime, duration, notes);

                Json::Value response;
                response["success"] = true;
                response["appointment_id"] = insert[0]["id"].as<int>();
                response["message"] = "Booked " + clientName + " for " + serviceName +
                                      " with " + staffName + " on " + date + " at " + time;
                response["duration_minutes"] = duration;
                return response;
            } catch (const std::exception& e) {
                Json::Value err;
                err["error"] = std::string("Booking failed: ") + e.what();
                return err;
            }
        }
    });
}

} // namespace Ai::Tools
