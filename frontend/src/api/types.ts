export interface TrackedAsset {
  ticker_id: string
  symbol: string
  company_name: string | null
  sector: string | null
  created_at: string
}

export interface Article {
  article_id: string
  title: string
  source: string | null
  url: string
  published_at: string
  summary: string | null
  symbol: string
  sentiment_score: number | null
  confidence: number
}

export interface SentimentDaily {
  symbol: string
  date: string
  avg_sentiment: number
  article_count: number
  momentum: number | null
  std_div: number | null
}

export interface Alert {
  alert_id: string
  symbol: string
  trigger_reason: string
  sentiment_value: number
  created_at: string
}

export interface PipelineStatus {
  lastRun: string | null
  articlesFetched: number
  articlesAnalyzed: number
  estimatedLlmCost: number
  alertsTriggered: number
}
