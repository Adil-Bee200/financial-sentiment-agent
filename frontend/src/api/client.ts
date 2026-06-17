import type { Alert, Article, SentimentDaily, TrackedAsset } from './types'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export function getTrackedAssets(): Promise<TrackedAsset[]> {
  return get('/api/tracked-assets')
}

export function getArticles(symbol?: string, limit = 20): Promise<Article[]> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (symbol) params.set('symbol', symbol)
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
