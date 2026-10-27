
import { useState } from "react";
import { loginUser, getCurrentUser, logoutUser } from "./auth/authApi";

export default function Login({ onLoginSuccess, onShowRegister }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await loginUser(username.trim(), password);
      const user = await getCurrentUser();
      onLoginSuccess(user);
    } catch (err) {
      logoutUser();

      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Login failed. Check your username/email and password, then try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>WorkSphere HRMS</h1>
        <h2>Welcome back</h2>
        <p>Sign in to your account</p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="login-username">Username or email</label>
          <input
            id="login-username"
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Enter username or email"
            autoComplete="username"
            required
          />

          <label htmlFor="login-password">Password</label>
          <input
            id="login-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter password"
            autoComplete="current-password"
            required
          />

          {error && <p className="auth-error" role="alert">{error}</p>}

          <button type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="auth-switch">
          Don't have an account?{" "}
          <button type="button" onClick={onShowRegister}>
            Create account
          </button>
        </p>
      </div>
    </div>
  );
}
