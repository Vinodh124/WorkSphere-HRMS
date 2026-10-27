
import { useEffect, useState } from "react";
import Login from "./Login";
import Register from "./Register";
import Dashboard from "./Dashboard";
import {
  getCurrentUser,
  getToken,
  logoutUser,
} from "./auth/authApi";
import "./Auth.css";

function App() {
  const [user, setUser] = useState(null);
  const [authPage, setAuthPage] = useState("login");
  const [checkingLogin, setCheckingLogin] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function checkExistingLogin() {
      if (!getToken()) {
        setCheckingLogin(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser();

        if (!cancelled) {
          setUser(currentUser);
        }
      } catch {
        logoutUser();

        if (!cancelled) {
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setCheckingLogin(false);
        }
      }
    }

    checkExistingLogin();

    return () => {
      cancelled = true;
    };
  }, []);

  function handleLoginSuccess(currentUser) {
    setUser(currentUser);
  }

  function handleLogout() {
    logoutUser();
    setUser(null);
    setAuthPage("login");
  }

  if (checkingLogin) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <h1>WorkSphere HRMS</h1>
          <p>Checking your login...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    if (authPage === "register") {
      return (
        <Register
          onShowLogin={() => setAuthPage("login")}
        />
      );
    }

    return (
      <Login
        onLoginSuccess={handleLoginSuccess}
        onShowRegister={() => setAuthPage("register")}
      />
    );
  }

  return (
    <>
      <Dashboard user={user} />

      <button
        type="button"
        onClick={handleLogout}
        title={`Sign out ${user.username || ""}`}
        style={{
          position: "fixed",
          top: "12px",
          right: "16px",
          zIndex: 10000,
          padding: "10px 16px",
          border: "1px solid #cbd5e1",
          borderRadius: "8px",
          background: "#ffffff",
          color: "#334155",
          fontWeight: 600,
          cursor: "pointer",
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
        }}
      >
        Logout
      </button>
    </>
  );
}

export default App;
