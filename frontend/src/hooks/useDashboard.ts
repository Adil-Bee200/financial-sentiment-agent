import { useCallback, useEffect, useState } from 'react'
import {
  getArticles,
  getDailySentiment,
  getPipelineStatus,
  getTrackedAssets,
} from '../api/client'
import type {
  Article,
  PipelineStatus,
  SentimentDaily,
  TrackedAsset,
} from '../api/types'
import { latestDailyBySymbol, mergeDailyBySymbol, sortByDateAsc } from '../lib/chart'

export function useDashboard() {
  const [assets, setAssets] = useState<TrackedAsset[]>([])
  const [dailyBySymbol, setDailyBySymbol] = useState<
    Record<string, SentimentDaily | undefined>
  >({})
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)
  const [articles, setArticles] = useState<Article[]>([])
  const [sentimentHistory, setSentimentHistory] = useState<SentimentDaily[]>([])
  const [pipeline, setPipeline] = useState<PipelineStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [assetList, dailyAll, pipelineStatus] = await Promise.all([
        getTrackedAssets(),
        getDailySentiment(undefined, 30),
        getPipelineStatus(),
      ])

      setAssets(assetList)
      setDailyBySymbol(latestDailyBySymbol(dailyAll))
      setPipeline(pipelineStatus)

      setSelectedSymbol((prev) => {
        if (prev && assetList.some((a) => a.symbol === prev)) return prev
        return assetList[0]?.symbol ?? null
      })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (!selectedSymbol) {
      setArticles([])
      setSentimentHistory([])
      return
    }
    let cancelled = false
    Promise.all([
      getArticles(selectedSymbol, 15),
      getDailySentiment(selectedSymbol, 7),
    ])
      .then(([articleData, dailyData]) => {
        if (!cancelled) {
          setArticles(articleData)
          setSentimentHistory(sortByDateAsc(dailyData))
          setDailyBySymbol((prev) => mergeDailyBySymbol(prev, dailyData))
        }
      })
      .catch(() => {
        if (!cancelled) {
          setArticles([])
          setSentimentHistory([])
        }
      })
    return () => {
      cancelled = true
    }
  }, [selectedSymbol])

  const selectedAsset = assets.find((a) => a.symbol === selectedSymbol) ?? null
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
    loading,
    error,
    reload: load,
  }
}
