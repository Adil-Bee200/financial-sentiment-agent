import { useCallback, useEffect, useState } from 'react'
import {
  getAlerts,
  getArticles,
  getDailySentiment,
  getHealth,
  getPipelineStatus,
  getTrackedAssets,
} from '../api/client'
import type {
  Alert,
  Article,
  HealthStatus,
  PipelineStatus,
  SentimentDaily,
  TrackedAsset,
} from '../api/types'
import { historyBySymbol, latestDailyBySymbol } from '../lib/chart'

const SENTIMENT_DAYS = 7
const MAX_ARTICLES_PER_TICKER = 10

export function useDashboard() {
  const [assets, setAssets] = useState<TrackedAsset[]>([])
  const [dailyBySymbol, setDailyBySymbol] = useState<
    Record<string, SentimentDaily | undefined>
  >({})
  const [sentimentHistoryBySymbol, setSentimentHistoryBySymbol] = useState<
    Record<string, SentimentDaily[]>
  >({})
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)
  const [articles, setArticles] = useState<Article[]>([])
  const [pipeline, setPipeline] = useState<PipelineStatus | null>(null)
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [connectingSince, setConnectingSince] = useState<number | null>(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setConnectingSince(Date.now())
    setElapsedSeconds(0)
    try {
      const [assetList, dailyAll, pipelineStatus, healthStatus, alertList] =
        await Promise.all([
          getTrackedAssets(),
          getDailySentiment(undefined, SENTIMENT_DAYS),
          getPipelineStatus(),
          getHealth(),
          getAlerts(10),
        ])

      setAssets(assetList)
      setDailyBySymbol(latestDailyBySymbol(dailyAll))
      setSentimentHistoryBySymbol(historyBySymbol(dailyAll))
      setPipeline(pipelineStatus)
      setHealth(healthStatus)
      setAlerts(alertList)

      setSelectedSymbol((prev) => {
        if (prev && assetList.some((a) => a.symbol === prev)) return prev
        return assetList[0]?.symbol ?? null
      })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load dashboard')
    } finally {
      setLoading(false)
      setConnectingSince(null)
    }
  }, [])

  useEffect(() => {
    if (connectingSince == null) return

    const tick = () => {
      setElapsedSeconds(Math.floor((Date.now() - connectingSince) / 1000))
    }
    tick()
    const id = window.setInterval(tick, 1000)
    return () => window.clearInterval(id)
  }, [connectingSince])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (!selectedSymbol) {
      setArticles([])
      return
    }
    let cancelled = false
    getArticles(selectedSymbol, MAX_ARTICLES_PER_TICKER)
      .then((data) => {
        if (!cancelled) setArticles(data)
      })
      .catch(() => {
        if (!cancelled) setArticles([])
      })
    return () => {
      cancelled = true
    }
  }, [selectedSymbol])

  const selectedAsset = assets.find((a) => a.symbol === selectedSymbol) ?? null
  const sentimentHistory = selectedSymbol
    ? (sentimentHistoryBySymbol[selectedSymbol] ?? [])
    : []
  const selectedDaily =
    (selectedSymbol ? dailyBySymbol[selectedSymbol] : undefined) ??
    sentimentHistory.at(-1)

  return {
    assets,
    dailyBySymbol,
    selectedSymbol,
    setSelectedSymbol,
    selectedAsset,
    selectedDaily,
    sentimentHistory,
    articles,
    pipeline,
    health,
    alerts,
    loading,
    error,
    elapsedSeconds,
    reload: load,
  }
}
