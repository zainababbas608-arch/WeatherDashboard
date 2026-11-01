// In dev/Docker, /api is proxied to Flask. On GitHub Pages, VITE_API_BASE points to the hosted backend.
export const API = import.meta.env.VITE_API_BASE || "";

const handle = async (res) => {
  if (!res.ok) throw new Error(`Server error (${res.status})`);
  return res.json();
};

export const getCities = () => fetch(`${API}/api/cities`).then(handle);
export const refreshCities = () => fetch(`${API}/api/refresh`, { method: "POST" }).then(handle);
export const sendChat = (message, history = []) =>
  fetch(`${API}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  }).then(handle);