export type OrderStatus =
  | "draft"
  | "pending_payment"
  | "payment_submitted"
  | "payment_review"
  | "processing"
  | "completed"
  | "cancelled"
  | "expired"
  | "rejected";

export interface OrderOut {
  id: number;
  public_id: string;
  status: OrderStatus;
  direction: string;
  base_currency: string;
  quote_currency: string;
  amount_from: string | null;
  amount_to: string | null;
  rate: string | null;
  fee_amount: string | null;
  network: string | null;
}

export interface OrderEvent {
  id: number;
  actor_type: string;
  actor_id: number | null;
  event_type: string;
  payload_json: Record<string, unknown> | null;
  created_at: string;
}

export interface OrderDetails extends OrderOut {
  created_at: string | null;
  updated_at: string | null;
  expires_at: string | null;
  events: OrderEvent[];
}

export interface UserOut {
  id: number;
  tg_id: number;
  username: string | null;
  lang: string | null;
  role: string;
  is_blocked: boolean;
}