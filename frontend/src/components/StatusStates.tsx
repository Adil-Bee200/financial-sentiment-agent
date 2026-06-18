interface LoadingStateProps {
  message?: string
}

export function LoadingState({ message = 'Loading dashboard…' }: LoadingStateProps) {
  return (
    <div className="flex h-screen items-center justify-center bg-[#080b12]">
      <div className="text-center">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-emerald-500/30 border-t-emerald-400" />
        <p className="mt-4 text-sm text-zinc-500">{message}</p>
      </div>
    </div>
  )
}

interface ApiConnectingBannerProps {
  elapsedSeconds: number
}

export function ApiConnectingBanner({ elapsedSeconds }: ApiConnectingBannerProps) {
  const showColdStartHint = elapsedSeconds >= 3

  return (
    <div
      className="shrink-0 border-b border-amber-500/20 bg-amber-500/10 px-4 py-3"
      role="status"
      aria-live="polite"
    >
      <div className="mx-auto flex max-w-3xl items-start gap-3">
        <div className="mt-0.5 h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-amber-400/30 border-t-amber-300" />
        <div className="min-w-0 text-sm">
          <p className="font-medium text-amber-200">Connecting to the API…</p>
          {showColdStartHint ? (
            <p className="mt-1 text-xs leading-relaxed text-amber-200/80">
              The backend may take up to a minute to wake up after being idle.
              Please wait, your dashboard will load automatically.
            </p>
          ) : (
            <p className="mt-1 text-xs text-amber-200/70">Fetching live sentiment data.</p>
          )}
        </div>
      </div>
    </div>
  )
}

interface ApiConnectingPanelProps {
  title?: string
}

export function ApiConnectingPanel({
  title = 'Waiting for API',
}: ApiConnectingPanelProps) {
  return (
    <div className="flex flex-1 items-center justify-center px-6 py-16">
      <div className="max-w-md text-center">
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-emerald-500/20 border-t-emerald-400" />
        <p className="mt-5 text-base font-medium text-zinc-200">{title}</p>
        <p className="mt-2 text-sm leading-relaxed text-zinc-500">
          The dashboard shell is ready. We&apos;re waiting for the backend to
          respond, cold starts on the free tier can take around a minute.
        </p>
      </div>
    </div>
  )
}

interface ErrorBannerProps {
  message: string
  onRetry?: () => void
}

export function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <div className="shrink-0 border-b border-red-500/20 bg-red-500/10 px-4 py-3">
      <div className="mx-auto flex max-w-3xl items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-red-300">Could not load live data</p>
          <p className="mt-1 text-xs leading-relaxed text-red-200/80">{message}</p>
        </div>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="shrink-0 rounded-lg border border-red-400/20 bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-200 transition-colors hover:bg-red-500/20"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  )
}

interface ErrorStateProps {
  message: string
  onRetry?: () => void
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex h-screen items-center justify-center bg-[#080b12] px-6">
      <div className="max-w-md rounded-xl border border-red-500/20 bg-red-500/5 p-6 text-center">
        <p className="text-sm font-medium text-red-400">Failed to load data</p>
        <p className="mt-2 text-xs leading-relaxed text-zinc-500">{message}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 rounded-lg border border-white/[0.12] bg-white/[0.06] px-4 py-2 text-sm text-zinc-300 transition-colors hover:bg-white/[0.1]"
          >
            Retry
          </button>
        )}
        <p className="mt-4 text-[10px] text-zinc-600">
          Make sure the API is running at{' '}
          {import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}
        </p>
      </div>
    </div>
  )
}
