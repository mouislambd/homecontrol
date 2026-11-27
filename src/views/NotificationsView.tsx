import { useState } from 'react'
import {
  clearNotifications,
  deleteNotification,
  fetchNotifications,
  markNotificationRead,
} from '../api/notifications'
import { errorMessage } from '../api/client'
import { Notice } from '../components/Notice'
import { StatePanel } from '../components/StatePanel'
import { useFetch } from '../hooks/useFetch'
import type { AppNotification } from '../types'

interface NotificationsViewProps {
  revision: number
}

const levelStyles: Record<string, string> = {
  info: 'bg-indigo-400/10 text-indigo-200',
  success: 'bg-emerald-400/10 text-emerald-200',
  warning: 'bg-amber-400/10 text-amber-200',
  error: 'bg-rose-400/10 text-rose-200',
}

export function NotificationsView({ revision }: NotificationsViewProps) {
  const { data, loading, error, reload } = useFetch(fetchNotifications, revision)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const notifications = data?.notifications ?? []
  const unread = data?.unread_count ?? 0

  const runAction = async (operation: () => Promise<void>) => {
    setBusy(true)
    setNotice(null)
    try {
      await operation()
      await reload()
    } catch (err) {
      setNotice(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="mt-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-white">
            Notifications
          </h2>
          <p className="mt-1 text-sm text-slate-400">
            {unread} unread message{unread === 1 ? '' : 's'}
          </p>
        </div>
        <button
          type="button"
          disabled={busy || notifications.length === 0}
          onClick={() =>
            void runAction(async () => {
              await clearNotifications()
            })
          }
          className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/5 disabled:opacity-50"
        >
          Clear all
        </button>
      </div>

      <div className="mt-6">
        <Notice message={notice} onDismiss={() => setNotice(null)} />
        <StatePanel
          loading={loading}
          error={error}
          empty={notifications.length === 0}
          emptyLabel="No notifications. Device activity will appear here."
          onRetry={() => void reload()}
        >
          <div className="overflow-hidden rounded-3xl border border-white/[0.07] bg-slate-900/40 backdrop-blur-xl">
            {notifications.map((item: AppNotification) => (
              <div
                key={item.id}
                className={`flex flex-wrap items-center justify-between gap-3 border-b border-white/5 px-5 py-4 last:border-0 ${
                  item.read ? 'opacity-60' : ''
                }`}
              >
                <div>
                  <p className="text-sm text-slate-200">{item.message}</p>
                  <p className="mt-1 text-[11px] text-slate-500">
                    {new Date(item.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded-full px-2.5 py-1 text-[11px] ${
                      levelStyles[item.level] ?? levelStyles.info
                    }`}
                  >
                    {item.level}
                  </span>
                  {!item.read && (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        void runAction(async () => {
                          await markNotificationRead(item.id)
                        })
                      }
                      className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:bg-white/5 disabled:opacity-50"
                    >
                      Mark read
                    </button>
                  )}
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      void runAction(async () => {
                        await deleteNotification(item.id)
                      })
                    }
                    className="rounded-full border border-rose-400/20 px-3 py-1.5 text-xs text-rose-200 transition hover:bg-rose-400/10 disabled:opacity-50"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </StatePanel>
      </div>
    </section>
  )
}
