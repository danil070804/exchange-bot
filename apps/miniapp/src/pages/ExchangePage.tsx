import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createMyOrder, quote, referenceConfig } from "../shared/api/client";

interface Props {
  tgId: number;
}

export function ExchangePage({ tgId }: Props) {
  const queryClient = useQueryClient();
  const { data: config } = useQuery({
    queryKey: ["reference-config"],
    queryFn: referenceConfig,
  });

  const [direction, setDirection] = useState("CARD_UAH_TO_CRYPTO_USDT");
  const [amount, setAmount] = useState(1000);

  const quoteQuery = useQuery({
    queryKey: ["quote", direction, amount],
    queryFn: () =>
      quote({
        direction,
        amount_from: amount,
        base_currency: "UAH",
        quote_currency: "USDT",
      }),
    enabled: amount > 0,
  });

  const createOrderMutation = useMutation({
    mutationFn: () =>
      createMyOrder(tgId, {
        direction,
        amount_from: amount,
        base_currency: "UAH",
        quote_currency: "USDT",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders", tgId] });
    },
  });

  const amountTo = useMemo(() => quoteQuery.data?.amount_to ?? "-", [quoteQuery.data]);

  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Exchange</h2>
        <p className="mt-1 text-sm text-slate-500">Create a new deal from Mini App.</p>
      </div>

      <div className="rounded-2xl bg-white p-4 shadow-sm">
        <label className="mb-2 block text-sm font-medium">Direction</label>
        <select
          className="w-full rounded-xl border border-slate-200 p-3 text-sm"
          value={direction}
          onChange={(event) => setDirection(event.target.value)}
        >
          {(config?.directions || []).map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <label className="mb-2 mt-4 block text-sm font-medium">Amount (UAH)</label>
        <input
          className="w-full rounded-xl border border-slate-200 p-3 text-sm"
          type="number"
          min={1}
          value={amount}
          onChange={(event) => setAmount(Number(event.target.value || 0))}
        />

        <div className="mt-4 rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
          <div>Rate: {quoteQuery.data?.rate ?? "-"}</div>
          <div>You get: {amountTo} USDT</div>
        </div>

        <button
          className="mt-4 w-full rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
          disabled={createOrderMutation.isPending || amount <= 0}
          onClick={() => createOrderMutation.mutate()}
        >
          {createOrderMutation.isPending ? "Creating..." : "Create order"}
        </button>

        {createOrderMutation.isSuccess && (
          <p className="mt-3 text-sm text-success">Order #{createOrderMutation.data.id} created</p>
        )}
        {createOrderMutation.error && (
          <p className="mt-3 text-sm text-danger">{String(createOrderMutation.error)}</p>
        )}
      </div>
    </div>
  );
}