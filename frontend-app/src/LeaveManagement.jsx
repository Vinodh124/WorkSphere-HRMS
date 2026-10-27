
import { useCallback, useEffect, useState } from "react";
import {
  CalendarDays,
  RefreshCw,
  CheckCircle,
  XCircle,
  Send,
} from "lucide-react";
import api from "./api/api";

const initialForm = {
  leave_type: "CASUAL",
  start_date: "",
  end_date: "",
  reason: "",
};

function LeaveManagement({ user }) {
  const [leaves, setLeaves] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const role = String(user?.role || "").toUpperCase();
  const canReview = ["HR", "ADMIN"].includes(role);

  const loadLeaves = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/leaves/");
      setLeaves(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not load leave requests. Please check your login and backend."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLeaves();
  }, [loadLeaves]);

  function updateForm(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  async function submitLeave(event) {
    event.preventDefault();
    setError("");
    setNotice("");

    if (form.end_date < form.start_date) {
      setError("End date cannot be earlier than start date.");
      return;
    }

    setSubmitting(true);

    try {
      await api.post("/leaves/", {
        employee_id: null,
        leave_type: form.leave_type,
        start_date: form.start_date,
        end_date: form.end_date,
        reason: form.reason.trim(),
      });

      setForm(initialForm);
      setNotice("Leave request submitted successfully.");
      await loadLeaves();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not submit your leave request."
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function reviewLeave(leaveId, status) {
    setError("");
    setNotice("");

    try {
      await api.patch(`/leaves/${leaveId}/review`, { status });
      setNotice(`Leave request #${leaveId} ${status.toLowerCase()}.`);
      await loadLeaves();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not review this leave request."
      );
    }
  }

  const inputStyle = {
    width: "100%",
    padding: "10px 12px",
    border: "1px solid #cbd5e1",
    borderRadius: "8px",
    boxSizing: "border-box",
    font: "inherit",
  };

  const buttonStyle = {
    display: "inline-flex",
    alignItems: "center",
    gap: "7px",
    padding: "9px 13px",
    border: "1px solid #cbd5e1",
    borderRadius: "8px",
    background: "#fff",
    cursor: "pointer",
    fontWeight: 600,
  };

  function statusColor(status) {
    if (status === "APPROVED") return "#15803d";
    if (status === "REJECTED") return "#b91c1c";
    return "#a16207";
  }

  return (
    <section style={{ display: "grid", gap: "24px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "12px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <h2 style={{ marginBottom: "6px" }}>Leave Management</h2>
          <p style={{ margin: 0, color: "#64748b" }}>
            Apply for leave and track request status.
          </p>
        </div>

        <button
          type="button"
          style={buttonStyle}
          onClick={loadLeaves}
          disabled={loading}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {error && (
        <p role="alert" style={{ color: "#b91c1c" }}>
          {String(error)}
        </p>
      )}

      {notice && (
        <p role="status" style={{ color: "#15803d" }}>
          {notice}
        </p>
      )}

      {!canReview && (
        <form
          onSubmit={submitLeave}
          style={{
            display: "grid",
            gap: "16px",
            padding: "20px",
            border: "1px solid #e2e8f0",
            borderRadius: "12px",
            background: "#fff",
          }}
        >
          <h3 style={{ margin: 0 }}>Apply for Leave</h3>

          <label>
            Leave type
            <select
              name="leave_type"
              value={form.leave_type}
              onChange={updateForm}
              style={inputStyle}
              required
            >
              <option value="CASUAL">Casual Leave</option>
              <option value="SICK">Sick Leave</option>
              <option value="PAID">Paid Leave</option>
            </select>
          </label>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "16px",
            }}
          >
            <label>
              Start date
              <input
                type="date"
                name="start_date"
                min={new Date().toLocaleDateString("en-CA")}
                value={form.start_date}
                onChange={updateForm}
                style={inputStyle}
                required
              />
            </label>

            <label>
              End date
              <input
                type="date"
                name="end_date"
                min={form.start_date || new Date().toLocaleDateString("en-CA")}
                value={form.end_date}
                onChange={updateForm}
                style={inputStyle}
                required
              />
            </label>
          </div>

          <label>
            Reason
            <textarea
              name="reason"
              value={form.reason}
              onChange={updateForm}
              minLength={3}
              maxLength={1000}
              rows={3}
              placeholder="Enter the reason for your leave"
              style={inputStyle}
              required
            />
          </label>

          <div>
            <button
              type="submit"
              style={{
                ...buttonStyle,
                background: "#1d4ed8",
                color: "#fff",
                borderColor: "#1d4ed8",
              }}
              disabled={submitting}
            >
              <Send size={16} />
              {submitting ? "Submitting..." : "Submit Leave Request"}
            </button>
          </div>
        </form>
      )}

      <div
        style={{
          padding: "20px",
          border: "1px solid #e2e8f0",
          borderRadius: "12px",
          background: "#fff",
        }}
      >
        <h3 style={{ marginTop: 0 }}>
          {canReview ? "All Leave Requests" : "My Leave Requests"}
        </h3>

        {loading ? (
          <p>Loading leave requests...</p>
        ) : leaves.length === 0 ? (
          <p>No leave requests found.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                textAlign: "left",
              }}
            >
              <thead>
                <tr>
                  {[
                    "Request",
                    ...(canReview ? ["Employee ID"] : []),
                    "Leave Type",
                    "Start Date",
                    "End Date",
                    "Reason",
                    "Status",
                    ...(canReview ? ["Actions"] : []),
                  ].map((heading) => (
                    <th
                      key={heading}
                      style={{
                        padding: "12px 10px",
                        borderBottom: "1px solid #e2e8f0",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {leaves.map((leave) => (
                  <tr key={leave.id}>
                    <td style={{ padding: "12px 10px" }}>#{leave.id}</td>

                    {canReview && (
                      <td style={{ padding: "12px 10px" }}>
                        {leave.employee_id}
                      </td>
                    )}

                    <td style={{ padding: "12px 10px" }}>
                      {leave.leave_type}
                    </td>
                    <td style={{ padding: "12px 10px", whiteSpace: "nowrap" }}>
                      {leave.start_date}
                    </td>
                    <td style={{ padding: "12px 10px", whiteSpace: "nowrap" }}>
                      {leave.end_date}
                    </td>
                    <td style={{ padding: "12px 10px" }}>{leave.reason}</td>
                    <td
                      style={{
                        padding: "12px 10px",
                        color: statusColor(leave.status),
                        fontWeight: 700,
                      }}
                    >
                      {leave.status}
                    </td>

                    {canReview && (
                      <td style={{ padding: "12px 10px" }}>
                        {leave.status === "PENDING" ? (
                          <div
                            style={{
                              display: "flex",
                              gap: "8px",
                              flexWrap: "wrap",
                            }}
                          >
                            <button
                              type="button"
                              style={{
                                ...buttonStyle,
                                color: "#15803d",
                              }}
                              onClick={() =>
                                reviewLeave(leave.id, "APPROVED")
                              }
                            >
                              <CheckCircle size={15} />
                              Approve
                            </button>

                            <button
                              type="button"
                              style={{
                                ...buttonStyle,
                                color: "#b91c1c",
                              }}
                              onClick={() =>
                                reviewLeave(leave.id, "REJECTED")
                              }
                            >
                              <XCircle size={15} />
                              Reject
                            </button>
                          </div>
                        ) : (
                          "Reviewed"
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <p style={{ color: "#64748b", fontSize: "13px" }}>
        <CalendarDays
          size={15}
          style={{ verticalAlign: "middle", marginRight: "6px" }}
        />
        Leave records and approvals are loaded from the backend.
      </p>
    </section>
  );
}

export default LeaveManagement;
