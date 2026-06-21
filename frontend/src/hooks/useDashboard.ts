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

async function fetchDashboardData() {
  const [assetList, dailyAll, pipelineStatus, healthStatus, alertList] =
    await Promise.all([
      getTrackedAssets(),
      getDailySentiment(undefined, SENTIMENT_DAYS),
      getPipelineStatus(),
      getHealth(),
      getAlerts(10),
    ])

  return { assetList, dailyAll, pipelineStatus, healthStatus, alertList }
}

export function useDashboard() {
  const [assets, setAssets] = useState<TrackedAsset[]>([])
  const [dailyBySymbol, setDailyBySymbol] = useState<
    Record<string, SentimentDaily | undefined>
  >({})
  const [sentimentHistoryBySymbol, setSentimentHistoryBySymbol] = useState<
    Record<string, SentimentDaily[]>
  >({})
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)
  const [articlesBySymbol, setArticlesBySymbol] = useState<
    Record<string, Article[]>
  >({})
  const [pipeline, setPipeline] = useState<PipelineStatus | null>(null)
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [connectingSince, setConnectingSince] = useState<number | null>(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)

  const applyDashboardData = useCallback(
    (data: Awaited<ReturnType<typeof fetchDashboardData>>) => {
      setError(null)
      setAssets(data.assetList)
      setDailyBySymbol(latestDailyBySymbol(data.dailyAll))
      setSentimentHistoryBySymbol(historyBySymbol(data.dailyAll))
      setPipeline(data.pipelineStatus)
      setHealth(data.healthStatus)
      setAlerts(data.alertList)
      setSelectedSymbol((prev) => {
        if (prev && data.assetList.some((a) => a.symbol === prev)) return prev
        return data.assetList[0]?.symbol ?? null
      })
    },
    [],
  )

  const reload = useCallback(async () => {
    setLoading(true)
    setConnectingSince(Date.now())
    setElapsedSeconds(0)
    setError(null)
    try {
      applyDashboardData(await fetchDashboardData())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load dashboard')
    } finally {
      setLoading(false)
      setConnectingSince(null)
    }
  }, [applyDashboardData])

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
    let cancelled = false

    fetchDashboardData()
      .then((data) => {
        if (!cancelled) applyDashboardData(data)
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load dashboard')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [applyDashboardData])

  useEffect(() => {
    if (!selectedSymbol) return

    let cancelled = false
    getArticles(selectedSymbol, MAX_ARTICLES_PER_TICKER)
      .then((data) => {
        if (!cancelled) {
          setArticlesBySymbol((prev) => ({ ...prev, [selectedSymbol]: data }))
        }
      })
      .catch(() => {
        if (!cancelled) {
          setArticlesBySymbol((prev) => ({ ...prev, [selectedSymbol]: [] }))
        }
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
  const articles = selectedSymbol
    ? (articlesBySymbol[selectedSymbol] ?? [])
    : []

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
    reload,
  }
}
