import { useQuery } from "@tanstack/react-query";

import { listOrders } from "../shared/api/client";

interface Props {
  tgId: number;
  onOpenOrder: (id: number) => void;
}

export function OrdersPage({ tgId, onOpenOrder }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["orders", tgId],
    queryFn: () => listOrders(tgId),
  });

  if (isLoading) {
    return <div className="rounded-2xl bg-white p-4 shadow-sm">Loading orders...</div>;
  }

  if (error) {
    return <div className="rounded-2xl bg-white p-4 text-danger shadow-sm">{String(error)}</div>;
  }

  return (
    <div className="space-y-3">
      {(data?.items || []).map((order) => (
        <button
          key={order.id}
          className="w-full rounded-2xl bg-white p-4 text-left shadow-sm"
          onClick={() => onOpenOrder(order.id)}
        >
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">#{order.id}</h3>
            <span className="text-xs text-slate-500">{order.status}</span>
          </div>
          <p className="mt-1 text-sm text-slate-500">{order.direction}</p>
          <p className="mt-2 text-sm font-medium text-slate-700">
            {order.amount_from} {order.base_currency}
          </p>
        </button>
      ))}
      {!data?.items?.length && <div className="rounded-2xl bg-white p-4 text-slate-500 shadow-sm">No orders yet</div>}
    </div>
  );
}