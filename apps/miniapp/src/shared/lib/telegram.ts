declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData: string;
        initDataUnsafe?: Record<string, unknown>;
        ready: () => void;
        expand: () => void;
        close: () => void;
      };
    };
  }
}

export function getTelegramWebApp() {
  return window.Telegram?.WebApp;
}

function getTgDataFromLocation(): string {
  const search = new URLSearchParams(window.location.search);
  const fromSearch = search.get("tgWebAppData") || search.get("initData");
  if (fromSearch) {
    return fromSearch;
  }

  const hashRaw = window.location.hash.startsWith("#") ? window.location.hash.slice(1) : window.location.hash;
  const hash = new URLSearchParams(hashRaw);
  const fromHash = hash.get("tgWebAppData") || hash.get("initData");
  return fromHash || "";
}

export function getTelegramInitData(): string {
  const fromSdk = getTelegramWebApp()?.initData?.trim();
  if (fromSdk) {
    return fromSdk;
  }
  return getTgDataFromLocation().trim();
}