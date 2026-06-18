import type { Alert, Article, HealthStatus, PipelineStatus, SentimentDaily, TrackedAsset } from './types'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const API_TIMEOUT_MS = 90_000
const API_MAX_RETRIES = 2
const API_RETRY_DELAY_MS = 3_000

function isRetryableFetchError(error: unknown): boolean {
  if (error instanceof DOMException && error.name === 'AbortError') return true
  if (error instanceof TypeError) return true
  return false
}

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function get<T>(path: string): Promise<T> {
  let lastError: unknown

  for (let attempt = 0; attempt <= API_MAX_RETRIES; attempt++) {
    const controller = new AbortController()
    const timer = window.setTimeout(() => controller.abort(), API_TIMEOUT_MS)

    try {
      const res = await fetch(`${API}${path}`, { signal: controller.signal })
      if (!res.ok) throw new Error(await res.text())
      return (await res.json()) as T
    } catch (error) {
      lastError = error
      const canRetry = attempt < API_MAX_RETRIES && isRetryableFetchError(error)
      if (!canRetry) break
      await sleep(API_RETRY_DELAY_MS * (attempt + 1))
    } finally {
      window.clearTimeout(timer)
    }
  }

  if (lastError instanceof DOMException && lastError.name === 'AbortError') {
    throw new Error(
      'The API took too long to respond. It may still be waking up — try again in a moment.',
    )
  }
  if (lastError instanceof TypeError) {
    throw new Error(
      'Could not reach the API. If the server was idle, it may need up to a minute to cold start.',
    )
  }
  throw lastError instanceof Error ? lastError : new Error('Failed to reach the API')
}

export function getApiBaseUrl(): string {
  return API
}

export function getTrackedAssets(): Promise<TrackedAsset[]> {
  return get('/api/tracked-assets')
}

export function getArticles(symbol: string, limit = 20): Promise<Article[]> {
  const params = new URLSearchParams({ symbol, limit: String(limit) })
  return get(`/api/articles?${params}`)
}

export function getDailySentiment(
  symbol?: string,
  days = 30,
): Promise<SentimentDaily[]> {
  const params = new URLSearchParams({ days: String(days) })
  if (symbol) params.set('symbol', symbol)
  return get(`/api/sentiment/daily?${params}`)
}

export function getAlerts(limit = 100): Promise<Alert[]> {
  return get(`/api/alerts?limit=${limit}`)
}

export function getPipelineStatus(): Promise<PipelineStatus> {
  return get('/api/pipeline/status')
}

export function getHealth(): Promise<HealthStatus> {
  return get('/health')
}
