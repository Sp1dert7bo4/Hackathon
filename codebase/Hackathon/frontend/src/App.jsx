import React, { useMemo, useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker as LeafletMarker, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const fallbackRecommendations = [
  {
    id: "demo-manhwah",
    name: "Manwah Cầu Giấy",
    cuisine: "Hotpot",
    rating: 4.8,
    price: "299k/người",
    distance: null,
    status: "Open now",
    kind: "ai",
    x: "59%",
    y: "42%",
    image: "https://images.unsplash.com/photo-1562607635-46016eaa1c40?auto=format&fit=crop&w=900&q=80",
    address: "Cầu Giấy, Hà Nội",
    reasons: ["Within your budget", "Suitable for groups of 4", "Highly rated", "Currently open"],
  },
  {
    id: "demo-nola",
    name: "Nola Cafe & Bar",
    cuisine: "Cafe",
    rating: 4.6,
    price: "90k-160k",
    distance: null,
    status: "Open now",
    kind: "cafe",
    x: "39%",
    y: "29%",
    image: "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=900&q=80",
    address: "Hoàn Kiếm, Hà Nội",
    reasons: ["Quiet atmosphere", "Good for study sessions", "Near Hồ Gươm", "Strong reviews"],
  },
  {
    id: "demo-sushi",
    name: "Sushi Zen Tràng Tiền",
    cuisine: "Japanese",
    rating: 4.7,
    price: "250k-380k",
    distance: null,
    status: "Open now",
    kind: "restaurant",
    x: "68%",
    y: "61%",
    image: "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=900&q=80",
    address: "Hoàn Kiếm, Hà Nội",
    reasons: ["Date-night friendly", "Premium Japanese menu", "Great rating", "Easy directions"],
  },
];

const filters = ["Near me", "Under 200k", "Cafe", "Buffet", "Date Night", "Family", "Japanese", "Korean"];
const examplePrompt = "Quán cafe phù hợp để học bài gần Hồ Gươm dưới 150k/người";

function SearchIcon({ className = "h-5 w-5" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="m21 21-4.35-4.35m1.35-5.15a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M21 3 10.8 13.2M21 3l-6.5 18-3.7-7.8L3 9.5 21 3Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function formatMoneyRange(restaurant) {
  if (restaurant.price_range) return restaurant.price_range;
  const min = Number(restaurant.price_min || 0).toLocaleString("vi-VN");
  const max = Number(restaurant.price_max || 0).toLocaleString("vi-VN");
  return `${min}-${max} VND`;
}

function pointFromIndex(index) {
  const points = [
    ["58%", "42%"],
    ["39%", "29%"],
    ["68%", "61%"],
    ["24%", "56%"],
    ["76%", "26%"],
    ["47%", "72%"],
  ];
  return points[index % points.length];
}

function mapApiResult(item, index, canUseDistance = false) {
  const restaurant = item.restaurant;
  const tags = restaurant.cuisine_tags || [];
  const cuisine = tags[0] || "Restaurant";
  const isCafe = tags.some((tag) => tag.toLowerCase().includes("cà phê") || tag.toLowerCase().includes("cafe"));

  return {
    id: restaurant.id,
    name: restaurant.name,
    cuisine,
    rating: restaurant.rating,
    price: formatMoneyRange(restaurant),
    distance: canUseDistance ? `${restaurant.distance_km}km` : null,
    status: restaurant.status === "open" ? "Open now" : "Closed",
    kind: isCafe ? "cafe" : "restaurant",
    lat: restaurant.latitude,
    lng: restaurant.longitude,
    image: restaurant.image_url,
    address: restaurant.address,
    reasons: item.reasons?.length ? item.reasons : ["Matches your request", "Good rating", "Relevant location", "Budget friendly"],
    raw: item,
  };
}

function ChatBubble({ role, children }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[82%] rounded-3xl px-5 py-4 text-[15px] leading-6 shadow-sm ${isUser ? "bg-slate-100 text-slate-900" : "bg-blue-50 text-slate-800"}`}>
        {children}
      </div>
    </div>
  );
}

function FilterChips({ onPick }) {
  return (
    <div className="flex gap-2 overflow-hidden">
      {filters.map((filter, index) => (
        <button
          key={filter}
          onClick={() => onPick(filter)}
          className={`shrink-0 rounded-full border px-4 py-2 text-sm font-semibold transition-all hover:-translate-y-0.5 hover:shadow-md ${
            index < 3 ? "border-primary bg-primary text-white shadow-sm" : "border-border bg-white text-slate-600 hover:border-primary hover:text-primary"
          }`}
        >
          {filter}
        </button>
      ))}
    </div>
  );
}

function RecommendationCard({ item, selected, onSelect, onFeedback }) {
  return (
    <article
      onClick={() => onSelect(item)}
      className={`group cursor-pointer rounded-[24px] border bg-white p-3 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-soft ${
        selected ? "border-primary ring-4 ring-blue-100" : "border-border"
      }`}
    >
      <div className="flex gap-4">
        <img className="h-28 w-28 shrink-0 rounded-2xl object-cover" src={item.image} alt={item.name} />
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="truncate text-lg font-extrabold text-slate-950">{item.name}</h3>
              <p className="text-sm font-semibold text-slate-500">{item.cuisine}</p>
            </div>
            <span className={`rounded-full px-3 py-1 text-xs font-bold ${item.status === "Open now" ? "bg-emerald-50 text-success" : "bg-amber-50 text-warning"}`}>
              {item.status}
            </span>
          </div>
          <div className="mt-3 text-sm font-semibold text-slate-700">
            <span>Star {item.rating}</span>
          </div>
        </div>
      </div>
      <div className="mt-3 rounded-2xl border border-blue-100 bg-blue-50/80 p-3">
        <p className="mb-2 text-sm font-extrabold text-primary">Why AI recommends this</p>
        <div className="grid grid-cols-2 gap-2">
          {item.reasons.slice(0, 4).map((reason) => (
            <span key={reason} className="text-xs font-semibold text-slate-700">✓ {reason}</span>
          ))}
        </div>
      </div>
      <div className="mt-3 flex gap-2">
        {["Quá xa", "Quá đắt", "Rating thấp"].map((reason) => (
          <button
            key={reason}
            onClick={(event) => {
              event.stopPropagation();
              onFeedback(reason);
            }}
            className="rounded-full border border-border px-3 py-1.5 text-xs font-bold text-slate-600 transition hover:border-primary hover:text-primary"
          >
            {reason}
          </button>
        ))}
      </div>
    </article>
  );
}

function createCustomIcon(kind, selected) {
  const colors = {
    restaurant: "bg-red-500 ring-red-100",
    cafe: "bg-blue-500 ring-blue-100",
    ai: "bg-emerald-500 ring-emerald-100",
  };
  const label = kind === "cafe" ? "C" : kind === "ai" ? "AI" : "R";
  const scaleClass = selected ? "scale-125" : "scale-100";
  const html = `<div class="grid h-11 w-11 place-items-center rounded-full text-white shadow-marker ring-8 transition-transform duration-300 ${colors[kind] || colors.restaurant} ${scaleClass}">${label}</div>`;
  
  return L.divIcon({
    html,
    className: "custom-leaflet-marker border-none bg-transparent",
    iconSize: [44, 44],
    iconAnchor: [22, 22],
  });
}

function MapController({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, 15, { animate: true });
    }
  }, [center, map]);
  return null;
}

function MapPanel({ recommendations, selected, onSelect }) {
  const markers = recommendations.filter((m) => m.lat && m.lng);
  const active = selected && selected.lat && selected.lng ? selected : markers[0] || null;
  const center = active ? [active.lat, active.lng] : [21.0285, 105.8542];

  return (
    <section className="relative h-full overflow-hidden bg-slate-100">
      <MapContainer center={center} zoom={14} style={{ height: "100%", width: "100%", zIndex: 0 }} zoomControl={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />
        <MapController center={center} />
        {markers.map((marker) => (
          <LeafletMarker 
            key={marker.id} 
            position={[marker.lat, marker.lng]}
            icon={createCustomIcon(marker.kind, active?.id === marker.id)}
            eventHandlers={{ click: () => onSelect(marker) }}
          />
        ))}
      </MapContainer>

      <div className="absolute left-1/2 top-6 z-30 w-[min(520px,calc(100%-48px))] -translate-x-1/2 rounded-3xl border border-white/70 bg-white/75 px-5 py-4 shadow-soft backdrop-blur-xl pointer-events-none">
        <div className="flex items-center gap-4">
          <div className="grid h-11 w-11 place-items-center rounded-2xl bg-primary text-white shadow-lg shadow-blue-500/25">
            <SearchIcon />
          </div>
          <div>
            <p className="text-lg font-extrabold text-slate-950">Hà Nội</p>
            <p className="text-sm font-semibold text-slate-500">{markers.length ? `${markers.length} địa điểm trên bản đồ` : "Chưa có địa điểm nào có toạ độ"}</p>
          </div>
        </div>
      </div>

      {active && (
        <div className="absolute bottom-8 left-8 z-30 w-[360px] overflow-hidden rounded-[28px] border border-white/80 bg-white shadow-soft">
          <img className="h-36 w-full object-cover" src={active.image} alt={active.name} />
          <div className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-xl font-extrabold text-slate-950">{active.name}</h3>
                <p className="mt-1 text-sm font-semibold text-slate-500">{active.cuisine}</p>
              </div>
              <span className="rounded-full bg-amber-50 px-3 py-1 text-sm font-extrabold text-warning">Star {active.rating}</span>
            </div>
            <p className="mt-3 line-clamp-2 text-sm font-semibold text-slate-600">{active.address}</p>
            <div className="mt-5 flex gap-3">
              <button 
                onClick={() => {
                  if (active.lat && active.lng) {
                    window.open(`https://www.google.com/maps/dir/?api=1&destination=${active.lat},${active.lng}`, '_blank');
                  } else {
                    window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(active.address || active.name)}`, '_blank');
                  }
                }}
                className="flex-1 rounded-2xl border border-border bg-white px-4 py-3 text-sm font-extrabold text-slate-700 transition hover:-translate-y-0.5 hover:border-primary hover:text-primary">
                Get Directions
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [apiResults, setApiResults] = useState([]);
  const [selected, setSelected] = useState(null);
  const [lastIntent, setLastIntent] = useState(null);
  const [conversationState, setConversationState] = useState({});
  const [loading, setLoading] = useState(false);
  const [warning, setWarning] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [aiProvider, setAiProvider] = useState("rules");
  const [canUseDistance, setCanUseDistance] = useState(false);

  const recommendations = useMemo(() => apiResults.map((item, index) => mapApiResult(item, index, canUseDistance)), [apiResults, canUseDistance]);
  const visibleRecommendations = hasSearched ? recommendations : [];

  async function runSearch(text = input) {
    const prompt = text.trim();
    if (!prompt) return;
    
    setInput(""); // Xoá chữ trong input sau khi submit

    setLoading(true);
    setHasSearched(true);
    setWarning("");
    setMessages((current) => [...current, { role: "user", text: prompt }, { role: "ai", text: "Đang phân tích yêu cầu và tìm địa điểm phù hợp..." }]);

    try {
      const data = await postJson("/api/chat", {
        text: prompt,
        conversation_state: conversationState,
      });
      setLastIntent(data.intent);
      setConversationState(data.conversation_state || {});
      setAiProvider(data.ai_provider || "rules");
      setCanUseDistance(Boolean(data.can_use_distance));

      if (data.status === "unsupported_location") {
        setApiResults([]);
        setSelected(null);
        setWarning(data.explanation || "");
        setMessages((current) => [
          ...current.slice(0, -1),
          {
            role: "ai",
            text: data.questions?.[0] || "Mom ơi ăn gì :> hiện chỉ hỗ trợ khu vực Hà Nội. Bạn vui lòng nhập yêu cầu khác trong Hà Nội.",
          },
        ]);
        return;
      }

      if (data.status === "needs_clarification") {
        setApiResults([]);
        setSelected(null);
        setMessages((current) => [
          ...current.slice(0, -1),
          {
            role: "ai",
            text: `${data.explanation ? `${data.explanation} ` : ""}${data.questions.join(" ")}`,
          },
        ]);
        return;
      }

      setApiResults(data.ranked_restaurants || []);
      setWarning(data.warning || (data.can_use_distance ? "" : "Mình chưa có vị trí GPS chính xác của bạn nên không thể tính khoảng cách đến các quán."));
      const mapped = (data.ranked_restaurants || []).map((item, index) => mapApiResult(item, index, Boolean(data.can_use_distance)));
      if (mapped[0]) setSelected(mapped[0]);
      setMessages((current) => [
        ...current.slice(0, -1),
        { role: "ai", text: data.explanation || `Tôi đã tìm thấy ${mapped.length} địa điểm phù hợp.` },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current.slice(0, -1),
        { role: "ai", text: `Backend chưa phản hồi: ${error.message}. Hãy kiểm tra FastAPI server ở cổng 8000.` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function runFeedback(reason) {
    if (!lastIntent || !apiResults.length) return;

    setLoading(true);
    try {
      const data = await postJson("/api/feedback", {
        user_id: "demo-user",
        feedback: reason,
        reason,
        last_intent: lastIntent,
        shown_restaurant_ids: apiResults.map((item) => item.restaurant.id),
      });
      setApiResults(data.ranked_restaurants || []);
      const mapped = (data.ranked_restaurants || []).map((item, index) => mapApiResult(item, index, canUseDistance));
      if (mapped[0]) setSelected(mapped[0]);
      setMessages((current) => [...current, { role: "user", text: reason }, { role: "ai", text: data.explanation || "Mình đã re-rank theo phản hồi của bạn." }]);
    } catch (error) {
      setWarning(`Không xử lý được feedback: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }

  function applyFilter(filter) {
    const additions = {
      "Near me": " gần tôi",
      "Under 200k": " dưới 200k/người",
      Cafe: " cafe",
      Buffet: " buffet",
      "Date Night": " phù hợp hẹn hò tối nay",
      Family: " phù hợp gia đình",
      Japanese: " nhà hàng Nhật",
      Korean: " đồ Hàn",
    };
    setInput((current) => `${current}${additions[filter] || ""}`.trim());
  }

  return (
    <main className="grid h-screen w-screen grid-cols-1 overflow-hidden bg-appbg lg:grid-cols-2">
      <section className="flex h-full min-h-0 flex-col border-r border-border bg-white">
        <header className="flex h-20 shrink-0 items-center justify-between border-b border-border bg-white px-8 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-orange-50 text-orange-500 font-extrabold text-xl shadow-inner">MAG</div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-orange-500" style={{ fontFamily: 'Pattaya, sans-serif' }}>Mom ơi ăn gì :{'>'} ☀️</h1>
              <p className="text-sm font-semibold text-slate-500">AI-powered restaurant discovery</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`rounded-full px-3 py-1.5 text-xs font-extrabold ${aiProvider === "openai" ? "bg-emerald-50 text-success" : "bg-slate-100 text-slate-500"}`}>
              {aiProvider === "openai" ? "OpenAI on" : "Rules mode"}
            </span>
            <div className="grid h-11 w-11 place-items-center rounded-2xl border border-border bg-white text-primary shadow-sm">
              <SearchIcon />
            </div>
          </div>
        </header>

        <div className="flex min-h-0 flex-1 flex-col">
          <div className="min-h-0 flex-1 space-y-5 overflow-y-auto px-8 py-6">
            {!messages.length && (
              <div className="flex h-full flex-col items-center justify-center text-center">
                <div className="mb-5 grid h-16 w-16 place-items-center rounded-3xl bg-orange-50 text-2xl font-extrabold text-orange-500 shadow-inner">MAG</div>
                <h2 className="text-2xl font-extrabold text-slate-950">Bạn muốn tìm quán như thế nào?</h2>
                <p className="mt-2 max-w-md text-sm font-semibold leading-6 text-slate-500">
                  Nhập một yêu cầu tự nhiên. Mom ơi ăn gì :{'>'} sẽ phân tích món, khu vực, ngân sách rồi hiển thị gợi ý và vị trí trên bản đồ.
                </p>
                <div className="mt-6 grid w-full max-w-xl gap-2">
                  {[
                    "Tôi muốn ăn lẩu cho 4 người dưới 300k/người ở Cầu Giấy",
                    "Quán cafe phù hợp để học bài gần Hồ Gươm",
                    "Nhà hàng Nhật cho buổi hẹn hò tối nay",
                  ].map((sample) => (
                    <button
                      key={sample}
                      onClick={() => setInput(sample)}
                      className="rounded-2xl border border-border bg-white px-4 py-3 text-left text-sm font-semibold text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:border-primary hover:text-primary hover:shadow-md"
                    >
                      {sample}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((message, index) => (
              <ChatBubble key={`${message.role}-${index}`} role={message.role}>{message.text}</ChatBubble>
            ))}
            {hasSearched && (conversationState.food_type || conversationState.location || conversationState.budget || conversationState.occasion) && (
              <div className="rounded-2xl border border-blue-100 bg-blue-50/70 px-4 py-3 text-sm font-semibold text-slate-700">
                <span className="text-primary">Collected:</span>
                {conversationState.food_type && ` món ${conversationState.food_type}`}
                {conversationState.location && ` · khu vực ${conversationState.location}`}
                {conversationState.budget && ` · ${Number(conversationState.budget).toLocaleString("vi-VN")}đ/người`}
                {conversationState.occasion && ` · ${conversationState.occasion}`}
              </div>
            )}
            {warning && <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-700">{warning}</div>}
            {hasSearched && (
              <div className="grid gap-4">
                {visibleRecommendations.slice(0, 5).map((item) => (
                  <RecommendationCard
                    key={item.id}
                    item={item}
                    selected={selected?.id === item.id}
                    onSelect={setSelected}
                    onFeedback={runFeedback}
                  />
                ))}
              </div>
            )}
          </div>

          <form
            className="shrink-0 border-t border-border bg-white px-8 py-5"
            onSubmit={(event) => {
              event.preventDefault();
              runSearch();
            }}
          >
            <div className="flex items-center gap-3 rounded-[28px] border border-border bg-slate-50 p-2 shadow-sm transition focus-within:border-primary focus-within:bg-white focus-within:shadow-lg">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                className="h-12 min-w-0 flex-1 bg-transparent px-4 text-[15px] font-semibold text-slate-800 outline-none placeholder:text-slate-400"
                placeholder="Hôm nay bạn muốn ăn gì?"
              />
              <button disabled={loading} className="grid h-12 w-12 place-items-center rounded-2xl bg-primary text-white shadow-lg shadow-blue-500/25 transition hover:-translate-y-0.5 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60">
                <SendIcon />
              </button>
            </div>
          </form>
        </div>
      </section>

      <MapPanel recommendations={visibleRecommendations} selected={selected} onSelect={setSelected} />
    </main>
  );
}
