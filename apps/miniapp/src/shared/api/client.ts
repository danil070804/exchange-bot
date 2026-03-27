import type { OrderDetails, OrderOut, UserOut } from "../types/orders";

const fromEnv = import.meta.env.VITE_BACKEND_URL?.trim();
const API_BASE = (fromEnv || window.location.origin).replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function telegramInit(initData: string): Promise<{ user: UserOut }> {
  return request("/api/v1/auth/telegram/init", {
    method: "POST",
    body: JSON.stringify({ init_data: initData }),
  });
}

export async function referenceConfig(): Promise<{ directions: string[] }> {
  return request("/api/v1/reference/config");
}

export async function quote(payload: {
  base_currency: string;
  quote_currency: string;
  direction: string;
  amount_from: number;
}): Promise<{ amount_to: string; rate: string }> {
  const params = new URLSearchParams({
    base_currency: payload.base_currency,
    quote_currency: payload.quote_currency,
    direction: payload.direction,
    amount_from: String(payload.amount_from),
  });
  return request(`/api/v1/rates/quote?${params.toString()}`);
}

export async function createMyOrder(
  tgId: number,
  payload: {
    direction: string;
    base_currency: string;
    quote_currency: string;
    amount_from: number;
  }
): Promise<OrderOut> {
  return request("/api/v1/orders/me", {
    method: "POST",
    headers: {
      "X-Telegram-Id": String(tgId),
    },
    body: JSON.stringify(payload),
  });
}

export async function listOrders(tgId: number): Promise<{ items: OrderOut[]; total: number }> {
  return request("/api/v1/orders?limit=20", {
    headers: {
      "X-Telegram-Id": String(tgId),
    },
  });
}

export async function getOrder(tgId: number, orderId: number): Promise<OrderDetails> {
  return request(`/api/v1/orders/${orderId}`, {
    headers: {
      "X-Telegram-Id": String(tgId),
    },
  });
}

export async function markPaid(tgId: number, orderId: number): Promise<OrderDetails> {
  return request(`/api/v1/orders/${orderId}/mark-paid`, {
    method: "POST",
    headers: {
      "X-Telegram-Id": String(tgId),
    },
    body: JSON.stringify({}),
  });
}