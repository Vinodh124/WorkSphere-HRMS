
import { useCallback, useEffect, useState } from "react";
import {
  Users,
  UserPlus,
  Search,
  RefreshCw,
  Pencil,
  Trash2,
  X,
  UserCheck,
  Clock3,
  UserX,
  CalendarCheck,
  CalendarDays,
  FileBarChart,
  Wallet,
  Bell,
} from "lucide-react";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

import api from "./api/api";
import Attendance from "./Attendance";
import MonthlyReports from "./MonthlyReports";
import LeaveManagement from "./LeaveManagement";
import Payroll from "./Payroll";
import "./App.css";

const emptyEmployee = {
  employee_code: "",
  full_name: "",
  email: "",
  department: "",
  designation: "",
  salary: "",
  status: "Active",
};

const emptyStats = {
  total_employees: 0,
  active_employees: 0,
  present_today: 0,
  absent_today: 0,
  half_day_today: 0,
  attendance_date: "",
  pending_leaves: 0,
  approved_leaves: 0,
  rejected_leaves: 0,
  payroll_total: 0,
  payroll_records_count: 0,
  payroll_month: "",
};

function Dashboard({ user }) {
  const [employees, setEmployees] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(emptyStats);
  const [activePage, setActivePage] = useState("employees");

  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [error, setError] = useState("");
  const [statsError, setStatsError] = useState("");
  const [search, setSearch] = useState("");

  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyEmployee);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [notificationError, setNotificationError] = useState("");

  const unreadCount = notifications.filter(
    (notification) => !notification.is_read
  ).length;

  const loadNotifications = useCallback(async () => {
    setNotificationsLoading(true);
    setNotificationError("");

    try {
      const response = await api.get("/notifications/");
      setNotifications(response.data);
    } catch (err) {
      setNotificationError(
        err.response?.data?.detail ||
          "Could not load notifications."
      );
    } finally {
      setNotificationsLoading(false);
    }
  }, []);

  async function toggleNotifications() {
    const willOpen = !showNotifications;
    setShowNotifications(willOpen);

    if (willOpen) {
      await loadNotifications();
    }
  }

  async function markNotificationRead(notificationId) {
    try {
      await api.patch(`/notifications/${notificationId}/read`);
      setNotifications((current) =>
        current.map((notification) =>
          notification.id === notificationId
            ? { ...notification, is_read: true }
            : notification
        )
      );
    } catch (err) {
      setNotificationError(
        err.response?.data?.detail ||
          "Could not mark the notification as read."
      );
    }
  }


  const loadEmployees = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/employees/");
      setEmployees(response.data);
    } catch (err) {
      setError(
        err.response?.status === 401
          ? "Your session has expired. Please log in again."
          : err.response?.status === 403
          ? "Your account does not have permission to view employee records."
          : err.response?.data?.detail ||
            "Could not load employees. Check that the backend is running."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDashboardStats = useCallback(async () => {
    setStatsLoading(true);
    setStatsError("");

    try {
      const response = await api.get("/dashboard/stats");

      setDashboardStats({
        ...emptyStats,
        ...response.data,
      });
    } catch (err) {
      setStatsError(
        err.response?.status === 401
          ? "Your session has expired. Please log in again."
          : err.response?.data?.detail ||
            "Dashboard statistics could not be loaded."
      );
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadEmployees();
    loadDashboardStats();
  }, [loadEmployees, loadDashboardStats]);

  async function refreshDashboard() {
    await Promise.all([
      loadEmployees(),
      loadDashboardStats(),
    ]);
  }

  const filteredEmployees = employees.filter((employee) => {
    const query = search.trim().toLowerCase();

    return (
      (employee.full_name || "").toLowerCase().includes(query) ||
      (employee.employee_code || "").toLowerCase().includes(query) ||
      (employee.email || "").toLowerCase().includes(query) ||
      (employee.department || "").toLowerCase().includes(query) ||
      (employee.designation || "").toLowerCase().includes(query)
    );
  });

  function openAddModal() {
    setEditingId(null);
    setForm({ ...emptyEmployee });
    setError("");
    setNotice("");
    setShowModal(true);
  }

  function openEditModal(employee) {
    setEditingId(employee.id);

    setForm({
      employee_code: employee.employee_code || "",
      full_name: employee.full_name || "",
      email: employee.email || "",
      department: employee.department || "",
      designation: employee.designation || "",
      salary: employee.salary ?? "",
      status: employee.status || "Active",
    });

    setError("");
    setNotice("");
    setShowModal(true);
  }

  function closeModal() {
    if (saving) return;

    setShowModal(false);
    setEditingId(null);
    setForm({ ...emptyEmployee });
  }

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setSaving(true);
    setError("");
    setNotice("");

    const payload = {
      ...form,
      employee_code: form.employee_code.trim(),
      full_name: form.full_name.trim(),
      email: form.email.trim(),
      department: form.department.trim(),
      designation: form.designation.trim(),
      salary: Number(form.salary),
    };

    try {
      if (editingId !== null) {
        await api.put(`/employees/${editingId}`, payload);
        setNotice("Employee updated successfully.");
      } else {
        await api.post("/employees/", payload);
        setNotice("Employee added successfully.");
      }

      setShowModal(false);
      setEditingId(null);
      setForm({ ...emptyEmployee });

      await refreshDashboard();
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(
        err.response?.status === 401
          ? "Your session has expired. Please log in again."
          : err.response?.status === 403
          ? "You do not have permission to manage employees."
          : typeof detail === "string"
          ? detail
          : "Could not save employee. Check the required fields and try again."
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(employee) {
    const confirmed = window.confirm(
      `Are you sure you want to delete ${employee.full_name}? This also deletes their attendance records.`
    );

    if (!confirmed) return;

    setError("");
    setNotice("");

    try {
      await api.delete(`/employees/${employee.id}`);
      setNotice("Employee deleted successfully.");
      await refreshDashboard();
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(
        err.response?.status === 401
          ? "Your session has expired. Please log in again."
          : err.response?.status === 403
          ? "You do not have permission to delete employees."
          : typeof detail === "string"
          ? detail
          : "Could not delete employee. Please try again."
      );
    }
  }

  const totalEmployees =
    dashboardStats.total_employees ?? employees.length;

  const activeEmployees = dashboardStats.active_employees;
  const presentToday = dashboardStats.present_today;
  const absentToday = dashboardStats.absent_today;
  const halfDayToday = dashboardStats.half_day_today;

  const pendingLeaves = dashboardStats.pending_leaves;
  const approvedLeaves = dashboardStats.approved_leaves;
  const rejectedLeaves = dashboardStats.rejected_leaves;

  const payrollTotal = Number(dashboardStats.payroll_total || 0);
  const payrollRecordsCount =
    dashboardStats.payroll_records_count || 0;

  const attendanceDate = dashboardStats.attendance_date
    ? new Date(
        `${dashboardStats.attendance_date}T00:00:00`
      ).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : new Date().toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });

  const payrollMonth = dashboardStats.payroll_month || "";

  const formattedPayrollMonth = payrollMonth
    ? new Date(`${payrollMonth}-01T00:00:00`).toLocaleDateString(
        "en-IN",
        {
          month: "long",
          year: "numeric",
        }
      )
    : "Current month";

  const formattedPayrollTotal = payrollTotal.toLocaleString("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  });

  const attendanceChartData = [
    { name: "Present", count: Number(presentToday || 0) },
    { name: "Absent", count: Number(absentToday || 0) },
    { name: "Half Day", count: Number(halfDayToday || 0) },
  ];

  const leaveChartData = [
    { name: "Pending", value: Number(pendingLeaves || 0) },
    { name: "Approved", value: Number(approvedLeaves || 0) },
    { name: "Rejected", value: Number(rejectedLeaves || 0) },
  ];

  const navigationItems = [
    { id: "employees", label: "Employees", icon: Users },
    { id: "attendance", label: "Attendance", icon: CalendarCheck },
    { id: "reports", label: "Monthly Reports", icon: FileBarChart },
    { id: "leaves", label: "Leave Management", icon: CalendarDays },
    { id: "payroll", label: "Payroll Management", icon: Wallet },
  ];

  const pageTitle =
    activePage === "employees"
      ? "Employee Dashboard"
      : activePage === "attendance"
      ? "Attendance Management"
      : activePage === "reports"
      ? "Monthly Attendance Reports"
      : activePage === "leaves"
      ? "Leave Management"
      : "Payroll Management";

  const pageDescription =
    activePage === "employees"
      ? "Manage employees and monitor your workforce."
      : activePage === "attendance"
      ? "Record and manage daily employee attendance."
      : activePage === "reports"
      ? "Review monthly attendance totals and working hours."
      : activePage === "leaves"
      ? "Apply for leave and manage leave requests."
      : "View employee salary details and payroll records.";

  return (
    <main className="dashboard">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            <Users size={23} />
          </div>
          <div>
            <h1>WorkSphere</h1>
            <p>HUMAN RESOURCE MANAGEMENT</p>
          </div>
        </div>

        
<div className="topbar-right">
  <div className="notification-wrapper">
    <button
      type="button"
      className="notification-bell"
      onClick={toggleNotifications}
      aria-label={`Notifications, ${unreadCount} unread`}
      aria-expanded={showNotifications}
    >
      <Bell size={21} />
      {unreadCount > 0 && (
        <span className="notification-count">
          {unreadCount > 99 ? "99+" : unreadCount}
        </span>
      )}
    </button>

    {showNotifications && (
      <div className="notification-panel">
        <div className="notification-panel-header">
          <strong>Notifications</strong>
          <button
            type="button"
            className="notification-close"
            onClick={() => setShowNotifications(false)}
            aria-label="Close notifications"
          >
            <X size={17} />
          </button>
        </div>

        {notificationsLoading ? (
          <p className="notification-empty">Loading notifications...</p>
        ) : notificationError ? (
          <p className="notification-error">{notificationError}</p>
        ) : notifications.length === 0 ? (
          <p className="notification-empty">
            You have no notifications.
          </p>
        ) : (
          <div className="notification-list">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`notification-item ${
                  notification.is_read ? "read" : "unread"
                }`}
              >
                <div className="notification-item-heading">
                  <strong>{notification.title}</strong>
                  {!notification.is_read && (
                    <span className="notification-unread-dot" />
                  )}
                </div>

                <p>{notification.message}</p>

                <div className="notification-item-footer">
                  <span>
                    {notification.created_at
                      ? new Date(notification.created_at).toLocaleString()
                      : ""}
                  </span>

                  {!notification.is_read && (
                    <button
                      type="button"
                      className="notification-mark-read"
                      onClick={() =>
                        markNotificationRead(notification.id)
                      }
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    )}
  </div>

  <span className="system-status">
    <span className="status-dot" />
    HRMS Dashboard
  </span>
</div>

      </header>

      <nav className="main-navigation" aria-label="Main navigation">
        {navigationItems.map((item) => {
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              type="button"
              className={`navigation-item ${
                activePage === item.id ? "active" : ""
              }`}
              onClick={() => {
                setActivePage(item.id);
                setError("");
                setStatsError("");
                setNotice("");
              }}
            >
              <Icon size={18} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <section className="welcome-section">
        <div>
          <p className="welcome-eyebrow">WORKSPACE OVERVIEW</p>
          <h2>{pageTitle}</h2>
          <p className="welcome-description">{pageDescription}</p>

          {(activePage === "employees" ||
            activePage === "attendance") && (
            <p className="welcome-description">
              Attendance date: {attendanceDate}
            </p>
          )}
        </div>

        {activePage === "employees" && (
          <button
            type="button"
            className="add-employee-btn"
            onClick={openAddModal}
          >
            <UserPlus size={17} />
            Add Employee
          </button>
        )}
      </section>

      {error && (
        <div className="app-alert error" role="alert">
          {error}
        </div>
      )}

      {notice && (
        <div className="app-alert success" role="status">
          {notice}
        </div>
      )}

      {activePage === "employees" && (
        <>
          <section className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon purple">
                <Users size={21} />
              </div>
              <div>
                <p>Total Employees</p>
                <h3>{statsLoading ? "..." : totalEmployees}</h3>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon green">
                <UserCheck size={21} />
              </div>
              <div>
                <p>Active Employees</p>
                <h3>{statsLoading ? "..." : activeEmployees}</h3>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon blue">
                <Clock3 size={21} />
              </div>
              <div>
                <p>Present Today</p>
                <h3>{statsLoading ? "..." : presentToday}</h3>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon orange">
                <UserX size={21} />
              </div>
              <div>
                <p>Absent Today</p>
                <h3>{statsLoading ? "..." : absentToday}</h3>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon blue">
                <CalendarCheck size={21} />
              </div>
              <div>
                <p>Half Day Today</p>
                <h3>{statsLoading ? "..." : halfDayToday}</h3>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon orange">
                <CalendarDays size={21} />
              </div>
              <div>
                <p>Pending Leaves</p>
                <h3>{statsLoading ? "..." : pendingLeaves}</h3>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon green">
                <CalendarCheck size={21} />
              </div>
              <div>
                <p>Approved Leaves</p>
                <h3>{statsLoading ? "..." : approvedLeaves}</h3>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon purple">
                <Wallet size={21} />
              </div>
              <div>
                <p>Monthly Payroll</p>
                <h3>
                  {statsLoading ? "..." : formattedPayrollTotal}
                </h3>
                <small>
                  {statsLoading ? "Loading..." : formattedPayrollMonth}
                </small>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon blue">
                <Users size={21} />
              </div>
              <div>
                <p>Payroll Records</p>
                <h3>{statsLoading ? "..." : payrollRecordsCount}</h3>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon orange">
                <CalendarDays size={21} />
              </div>
              <div>
                <p>Rejected Leaves</p>
                <h3>{statsLoading ? "..." : rejectedLeaves}</h3>
              </div>
            </div>
          </section>

          {statsError && (
            <div className="app-alert error" role="alert">
              {statsError}{" "}
              <button
                type="button"
                onClick={loadDashboardStats}
                className="refresh-btn"
              >
                Retry
              </button>
            </div>
          )}

          <section className="analytics-grid">
            <div className="employee-panel analytics-panel">
              <div className="panel-heading">
                <div>
                  <h2>Attendance Overview</h2>
                  <p>Today's employee attendance</p>
                </div>
              </div>

              <div className="chart-container">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={attendanceChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Bar
                      dataKey="count"
                      name="Employees"
                      fill="#6366f1"
                      radius={[5, 5, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="employee-panel analytics-panel">
              <div className="panel-heading">
                <div>
                  <h2>Leave Status</h2>
                  <p>Leave request breakdown</p>
                </div>
              </div>

              <div className="chart-container">
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={leaveChartData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={85}
                      label
                    >
                      <Cell fill="#f59e0b" />
                      <Cell fill="#10b981" />
                      <Cell fill="#ef4444" />
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="employee-panel analytics-panel payroll-chart-panel">
              <div className="panel-heading">
                <div>
                  <h2>Payroll Summary</h2>
                  <p>{formattedPayrollMonth}</p>
                </div>
              </div>

              <div className="payroll-chart-summary">
                <span>Total payroll</span>
                <strong>
                  {statsLoading ? "..." : formattedPayrollTotal}
                </strong>
                <span>
                  {payrollRecordsCount} payroll records
                </span>
              </div>

              <div className="chart-container payroll-chart">
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart
                    data={[
                      {
                        name: "Monthly Payroll",
                        amount: payrollTotal,
                      },
                    ]}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip
                      formatter={(value) =>
                        Number(value).toLocaleString("en-IN", {
                          style: "currency",
                          currency: "INR",
                          maximumFractionDigits: 0,
                        })
                      }
                    />
                    <Bar
                      dataKey="amount"
                      name="Payroll"
                      fill="#10b981"
                      radius={[5, 5, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          <section className="employee-panel">
            <div className="panel-heading">
              <div>
                <h2>Employee Directory</h2>
                <p>View and manage your workforce.</p>
              </div>

              <button
                type="button"
                className="refresh-btn"
                onClick={refreshDashboard}
                disabled={loading || statsLoading}
                title="Refresh dashboard"
              >
                <RefreshCw size={16} />
                Refresh
              </button>
            </div>

            <div className="directory-toolbar">
              <div className="search-box">
                <Search size={17} />
                <input
                  type="search"
                  placeholder="Search employees..."
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  aria-label="Search employees"
                />
              </div>

              <span className="employee-count">
                {filteredEmployees.length} employee
                {filteredEmployees.length !== 1 ? "s" : ""}
              </span>
            </div>

            <div className="employee-table-wrapper">
              <table className="employee-table">
                <thead>
                  <tr>
                    <th>EMPLOYEE</th>
                    <th>DEPARTMENT</th>
                    <th>DESIGNATION</th>
                    <th>SALARY</th>
                    <th>STATUS</th>
                    <th>ACTIONS</th>
                  </tr>
                </thead>

                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="empty-state">
                        Loading employees...
                      </td>
                    </tr>
                  ) : filteredEmployees.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="empty-state">
                        {error
                          ? "Employee records could not be loaded."
                          : "No employees found."}
                      </td>
                    </tr>
                  ) : (
                    filteredEmployees.map((employee) => (
                      <tr key={employee.id}>
                        <td>
                          <div className="employee-name-cell">
                            <div className="employee-avatar">
                              {(employee.full_name || "?")
                                .trim()
                                .charAt(0)
                                .toUpperCase()}
                            </div>

                            <div>
                              <strong>{employee.full_name}</strong>
                              <span>{employee.employee_code}</span>
                              <small>{employee.email}</small>
                            </div>
                          </div>
                        </td>

                        <td>{employee.department || "—"}</td>
                        <td>{employee.designation || "—"}</td>

                        <td>
                          {employee.salary == null
                            ? "—"
                            : Number(employee.salary).toLocaleString(
                                "en-IN",
                                {
                                  style: "currency",
                                  currency: "INR",
                                  maximumFractionDigits: 2,
                                }
                              )}
                        </td>

                        <td>
                          <span
                            className={`employee-status ${
                              (employee.status || "Active").toLowerCase()
                            }`}
                          >
                            {employee.status || "Active"}
                          </span>
                        </td>

                        <td>
                          <div className="employee-actions">
                            <button
                              type="button"
                              className="icon-action edit"
                              title="Edit employee"
                              aria-label={`Edit ${employee.full_name}`}
                              onClick={() => openEditModal(employee)}
                            >
                              <Pencil size={15} />
                            </button>

                            <button
                              type="button"
                              className="icon-action delete"
                              title="Delete employee"
                              aria-label={`Delete ${employee.full_name}`}
                              onClick={() => handleDelete(employee)}
                            >
                              <Trash2 size={15} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {activePage === "attendance" && (
        <Attendance onAttendanceChange={loadDashboardStats} />
      )}

      {activePage === "reports" && <MonthlyReports />}

      {activePage === "leaves" && <LeaveManagement user={user} />}

      {activePage === "payroll" && <Payroll />}

      <footer className="footer">
        <span>WorkSphere HRMS</span>
        <span>
          Employee, Attendance, Reports, Leave Management and Payroll
        </span>
      </footer>

      {showModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div
            className="employee-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="modal-heading">
              <div>
                <h2>
                  {editingId !== null ? "Edit Employee" : "Add Employee"}
                </h2>
                <p>
                  {editingId !== null
                    ? "Update the employee details below."
                    : "Enter the new employee details below."}
                </p>
              </div>

              <button
                type="button"
                className="modal-close"
                onClick={closeModal}
                aria-label="Close dialog"
                disabled={saving}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-grid">
                <label>
                  Employee Code
                  <input
                    name="employee_code"
                    value={form.employee_code}
                    onChange={handleChange}
                    placeholder="EMP002"
                    maxLength={30}
                    required
                  />
                </label>

                <label>
                  Full Name
                  <input
                    name="full_name"
                    value={form.full_name}
                    onChange={handleChange}
                    placeholder="Employee name"
                    maxLength={120}
                    required
                  />
                </label>

                <label>
                  Email
                  <input
                    name="email"
                    type="email"
                    value={form.email}
                    onChange={handleChange}
                    placeholder="employee@example.com"
                    required
                  />
                </label>

                <label>
                  Department
                  <input
                    name="department"
                    value={form.department}
                    onChange={handleChange}
                    placeholder="IT"
                    maxLength={100}
                    required
                  />
                </label>

                <label>
                  Designation
                  <input
                    name="designation"
                    value={form.designation}
                    onChange={handleChange}
                    placeholder="Software Developer"
                    maxLength={100}
                    required
                  />
                </label>

                <label>
                  Salary (₹)
                  <input
                    name="salary"
                    type="number"
                    min="0"
                    step="0.01"
                    value={form.salary}
                    onChange={handleChange}
                    placeholder="45000"
                    required
                  />
                </label>

                <label>
                  Status
                  <select
                    name="status"
                    value={form.status}
                    onChange={handleChange}
                    required
                  >
                    <option value="Active">Active</option>
                    <option value="Inactive">Inactive</option>
                  </select>
                </label>
              </div>

              {error && (
                <div className="app-alert error" role="alert">
                  {error}
                </div>
              )}

              <div className="modal-actions">
                <button
                  type="button"
                  className="cancel-btn"
                  onClick={closeModal}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="save-btn"
                  disabled={saving}
                >
                  {saving
                    ? "Saving..."
                    : editingId !== null
                    ? "Update Employee"
                    : "Save Employee"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}

export default Dashboard;
