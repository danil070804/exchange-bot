import { useQuery } from "@tanstack/react-query";

import { telegramInit } from "../../shared/api/client";
import { ensureTelegramSdkLoaded, getTelegramInitData, getTelegramWebApp } from "../../shared/lib/telegram";
import type { UserOut } from "../../shared/types/orders";

export function useTelegramInit() {
  return useQuery({
    queryKey: ["telegram-init"],
    queryFn: async () => {
      await ensureTelegramSdkLoaded();
      const webApp = getTelegramWebApp();
      const initData = getTelegramInitData();
      webApp?.ready();
      webApp?.expand();

      if (initData) {
        const payload = await telegramInit(initData);
        return payload.user;
      }

      const unsafeUser = webApp?.initDataUnsafe?.user;
      if (unsafeUser?.id) {
        const fallbackUser: UserOut = {
          id: 0,
          tg_id: Number(unsafeUser.id),
          username: unsafeUser.username ?? null,
          lang: unsafeUser.language_code ?? null,
          role: "client",
          is_blocked: false,
        };
        return fallbackUser;
      }

      throw new Error("Open this app from Telegram to initialize user session");
    },
    staleTime: 300000,
  });
}