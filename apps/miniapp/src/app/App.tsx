import { useState } from "react";

import { useTelegramInit } from "../features/auth/useTelegramInit";
import { ExchangePage } from "../pages/ExchangePage";
import { OrderDetailsPage } from "../pages/OrderDetailsPage";
import { OrdersPage } from "../pages/OrdersPage";
import { ProfilePage } from "../pages/ProfilePage";

type Tab = "exchange" | "orders" | "profile";

export function App() {
  const [tab, setTab] = useState<Tab>("exchange");
  const [activeOrderId, setActiveOrderId] = useState<number | null>(null);
  const debugMode = typeof window !== "undefined" && new URLSearchParams(window.location.search).has("debug");

  const { data: user, isLoading, error } = useTelegramInit();

  if (isLoading) {
    return <div className="mx-auto max-w-md p-4 text-sm text-slate-600">Initializing Mini App...</div>;
  }

  if (error || !user) {
    const dbg =
      typeof window !== "undefined"
        ? {
            href: window.location.href,
            search: window.location.search,
            hash: window.location.hash,
            hasTelegram: Boolean((window as any).Telegram),
            hasWebApp: Boolean((window as any).Telegram?.WebApp),
            initData: (window as any).Telegram?.WebApp?.initData,
          }
        : null;

    return (
      <div className="mx-auto max-w-md p-4">
        <div className="rounded-2xl bg-white p-4 text-sm text-danger shadow-sm">
          {String(error || "User is not initialized")}
        </div>
        {debugMode && dbg ? (
          <pre className="mt-3 overflow-x-auto rounded-xl bg-slate-100 p-3 text-[11px] text-slate-700">
            {JSON.stringify(dbg, null, 2)}
          </pre>
        ) : null}
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-full w-full max-w-md flex-col bg-slate-50">
      <main className="flex-1 p-4 pb-24">
        {activeOrderId ? (
          <OrderDetailsPage tgId={user.tg_id} orderId={activeOrderId} onBack={() => setActiveOrderId(null)} />
        ) : null}

        {!activeOrderId && tab === "exchange" ? <ExchangePage tgId={user.tg_id} /> : null}
        {!activeOrderId && tab === "orders" ? <OrdersPage tgId={user.tg_id} onOpenOrder={setActiveOrderId} /> : null}
        {!activeOrderId && tab === "profile" ? <ProfilePage user={user} /> : null}
      </main>

      {!activeOrderId && (
        <nav className="fixed bottom-0 left-0 right-0 mx-auto flex w-full max-w-md border-t border-slate-200 bg-white">
          <TabButton label="Exchange" active={tab === "exchange"} onClick={() => setTab("exchange")} />
          <TabButton label="Orders" active={tab === "orders"} onClick={() => setTab("orders")} />
          <TabButton label="Profile" active={tab === "profile"} onClick={() => setTab("profile")} />
        </nav>
      )}
    </div>
  );
}

function TabButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      className={`flex-1 px-4 py-3 text-sm font-medium ${active ? "text-primary" : "text-slate-500"}`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}
