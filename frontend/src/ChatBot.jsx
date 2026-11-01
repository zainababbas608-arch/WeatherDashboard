import "./chat.css";
import { useEffect, useRef, useState } from "react";
import { sendChat } from "./api";

const SUGGESTIONS = [
  "Which city is hottest?",
  "Which city has the most sunshine?",
  "Compare Karachi and Lahore",
  "Average temperature",
  "Give me a summary",
];

export default function ChatBot() {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [input, setInput] = useState("");
  const [msgs, setMsgs] = useState([
    { role: "assistant", content: "Hi! Ask me anything about the weather data for the 7 cities." },
  ]);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, open]);

  const send = async (text) => {
    const q = (text ?? input).trim();
    if (!q || busy) return;
    const history = msgs.slice(1);              // skip the greeting
    setMsgs((m) => [...m, { role: "user", content: q }]);
    setInput("");
    setBusy(true);
    try {
      const { reply } = await sendChat(q, history);
      setMsgs((m) => [...m, { role: "assistant", content: reply }]);
    } catch {
      setMsgs((m) => [...m, { role: "assistant", content: "Sorry, I could not reach the server." }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <button className="chat-fab" onClick={() => setOpen((o) => !o)} aria-label="Toggle chatbot">
        {open ? "✕" : "💬"}
      </button>
      {open && (
        <div className="chat-box" role="dialog" aria-label="Weather analytics chatbot">
          <div className="chat-head">Weather Analytics Bot</div>
          <div className="chat-body">
            {msgs.map((m, i) => (
              <div key={i} className={`bubble ${m.role}`}>{m.content}</div>
            ))}
            {busy && <div className="bubble assistant">Thinking…</div>}
            <div ref={endRef} />
          </div>
          <div className="chips">
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => send(s)} disabled={busy}>{s}</button>
            ))}
          </div>
          <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send(); }}>
            <input value={input} onChange={(e) => setInput(e.target.value)}
                   placeholder="Ask about the data…" maxLength={500} />
            <button type="submit" disabled={busy || !input.trim()}>Send</button>
          </form>
        </div>
      )}
    </>
  );
}
