import { useState, useRef, useEffect, useCallback } from "react";

// ─── TYPES ───────────────────────────────────
type MsgKind = "text" | "err_unknown" | "err_notfound";

interface BotMsg {
  id: number;
  role: "bot";
  kind: MsgKind;
  text?: string;
  suggestions?: string[];
  timestamp: string;
}

interface UserMsg {
  id: number;
  role: "user";
  text: string;
  timestamp: string;
}

type ChatMsg = UserMsg | BotMsg;

interface CartLine {
  item: string;
  quantity: number;
  amount: number;
}

interface CartData {
  lines: CartLine[];
  total: number;
  total_items: number;
}

// ─── DATA ─────────────────────────────────────
const QUICK_ACTIONS = [
  { emoji: "🍽️", label: "View Menu", q: "Show me the full menu" },
  { emoji: "💰", label: "Check Prices", q: "What are your prices?" },
  { emoji: "🕐", label: "Opening Hours", q: "What are your opening hours?" },
  { emoji: "⭐", label: "Popular Items", q: "Show me your popular dishes" },
];

const CHIPS = [
  { label: "What are today's specials?", q: "What are today's specials?" },
  { label: "How much is the burger?", q: "How much is the burger?" },
  { label: "Are you open today?", q: "Are you open today?" },
  { label: "Show me drinks", q: "Show me drinks" },
  { label: "Vegetarian options", q: "Do you have vegetarian options?" },
  { label: "Under ₹200", q: "Show me the full menu" },
];

// ─── HELPERS ──────────────────────────────────
let _id = 1;
const uid = () => _id++;
const ts = () => new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });

// ─── ICONS ────────────────────────────────────
const SendArrow = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);
const MinIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);
const XIcon = ({ s = 14 }: { s?: number }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);
const Chip = ({ label, onClick }: { label: string; onClick: () => void }) => (
  <button onClick={onClick} className="chip-btn flex-shrink-0 text-[11.5px] font-medium rounded-full px-3.5 py-1.5 border border-[#F0C8C0] text-[#C84040] bg-transparent whitespace-nowrap cursor-pointer hover:bg-[#FFF0EC] transition-colors">
    {label}
  </button>
);

// ─── ATOMS ────────────────────────────────────
function BotAvatar({ size = 28 }: { size?: number }) {
  return (
    <div
      className="rounded-2xl flex items-center justify-center flex-shrink-0 text-sm"
      style={{ width: size, height: size, background: "linear-gradient(135deg,#F47055 0%,#D03828 100%)", boxShadow: "0 2px 8px rgba(208,56,40,0.35)" }}
    >🍽️</div>
  );
}

function TypingBubble() {
  return (
    <div className="flex items-end gap-2.5 msg-in">
      <BotAvatar />
      <div className="bg-white border border-[#EDD8D0] rounded-2xl rounded-bl-sm px-4 py-3.5 shadow-sm flex items-center gap-1.5">
        <span className="dot1 w-2 h-2 rounded-full inline-block bg-[#D83828]" />
        <span className="dot2 w-2 h-2 rounded-full inline-block bg-[#D83828]" />
        <span className="dot3 w-2 h-2 rounded-full inline-block bg-[#D83828]" />
      </div>
    </div>
  );
}

// ─── BUBBLE COMPONENTS ────────────────────────
function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex justify-end msg-in">
      <div
        className="max-w-[78%] rounded-2xl rounded-br-sm px-4 py-3 text-[13.5px] leading-relaxed text-white shadow-sm"
        style={{ background: "linear-gradient(135deg,#E85038 0%,#C82820 100%)" }}
      >{text}</div>
    </div>
  );
}

function BotTextBubble({ text }: { text: string }) {
  const parts = text.split(/\*\*(.*?)\*\*/g);
  const formatted = parts.map((p, i) =>
    i % 2 === 1 ? <strong key={i} className="text-[#B83020] font-semibold">{p}</strong> : p
  );
  return (
    <div className="flex items-end gap-2.5 msg-in">
      <BotAvatar />
      <div className="bg-white border border-[#EDD8D0] rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm max-w-[85%]">
        <p className="text-[13.5px] text-[#3A2018] leading-relaxed whitespace-pre-wrap">{formatted}</p>
      </div>
    </div>
  );
}

function ErrorBubble({ kind, text, suggestions, onSend }: { kind: MsgKind; text?: string; suggestions?: string[]; onSend: (t: string) => void }) {
  return (
    <div className="flex items-end gap-2.5 msg-in w-full">
      <BotAvatar />
      <div className="flex flex-col gap-2 max-w-[85%]">
        <div className="bg-amber-50 border border-amber-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
          <p className="text-[13px] font-semibold text-[#1A1008]">
            {kind === "err_notfound" ? "🔍 Item not found" : "⚠️ Server connection issue"}
          </p>
          {text && <p className="text-[12.5px] text-[#4A3020] mt-1 leading-relaxed">{text}</p>}
        </div>
        {suggestions && (
          <div className="flex flex-wrap gap-1.5">
            {suggestions.map(s => <Chip key={s} label={s} onClick={() => onSend(s)} />)}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── WELCOME SCREEN ──────────────────────────
function WelcomeScreen({ onSend }: { onSend: (t: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-start h-full px-4 pt-8 pb-4 overflow-y-auto" style={{ scrollbarWidth: "none" }}>
      <div className="text-4xl mb-3 select-none" style={{ filter: "drop-shadow(0 2px 6px rgba(0,0,0,0.12))" }}>👋</div>

      <h2 className="text-[1.65rem] font-extrabold text-[#1A1008] text-center leading-snug mb-1.5" style={{ fontFamily: "Outfit,sans-serif" }}>
        Welcome to Cafe Delight!
      </h2>
      <p className="text-[13.5px] text-[#6A5048] text-center leading-relaxed max-w-[290px] mb-6">
        I am your personal ordering assistant. Ask me about our menu, prices, or place an order!
      </p>

      <div className="grid grid-cols-2 gap-3 w-full mb-5">
        {QUICK_ACTIONS.map(a => (
          <button key={a.label} onClick={() => onSend(a.q)}
            className="qa-card bg-white border border-[#EDD8D0] hover:border-[#E85038] rounded-2xl p-4 text-left shadow-sm cursor-pointer transition-all"
          >
            <span className="text-[2rem] block mb-2 leading-none">{a.emoji}</span>
            <span className="text-[13.5px] font-semibold text-[#1A1008] block leading-snug" style={{ fontFamily: "Outfit,sans-serif" }}>{a.label}</span>
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2 justify-center">
        {CHIPS.slice(0, 4).map(c => (
          <button key={c.label} onClick={() => onSend(c.q)}
            className="chip-btn text-[12px] font-medium rounded-full px-3.5 py-1.5 border border-[#F0C8C0] text-[#C84040] bg-transparent whitespace-nowrap cursor-pointer hover:bg-[#FFF0EC] transition-colors"
          >{c.label}</button>
        ))}
      </div>
    </div>
  );
}

// ─── CHAT PANEL ──────────────────────────────
export default function App() {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [cart, setCart] = useState<CartData>({ lines: [], total: 0, total_items: 0 });

  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const empty = messages.length === 0 && !typing;
  const cnt = cart.total_items;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  // Initial cart synchronization with Flask backend session
  useEffect(() => {
    fetch('/api/cart/summary', { credentials: 'same-origin' })
      .then(res => res.json())
      .then((data: CartData) => {
        if (data && typeof data.total === 'number') {
          setCart(data);
        }
      })
      .catch(err => console.warn("Initial cart summary fetch failed:", err));
  }, []);

  const handleViewCart = useCallback(async () => {
    if (typing) return;
    setTyping(true);
    try {
      const res = await fetch('/api/cart/view', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin'
      });
      const data = await res.json();
      setTyping(false);
      if (data.message) {
        setMessages(prev => [...prev, { id: uid(), role: "bot", kind: "text", text: data.message, timestamp: ts() }]);
      }
      if (data.cart) {
        setCart(data.cart);
      }
    } catch (err) {
      setTyping(false);
      setMessages(prev => [...prev, {
        id: uid(),
        role: "bot",
        kind: "err_unknown",
        text: "Unable to view cart. Please make sure the Flask backend is running.",
        timestamp: ts()
      }]);
    }
  }, [typing]);

  const handleClearCart = useCallback(async () => {
    if (typing) return;
    setTyping(true);
    try {
      const res = await fetch('/api/cart/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin'
      });
      const data = await res.json();
      setTyping(false);
      if (data.message) {
        setMessages(prev => [...prev, { id: uid(), role: "bot", kind: "text", text: data.message, timestamp: ts() }]);
      }
      if (data.cart) {
        setCart(data.cart);
      }
    } catch (err) {
      setTyping(false);
      setMessages(prev => [...prev, {
        id: uid(),
        role: "bot",
        kind: "err_unknown",
        text: "Unable to clear cart. Please make sure the Flask backend is running.",
        timestamp: ts()
      }]);
    }
  }, [typing]);

  const sendMessage = useCallback(async (raw: string) => {
    const text = raw.trim();
    if (!text || typing) return;

    const lower = text.toLowerCase();
    if (lower === "view cart" || lower === "show cart") {
      handleViewCart();
      return;
    }
    if (lower === "clear cart" || lower === "clear order") {
      handleClearCart();
      return;
    }

    setMessages(prev => [...prev, { id: uid(), role: "user", text, timestamp: ts() }]);
    setInput("");
    setTyping(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
        credentials: 'same-origin'
      });

      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }

      const data = await res.json();
      setTyping(false);

      if (data.message) {
        setMessages(prev => [...prev, { id: uid(), role: "bot", kind: "text", text: data.message, timestamp: ts() }]);
      }
      if (data.cart) {
        setCart(data.cart);
      }
    } catch (err) {
      setTyping(false);
      setMessages(prev => [...prev, {
        id: uid(),
        role: "bot",
        kind: "err_unknown",
        text: "Unable to reach Cafe Delight backend server. Please verify python app.py is running on http://127.0.0.1:5000.",
        timestamp: ts(),
        suggestions: ["View Menu", "Show cart"]
      }]);
    }
  }, [typing, handleViewCart, handleClearCart]);

  return (
    <div className="w-full h-full flex items-center justify-center" style={{ background: "#EDE3DC" }}>
      <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse 70% 70% at 50% 50%, #F5EDE8 0%, #E0D0C8 100%)", opacity: 0.9 }} />

      {/* ── THE CHATBOT PANEL ── */}
      <div
        className="chat-shell relative flex flex-col overflow-hidden bg-white"
        style={{
          width: "clamp(340px, 90vw, 440px)",
          height: "clamp(560px, 88vh, 730px)",
          borderRadius: "20px",
          border: "1px solid #E8D0C8",
          boxShadow: "0 32px 80px rgba(80,30,20,0.18), 0 8px 24px rgba(80,30,20,0.10), 0 1px 4px rgba(80,30,20,0.06)",
        }}
      >
        {/* ── HEADER ── */}
        <div
          className="flex items-center gap-3 px-4 py-3.5 flex-shrink-0"
          style={{ background: "linear-gradient(135deg,#E85038 0%,#D83828 60%,#C02818 100%)" }}
        >
          {/* Avatar */}
          <div className="relative flex-shrink-0">
            <div className="w-10 h-10 rounded-2xl bg-white/20 flex items-center justify-center text-[1.2rem] backdrop-blur-sm">🍽️</div>
            <span className="online-dot absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 border-2 border-white" />
          </div>
          {/* Text */}
          <div className="flex-1 min-w-0">
            <p className="text-white font-extrabold text-[15px] leading-tight" style={{ fontFamily: "Outfit,sans-serif" }}>Cafe Delight</p>
            <p className="text-white/80 text-[11.5px] flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
              Smart Ordering Assistant · Online
            </p>
          </div>
          {/* Cart badge */}
          {cnt > 0 && (
            <button onClick={handleViewCart}
              className="flex items-center gap-1 bg-white/20 hover:bg-white/30 rounded-full px-2.5 py-1.5 cursor-pointer transition-colors badge-pop"
              title="View Cart"
            >
              <span className="text-white text-[11px] font-bold">🛒 {cart.total_items} · Rs. {cart.total}</span>
            </button>
          )}
          {/* Controls */}
          <div className="flex items-center gap-1 ml-1">
            <button className="w-7 h-7 rounded-lg bg-white/15 hover:bg-white/28 flex items-center justify-center text-white cursor-pointer transition-colors" title="Minimize"><MinIcon /></button>
            <button className="w-7 h-7 rounded-lg bg-white/15 hover:bg-white/28 flex items-center justify-center text-white cursor-pointer transition-colors" title="Close"><XIcon /></button>
          </div>
        </div>

        {/* ── MESSAGES ── */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-3" style={{ background: "#FEF9F6" }}>
          {empty
            ? <WelcomeScreen onSend={sendMessage} />
            : (
              <>
                {messages.map(msg => {
                  if (msg.role === "user") {
                    return (
                      <div key={msg.id} className="flex flex-col items-end gap-1">
                        <UserBubble text={msg.text} />
                        <span className="text-[10px] text-[#C0A090] pr-0.5">{msg.timestamp}</span>
                      </div>
                    );
                  }
                  const bot = msg as BotMsg;
                  return (
                    <div key={bot.id} className="flex flex-col items-start gap-1.5">
                      {bot.kind === "text" && <BotTextBubble text={bot.text ?? ""} />}
                      {bot.kind === "err_unknown" && <ErrorBubble kind={bot.kind} text={bot.text} suggestions={bot.suggestions} onSend={sendMessage} />}
                      <span className="text-[10px] text-[#C0A090] pl-9">{bot.timestamp}</span>
                    </div>
                  );
                })}
                {typing && <TypingBubble />}
              </>
            )
          }
          <div ref={endRef} />
        </div>

        {/* ── CHIP STRIP (active chat only) ── */}
        {!empty && (
          <div className="flex gap-1.5 px-3 py-2 bg-white border-t border-[#F0E0D8] overflow-x-auto flex-shrink-0" style={{ scrollbarWidth: "none" }}>
            {CHIPS.map(c => (
              <button key={c.label} onClick={() => sendMessage(c.q)}
                className="chip-btn flex-shrink-0 text-[10.5px] font-medium rounded-full px-3 py-1.5 border border-[#F0C8C0] text-[#C84040] bg-transparent whitespace-nowrap cursor-pointer hover:bg-[#FFF0EC] transition-colors"
              >{c.label}</button>
            ))}
          </div>
        )}

        {/* ── INPUT BAR ── */}
        <div className="flex items-center gap-2.5 px-3 py-3 bg-white border-t border-[#EDD8D0] flex-shrink-0">
          <div className="flex-1 flex items-center gap-2 rounded-2xl px-4 py-2.5 border border-transparent transition-all focus-within:border-[#E85038] focus-within:ring-2 focus-within:ring-[#E85038]/12"
            style={{ background: "#FFF0EC" }}
          >
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); } }}
              placeholder="Ask about menu, prices or order food..."
              disabled={typing}
              className="flex-1 bg-transparent text-[13.5px] text-[#1A1008] placeholder-[#C8A098] outline-none disabled:opacity-50"
            />
          </div>
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || typing}
            className="send-btn w-10 h-10 rounded-xl flex items-center justify-center text-white cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed flex-shrink-0 transition-all"
            style={{
              background: input.trim() && !typing ? "linear-gradient(135deg,#E85038,#C82820)" : "#E8C0B8",
              boxShadow: input.trim() && !typing ? "0 4px 14px rgba(232,80,56,0.45)" : "none",
            }}
          ><SendArrow /></button>
        </div>
      </div>
    </div>
  );
}

