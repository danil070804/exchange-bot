import type { UserOut } from "../shared/types/orders";

interface Props {
  user: UserOut;
}

export function ProfilePage({ user }: Props) {
  return (
    <div className="space-y-3">
      <div className="rounded-2xl bg-white p-4 shadow-sm">
        <h2 className="text-lg font-semibold">Profile</h2>
        <div className="mt-3 space-y-1 text-sm text-slate-600">
          <div>Telegram ID: {user.tg_id}</div>
          <div>Username: {user.username || "-"}</div>
          <div>Lang: {user.lang || "-"}</div>
          <div>Role: {user.role}</div>
        </div>
      </div>
      <div className="rounded-2xl bg-white p-4 text-sm text-slate-500 shadow-sm">
        Support is available via Telegram bot admin flow.
      </div>
    </div>
  );
}