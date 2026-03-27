import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getOrder, markPaid } from "../shared/api/client";

interface Props {
  tgId: number;
  orderId: number;
  onBack: () => void;
}

export function OrderDetailsPage({ tgId, orderId, onBack }: Props) {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["order", orderId, tgId],
    queryFn: () => getOrder(tgId, orderId),
  });

  const markPaidMutation = useMutation({
    mutationFn: () => markPaid(tgId, orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders", tgId] });
      queryClient.invalidateQueries({ queryKey: ["order", orderId, tgId] });
    },
  });

  if (isLoading) {
    return <div className="rounded-2xl bg-white p-4 shadow-sm">Loading order...</div>;
  }

  if (error || !data) {
    return <div className="rounded-2xl bg-white p-4 text-danger shadow-sm">{String(error || "Order not found")}</div>;
  }

  return (
    <div className="space-y-4">
      <button className="text-sm text-primary" onClick={onBack}>
        Back to orders
      </button>

      <div className="rounded-2xl bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold">Order #{data.id}</h2>
        <p className="mt-1 text-sm text-slate-500">{data.direction}</p>
        <div className="mt-3 text-sm">
          <div>Status: {data.status}</div>
          <div>Amount: {data.amount_from} {data.base_currency}</div>
          <div>Rate: {data.rate ?? "-"}</div>
        </div>
      </div>

      <div className="rounded-2xl bg-white p-4 shadow-sm">
        <h3 className="font-semibold">Timeline</h3>
        <div className="mt-2 space-y-2 text-sm">
          {data.events?.map((event) => (
            <div key={event.id} className="rounded-xl bg-slate-50 p-2">
              <div className="font-medium">{event.event_type}</div>
              <div className="text-slate-500">{new Date(event.created_at).toLocaleString()}</div>
            </div>
          ))}
          {!data.events?.length && <div className="text-slate-500">No events yet</div>}
        </div>
      </div>

      <button
        className="w-full rounded-xl bg-success px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
        disabled={markPaidMutation.isPending}
        onClick={() => markPaidMutation.mutate()}
      >
        {markPaidMutation.isPending ? "Submitting..." : "I paid"}
      </button>
    </div>
  );
}