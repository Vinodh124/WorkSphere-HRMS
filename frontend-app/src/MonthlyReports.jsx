
import { useEffect, useMemo, useState } from "react";
import api from "./api/api";
import {
  CalendarDays,
  Download,
  RefreshCw,
  Search,
  Users,
  UserCheck,
  UserX,
  Clock3,
} from "lucide-react";


export default function MonthlyReports() {
  const currentDate = new Date();

  const [year, setYear] = useState(currentDate.getFullYear());
  const [month, setMonth] = useState(currentDate.getMonth() + 1);
  const [search, setSearch] = useState("");
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadReport() {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/attendance/monthly-report", {
        params: { year, month },
      });

      setReportData(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load monthly report. Check the backend."
      );
      setReportData(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReport();
  }, [year, month]);

  const report = reportData?.report || [];

  const filteredReport = useMemo(() => {
    const term = search.trim().toLowerCase();

    return report.filter((employee) =>
      [
        employee.employee_name,
        employee.employee_code,
        employee.department,
        employee.designation,
      ].some((value) =>
        String(value || "").toLowerCase().includes(term)
      )
    );
  }, [report, search]);

  const totals = useMemo(
    () =>
      report.reduce(
        (result, employee) => ({
          present: result.present + employee.present_days,
          absent: result.absent + employee.absent_days,
          halfDay: result.halfDay + employee.half_days,
          hours: result.hours + employee.total_working_hours,
        }),
        { present: 0, absent: 0, halfDay: 0, hours: 0 }
      ),
    [report]
  );

  function exportCsv() {
    const escapeCsv = (value) =>
      `"${String(value ?? "").replace(/"/g, '""')}"`;

    const rows = [
      [
        "Employee Code",
        "Employee Name",
        "Department",
        "Designation",
        "Present Days",
        "Absent Days",
        "Half Days",
        "Days Recorded",
        "Total Working Hours",
      ],
      ...filteredReport.map((employee) => [
        employee.employee_code,
        employee.employee_name,
        employee.department,
        employee.designation,
        employee.present_days,
        employee.absent_days,
        employee.half_days,
        employee.days_recorded,
        employee.total_working_hours,
      ]),
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
    link.download = `monthly-attendance-${year}-${String(month).padStart(2, "0")}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="attendance-section">
      <div className="attendance-heading">
        <div>
          <p className="attendance-eyebrow">PEOPLE ANALYTICS</p>
          <h2>
            <CalendarDays size={24} />
            Monthly Attendance Reports
          </h2>
          <p className="attendance-subtitle">
            Review employee attendance and working hours by month.
          </p>
        </div>

        <button
          className="attendance-refresh"
          onClick={loadReport}
          disabled={loading}
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

      <div className="attendance-card" style={{ padding: 18, marginBottom: 20 }}>
        <div className="attendance-toolbar">
          <div>
            <h3>Report Period</h3>
            <p>Select the month and year to view attendance totals.</p>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <select
              value={month}
              onChange={(event) => setMonth(Number(event.target.value))}
              aria-label="Report month"
            >
              {Array.from({ length: 12 }, (_, index) => (
                <option key={index + 1} value={index + 1}>
                  {new Date(2000, index, 1).toLocaleString("en-IN", {
                    month: "long",
                  })}
                </option>
              ))}
            </select>

            <select
              value={year}
              onChange={(event) => setYear(Number(event.target.value))}
              aria-label="Report year"
            >
              {Array.from({ length: 11 }, (_, index) => {
                const value = currentDate.getFullYear() - 5 + index;
                return (
                  <option key={value} value={value}>
                    {value}
                  </option>
                );
              })}
            </select>
          </div>
        </div>
      </div>

      <div className="attendance-summary">
        <div>
          <Users size={19} />
          <span>Employees</span>
          <strong>{reportData?.total_employees ?? 0}</strong>
        </div>
        <div>
          <UserCheck size={19} />
          <span>Present Days</span>
          <strong>{totals.present}</strong>
        </div>
        <div>
          <UserX size={19} />
          <span>Absent Days</span>
          <strong>{totals.absent}</strong>
        </div>
        <div>
          <Clock3 size={19} />
          <span>Working Hours</span>
          <strong>{totals.hours.toFixed(2)}</strong>
        </div>
      </div>

      <div className="attendance-card">
        <div className="attendance-toolbar">
          <div>
            <h3>
              {reportData?.month_name || "Monthly"} {year} Report
            </h3>
            <p>
              Present, absent, half-day, and recorded attendance totals.
            </p>
          </div>

          <button
            className="attendance-refresh"
            onClick={exportCsv}
            disabled={loading || filteredReport.length === 0}
          >
            <Download size={17} />
            Export CSV
          </button>
        </div>

        <div className="attendance-filters">
          <label className="attendance-search">
            <Search size={17} />
            <input
              type="search"
              placeholder="Search employee or department..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
        </div>

        <div className="attendance-table-wrapper">
          <table className="attendance-table">
            <thead>
              <tr>
                <th>EMPLOYEE</th>
                <th>DEPARTMENT</th>
                <th>PRESENT</th>
                <th>ABSENT</th>
                <th>HALF DAY</th>
                <th>DAYS RECORDED</th>
                <th>WORKING HOURS</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" className="attendance-empty">
                    Loading monthly report...
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan="7" className="attendance-empty">
                    Report could not be loaded.
                  </td>
                </tr>
              ) : filteredReport.length === 0 ? (
                <tr>
                  <td colSpan="7" className="attendance-empty">
                    No employees match your search.
                  </td>
                </tr>
              ) : (
                filteredReport.map((employee) => (
                  <tr key={employee.employee_id}>
                    <td>
                      <strong>{employee.employee_name}</strong>
                      <span className="attendance-employee-code">
                        {employee.employee_code}
                      </span>
                    </td>
                    <td>{employee.department || "—"}</td>
                    <td>{employee.present_days}</td>
                    <td>{employee.absent_days}</td>
                    <td>{employee.half_days}</td>
                    <td>{employee.days_recorded}</td>
                    <td>
                      {Number(employee.total_working_hours).toFixed(2)} hrs
                    </td>
                  </tr>
                ))
              )}
            </tbody>

            {!loading && !error && filteredReport.length > 0 && (
              <tfoot>
                <tr>
                  <th colSpan="2">Filtered totals</th>
                  <th>
                    {filteredReport.reduce(
                      (sum, item) => sum + item.present_days,
                      0
                    )}
                  </th>
                  <th>
                    {filteredReport.reduce(
                      (sum, item) => sum + item.absent_days,
                      0
                    )}
                  </th>
                  <th>
                    {filteredReport.reduce(
                      (sum, item) => sum + item.half_days,
                      0
                    )}
                  </th>
                  <th>
                    {filteredReport.reduce(
                      (sum, item) => sum + item.days_recorded,
                      0
                    )}
                  </th>
                  <th>
                    {filteredReport
                      .reduce(
                        (sum, item) =>
                          sum + Number(item.total_working_hours || 0),
                        0
                      )
                      .toFixed(2)}{" "}
                    hrs
                  </th>
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      </div>
    </section>
  );
}
