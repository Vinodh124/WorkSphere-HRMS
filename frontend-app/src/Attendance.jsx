
import { useEffect, useState } from "react";
import api from "./api/api";
import {
  Clock3,
  CalendarDays,
  RefreshCw,
  Search,
  Download,
} from "lucide-react";



function localDateString() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatTime(value) {
  if (!value) return "—";

  return new Date(value).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatHours(value) {
  if (value == null) return "—";
  return `${Number(value).toFixed(2)} hrs`;
}

export default function Attendance({ onAttendanceChange }) {
  const [employees, setEmployees] = useState([]);
  const [records, setRecords] = useState([]);
  const [selectedDate, setSelectedDate] = useState(localDateString());
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [busyEmployee, setBusyEmployee] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const isToday = selectedDate === localDateString();

  async function loadData() {
    setLoading(true);
    setError("");

    try {
      const [employeeResponse, attendanceResponse] = await Promise.all([
        api.get("/employees/"),
        api.get("/attendance/", {
          params: { attendance_date: selectedDate },
        }),
      ]);

      setEmployees(employeeResponse.data);
      setRecords(attendanceResponse.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load attendance. Check that the backend is running."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [selectedDate]);

  async function runAction(employee, action) {
    setBusyEmployee(employee.id);
    setError("");
    setNotice("");

    try {
      if (action === "check-in") {
        await api.post("/attendance/check-in", {
          employee_id: employee.id,
        });
        setNotice(`Checked in ${employee.full_name}.`);
      } else if (action === "check-out") {
        const record = records.find(
          (item) => item.employee_id === employee.id
        );

        if (!record) {
          throw new Error("Attendance record not found. Refresh and try again.");
        }

        await api.post(`/attendance/${record.id}/check-out`);
        setNotice(`Checked out ${employee.full_name}.`);
      } else {
        await api.post("/attendance/mark-status", {
          employee_id: employee.id,
          attendance_date: selectedDate,
          status: action,
        });
        setNotice(
          `${employee.full_name}: ${action.replace("_", " ")}.`
        );
      }

      await loadData();

      if (onAttendanceChange) {
        await onAttendanceChange();
      }
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : err.message || "The attendance action failed. Please try again."
      );
    } finally {
      setBusyEmployee(null);
    }
  }

  const recordByEmployee = new Map(
    records.map((record) => [record.employee_id, record])
  );

  const filteredEmployees = employees.filter((employee) => {
    const record = recordByEmployee.get(employee.id);
    const status = record?.status || "NOT MARKED";
    const search = searchTerm.trim().toLowerCase();

    const matchesSearch =
      String(employee.full_name || "").toLowerCase().includes(search) ||
      String(employee.employee_code || "").toLowerCase().includes(search) ||
      String(employee.department || "").toLowerCase().includes(search);

    const matchesStatus =
      statusFilter === "ALL" || status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const presentCount = records.filter(
    (record) => record.status === "PRESENT"
  ).length;

  const absentCount = records.filter(
    (record) => record.status === "ABSENT"
  ).length;

  const halfDayCount = records.filter(
    (record) => record.status === "HALF_DAY"
  ).length;

  function exportAttendance() {
    const escapeCsv = (value) =>
      `"${String(value ?? "").replace(/"/g, '""')}"`;

    const rows = [
      [
        "Employee Code",
        "Employee Name",
        "Department",
        "Date",
        "Check In",
        "Check Out",
        "Working Hours",
        "Status",
      ],
      ...filteredEmployees.map((employee) => {
        const record = recordByEmployee.get(employee.id);

        return [
          employee.employee_code,
          employee.full_name,
          employee.department,
          selectedDate,
          record?.check_in ? formatTime(record.check_in) : "",
          record?.check_out ? formatTime(record.check_out) : "",
          record?.working_hours ?? "",
          record?.status || "NOT MARKED",
        ];
      }),
    ];

    const csv = rows
      .map((row) => row.map(escapeCsv).join(","))
      .join("\r\n");

    const blob = new Blob(["\uFEFF" + csv], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = `attendance-${selectedDate}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="attendance-section">
      <div className="attendance-heading">
        <div>
          <p className="attendance-eyebrow">PEOPLE OPERATIONS</p>
          <h2>
            <Clock3 size={24} /> Attendance Management
          </h2>
          <p className="attendance-subtitle">
            Manage daily attendance, working hours, and historical records.
          </p>
        </div>

        <button
          className="attendance-refresh"
          onClick={loadData}
          disabled={loading}
          title="Refresh attendance"
        >
          <RefreshCw size={17} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="attendance-alert error" role="alert">
          {error}
        </div>
      )}

      {notice && (
        <div className="attendance-alert success" role="status">
          {notice}
        </div>
      )}

      <div className="attendance-summary">
        <div>
          <span>Present</span>
          <strong>{presentCount}</strong>
        </div>
        <div>
          <span>Absent</span>
          <strong>{absentCount}</strong>
        </div>
        <div>
          <span>Half Day</span>
          <strong>{halfDayCount}</strong>
        </div>
        <div>
          <span>Employees</span>
          <strong>{employees.length}</strong>
        </div>
      </div>

      <div className="attendance-card">
        <div className="attendance-toolbar">
          <div>
            <h3>Attendance History</h3>
            <p>
              {isToday
                ? "Record check-ins and check-outs for today."
                : "Viewing attendance records for the selected date."}
            </p>
          </div>

          <label className="attendance-date">
            <CalendarDays size={17} />
            <input
              type="date"
              value={selectedDate}
              max={localDateString()}
              onChange={(event) => setSelectedDate(event.target.value)}
              aria-label="Select attendance date"
            />
          </label>
        </div>

        <div className="attendance-filters">
          <label className="attendance-search">
            <Search size={17} />
            <input
              type="search"
              placeholder="Search name, code, or department..."
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              aria-label="Search employees"
            />
          </label>

          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            aria-label="Filter by attendance status"
          >
            <option value="ALL">All statuses</option>
            <option value="PRESENT">Present</option>
            <option value="ABSENT">Absent</option>
            <option value="HALF_DAY">Half Day</option>
            <option value="NOT MARKED">Not Marked</option>
          </select>

          <button
            className="attendance-refresh"
            onClick={exportAttendance}
            disabled={loading || filteredEmployees.length === 0}
            title="Export filtered attendance to CSV"
          >
            <Download size={17} />
            Export CSV
          </button>
        </div>

        <div className="attendance-table-wrapper">
          <table className="attendance-table">
            <thead>
              <tr>
                <th>EMPLOYEE</th>
                <th>CHECK IN</th>
                <th>CHECK OUT</th>
                <th>WORKING HOURS</th>
                <th>STATUS</th>
                <th>ACTIONS</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className="attendance-empty">
                    Loading attendance...
                  </td>
                </tr>
              ) : filteredEmployees.length === 0 ? (
                <tr>
                  <td colSpan="6" className="attendance-empty">
                    No matching employees found for these filters.
                  </td>
                </tr>
              ) : (
                filteredEmployees.map((employee) => {
                  const record = recordByEmployee.get(employee.id);
                  const status = record?.status || "NOT MARKED";
                  const busy = busyEmployee === employee.id;

                  return (
                    <tr key={employee.id}>
                      <td>
                        <strong>{employee.full_name}</strong>
                        <span className="attendance-employee-code">
                          {employee.employee_code}
                        </span>
                      </td>

                      <td>{formatTime(record?.check_in)}</td>
                      <td>{formatTime(record?.check_out)}</td>
                      <td>{formatHours(record?.working_hours)}</td>

                      <td>
                        <span
                          className={`attendance-status ${status
                            .toLowerCase()
                            .replace(/\s+/g, "-")}`}
                        >
                          {status.replace("_", " ")}
                        </span>
                      </td>

                      <td>
                        <div className="attendance-actions">
                          {isToday && !record && (
                            <button
                              className="attendance-action primary"
                              disabled={busy}
                              onClick={() =>
                                runAction(employee, "check-in")
                              }
                            >
                              Check In
                            </button>
                          )}

                          {isToday &&
                            record?.check_in &&
                            !record?.check_out &&
                            record.status !== "ABSENT" && (
                              <button
                                className="attendance-action primary"
                                disabled={busy}
                                onClick={() =>
                                  runAction(employee, "check-out")
                                }
                              >
                                Check Out
                              </button>
                            )}

                          <button
                            className="attendance-action"
                            disabled={busy}
                            onClick={() => runAction(employee, "PRESENT")}
                          >
                            Present
                          </button>

                          <button
                            className="attendance-action"
                            disabled={busy}
                            onClick={() => runAction(employee, "HALF_DAY")}
                          >
                            Half Day
                          </button>

                          <button
                            className="attendance-action danger"
                            disabled={busy}
                            onClick={() => runAction(employee, "ABSENT")}
                          >
                            Absent
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {!loading && (
          <p className="attendance-subtitle">
            Showing {filteredEmployees.length} of {employees.length} employees
            for {selectedDate}.
          </p>
        )}
      </div>
    </section>
  );
}
