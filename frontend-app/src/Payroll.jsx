
import { useCallback, useEffect, useState } from "react";
import { RefreshCw, Wallet, PlusCircle } from "lucide-react";
import api from "./api/api";

function Payroll() {
  const [payrollRecords, setPayrollRecords] = useState([]);
  const [month, setMonth] = useState(
    new Date().toISOString().slice(0, 7)
  );
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [form, setForm] = useState({
    employee_id: "",
    basic_salary: "",
    bonus: "0",
    deductions: "0",
    month: new Date().toISOString().slice(0, 7),
  });

  const loadPayroll = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/payroll/", {
        params: month ? { month } : {},
      });

      setPayrollRecords(
        Array.isArray(response.data) ? response.data : []
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load payroll. Check your login and permissions."
      );
      setPayrollRecords([]);
    } finally {
      setLoading(false);
    }
  }, [month]);

  useEffect(() => {
    loadPayroll();
  }, [loadPayroll]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
    setError("");
    setMessage("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");

    const employeeId = Number(form.employee_id);
    const basicSalary = Number(form.basic_salary);
    const bonus = Number(form.bonus);
    const deductions = Number(form.deductions);

    if (!Number.isInteger(employeeId) || employeeId <= 0) {
      setError("Enter a valid Employee ID.");
      return;
    }

    if (
      !form.month ||
      !Number.isFinite(basicSalary) ||
      basicSalary < 0 ||
      !Number.isFinite(bonus) ||
      bonus < 0 ||
      !Number.isFinite(deductions) ||
      deductions < 0
    ) {
      setError("Enter a valid month and non-negative salary amounts.");
      return;
    }

    if (deductions > basicSalary + bonus) {
      setError("Deductions cannot exceed salary plus bonus.");
      return;
    }

    setSaving(true);

    try {
      const response = await api.post("/payroll/", {
        employee_id: employeeId,
        basic_salary: basicSalary,
        bonus,
        deductions,
        month: form.month,
      });

      setMessage(
        `Payroll created successfully. Net salary: ₹${Number(
          response.data.net_salary
        ).toLocaleString("en-IN", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })}`
      );

      setMonth(form.month);
      setForm((previous) => ({
        ...previous,
        employee_id: "",
        basic_salary: "",
        bonus: "0",
        deductions: "0",
      }));

      const updated = await api.get("/payroll/", {
        params: { month: form.month },
      });

      setPayrollRecords(
        Array.isArray(updated.data) ? updated.data : []
      );
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
          ? detail.map((item) => item.msg).join(", ")
          : "Unable to create payroll. Check the employee ID and your HR/Admin permissions."
      );
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (amount) =>
    new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(Number(amount) || 0);

  const totalNetSalary = payrollRecords.reduce(
    (total, record) => total + Number(record.net_salary || 0),
    0
  );

  const inputStyle = {
    width: "100%",
    boxSizing: "border-box",
    padding: "10px 12px",
    border: "1px solid #d1d5db",
    borderRadius: 8,
    marginTop: 6,
  };

  const labelStyle = {
    display: "block",
    fontWeight: 500,
    marginBottom: 12,
  };

  return (
    <section style={{ padding: "8px 0 24px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 16,
          marginBottom: 24,
        }}
      >
        <div>
          <h2 style={{ margin: "0 0 8px" }}>
            <Wallet
              size={23}
              style={{ verticalAlign: "middle", marginRight: 8 }}
            />
            Payroll Management
          </h2>

          <p style={{ margin: 0, color: "#64748b" }}>
            Generate payroll and review employee salary records.
          </p>
        </div>

        <button
          type="button"
          onClick={loadPayroll}
          disabled={loading}
          style={{
            padding: "10px 16px",
            border: "1px solid #d1d5db",
            borderRadius: 8,
            background: "#ffffff",
            cursor: loading ? "wait" : "pointer",
          }}
        >
          <RefreshCw
            size={15}
            style={{ verticalAlign: "middle", marginRight: 6 }}
          />
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      <div
        style={{
          padding: 20,
          border: "1px solid #e5e7eb",
          borderRadius: 12,
          marginBottom: 24,
          background: "#ffffff",
        }}
      >
        <h3 style={{ marginTop: 0 }}>
          <PlusCircle
            size={19}
            style={{ verticalAlign: "middle", marginRight: 8 }}
          />
          Generate Payroll
        </h3>

        <form onSubmit={handleSubmit}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(200px, 1fr))",
              gap: 16,
            }}
          >
            <label style={labelStyle}>
              Employee ID
              <input
                style={inputStyle}
                type="number"
                name="employee_id"
                min="1"
                step="1"
                value={form.employee_id}
                onChange={handleChange}
                placeholder="Enter employee ID"
                required
              />
            </label>

            <label style={labelStyle}>
              Payroll Month
              <input
                style={inputStyle}
                type="month"
                name="month"
                value={form.month}
                onChange={handleChange}
                required
              />
            </label>

            <label style={labelStyle}>
              Basic Salary (₹)
              <input
                style={inputStyle}
                type="number"
                name="basic_salary"
                min="0"
                step="0.01"
                value={form.basic_salary}
                onChange={handleChange}
                placeholder="30000"
                required
              />
            </label>

            <label style={labelStyle}>
              Bonus (₹)
              <input
                style={inputStyle}
                type="number"
                name="bonus"
                min="0"
                step="0.01"
                value={form.bonus}
                onChange={handleChange}
                required
              />
            </label>

            <label style={labelStyle}>
              Deductions (₹)
              <input
                style={inputStyle}
                type="number"
                name="deductions"
                min="0"
                step="0.01"
                value={form.deductions}
                onChange={handleChange}
                required
              />
            </label>
          </div>

          {error && (
            <p
              role="alert"
              style={{ color: "#b91c1c", marginBottom: 12 }}
            >
              {error}
            </p>
          )}

          {message && (
            <p
              role="status"
              style={{ color: "#15803d", marginBottom: 12 }}
            >
              {message}
            </p>
          )}

          <button
            type="submit"
            disabled={saving}
            style={{
              padding: "11px 18px",
              border: "none",
              borderRadius: 8,
              background: "#2563eb",
              color: "#ffffff",
              fontWeight: 600,
              cursor: saving ? "wait" : "pointer",
            }}
          >
            {saving ? "Generating..." : "Generate Payroll"}
          </button>
        </form>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 12,
          marginBottom: 20,
        }}
      >
        <label htmlFor="payroll-month">Filter month:</label>

        <input
          id="payroll-month"
          type="month"
          value={month}
          onChange={(event) => setMonth(event.target.value)}
          style={{
            padding: "9px 12px",
            border: "1px solid #d1d5db",
            borderRadius: 8,
          }}
        />

        <button
          type="button"
          onClick={() => setMonth("")}
          style={{
            padding: "9px 12px",
            border: "1px solid #d1d5db",
            borderRadius: 8,
            background: "#ffffff",
            cursor: "pointer",
          }}
        >
          All months
        </button>
      </div>

      <div
        style={{
          padding: 20,
          border: "1px solid #e5e7eb",
          borderRadius: 12,
          marginBottom: 22,
          background: "#ffffff",
        }}
      >
        <p style={{ margin: "0 0 8px", color: "#64748b" }}>
          Total net payroll
        </p>

        <h2 style={{ margin: 0 }}>
          {formatCurrency(totalNetSalary)}
        </h2>

        <p style={{ margin: "8px 0 0", color: "#64748b" }}>
          {payrollRecords.length} payroll record(s)
        </p>
      </div>

      {error && (
        <p
          role="alert"
          style={{
            padding: 12,
            borderRadius: 8,
            background: "#fef2f2",
            color: "#b91c1c",
          }}
        >
          {error}
        </p>
      )}

      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            background: "#ffffff",
          }}
        >
          <thead>
            <tr style={{ background: "#f8fafc", textAlign: "left" }}>
              {[
                "Employee ID",
                "Employee Name",
                "Month",
                "Basic Salary",
                "Bonus",
                "Deductions",
                "Net Salary",
                "Created At",
              ].map((heading) => (
                <th
                  key={heading}
                  style={{
                    padding: 13,
                    borderBottom: "1px solid #e5e7eb",
                    whiteSpace: "nowrap",
                  }}
                >
                  {heading}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {!loading &&
              !error &&
              payrollRecords.map((record) => (
                <tr key={record.id}>
                  <td style={cellStyle}>{record.employee_id}</td>

                  <td style={cellStyle}>
                    {record.employee_name || "—"}
                  </td>

                  <td style={cellStyle}>{record.month}</td>

                  <td style={cellStyle}>
                    {formatCurrency(record.basic_salary)}
                  </td>

                  <td style={cellStyle}>
                    {formatCurrency(record.bonus)}
                  </td>

                  <td style={cellStyle}>
                    {formatCurrency(record.deductions)}
                  </td>

                  <td style={{ ...cellStyle, fontWeight: 600 }}>
                    {formatCurrency(record.net_salary)}
                  </td>

                  <td style={cellStyle}>
                    {record.created_at
                      ? new Date(
                          record.created_at
                        ).toLocaleDateString("en-IN")
                      : "—"}
                  </td>
                </tr>
              ))}

            {!loading && !error && payrollRecords.length === 0 && (
              <tr>
                <td
                  colSpan={8}
                  style={{
                    padding: 24,
                    textAlign: "center",
                    color: "#64748b",
                  }}
                >
                  No payroll records found for this month.
                </td>
              </tr>
            )}

            {loading && (
              <tr>
                <td
                  colSpan={8}
                  style={{
                    padding: 24,
                    textAlign: "center",
                  }}
                >
                  Loading payroll records...
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

const cellStyle = {
  padding: 13,
  borderBottom: "1px solid #e5e7eb",
  whiteSpace: "nowrap",
};

export default Payroll;
