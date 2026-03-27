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

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function ensureTelegramSdkLoaded(): Promise<void> {
  if (window.Telegram?.WebApp) {
    return;
  }

  const scriptId = "telegram-webapp-sdk";
  let script = document.getElementById(scriptId) as HTMLScriptElement | null;

  if (!script) {
    script = document.createElement("script");
    script.id = scriptId;
    script.src = "https://telegram.org/js/telegram-web-app.js";
    script.async = true;
    document.head.appendChild(script);
  }

  for (let i = 0; i < 20; i += 1) {
    if (window.Telegram?.WebApp) {
      return;
    }
    await wait(100);
  }
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