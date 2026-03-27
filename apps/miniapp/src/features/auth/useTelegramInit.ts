import { useQuery } from "@tanstack/react-query";

import { telegramInit } from "../../shared/api/client";
import { getTelegramWebApp } from "../../shared/lib/telegram";

export function useTelegramInit() {
  return useQuery({
    queryKey: ["telegram-init"],
    queryFn: async () => {
      const webApp = getTelegramWebApp();
      const initData = webApp?.initData || "";
      if (!initData) {
        throw new Error("Open this app from Telegram to initialize user session");
      }
      webApp?.ready();
      webApp?.expand();
      const payload = await telegramInit(initData);
      return payload.user;
    },
    staleTime: 300000,
  });
}