import axios from "axios";

const BASE_URL = "https://api-woad-ten-44.vercel.app/api";

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("forex_trading_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || "Request failed";
    return Promise.reject(new Error(msg));
  }
);

export default api;

// Direct bridge client - no auth, no /api prefix
export const bridgeApi = axios.create({
  baseURL: "http://localhost:8765",
  headers: { "Content-Type": "application/json" },
});

bridgeApi.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || "Bridge request failed";
    return Promise.reject(new Error(msg));
  }
);
