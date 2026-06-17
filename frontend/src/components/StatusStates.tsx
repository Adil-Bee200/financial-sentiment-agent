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
