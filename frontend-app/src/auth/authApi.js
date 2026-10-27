
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";
const TOKEN_KEY = "worksphere_access_token";

export async function registerUser(userData) {
  const response = await axios.post(
    `${API_URL}/auth/register`,
    {
      username: userData.username,
      email: userData.email,
      password: userData.password,
    }
  );

  return response.data;
}

export async function loginUser(username, password) {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const response = await axios.post(
    `${API_URL}/auth/login`,
    formData,
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    }
  );

  const token = response.data.access_token;

  if (!token) {
    throw new Error("The login response did not contain an access token.");
  }

  localStorage.setItem(TOKEN_KEY, token);

  return response.data;
}

export async function getCurrentUser() {
  const token = localStorage.getItem(TOKEN_KEY);

  if (!token) {
    throw new Error("No login token found.");
  }

  const response = await axios.get(`${API_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return response.data;
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function logoutUser() {
  localStorage.removeItem(TOKEN_KEY);
}
