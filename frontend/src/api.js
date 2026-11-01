// All calls go through the Vite proxy (/api -> http://localhost:5000)
const handle = async (res) => {
  if (!res.ok) throw new Error(`Server error (${res.status})`);
  return res.json();
};

export const getCities = () => fetch("/api/cities").then(handle);
export const refreshCities = () => fetch("/api/refresh", { method: "POST" }).then(handle);
export const sendChat = (message, history = []) =>
  fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  }).then(handle);