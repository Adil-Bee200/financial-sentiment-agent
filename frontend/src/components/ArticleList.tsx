import { useState } from 'react'
import type { Article } from '../api/types'
import { formatRelativeTime } from '../lib/format'
import {
  formatScore,
  getSentimentBg,
  getSentimentLabel,
} from '../lib/sentiment'
import { Card, SectionTitle } from './ui'

interface ArticleListProps {
  articles: Article[]
  symbol: string | null
}

export function ArticleList({ articles, symbol }: ArticleListProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <SectionTitle>
        Top relevant recent articles{symbol ? ` — ${symbol}` : ''}
      </SectionTitle>

      {articles.length === 0 ? (
        <Card className="mt-3 flex flex-1 items-center justify-center p-8">
          <p className="text-sm text-zinc-500">
            {symbol
              ? 'No articles found for this ticker yet.'
              : 'Select a ticker to view articles.'}
          </p>
        </Card>
      ) : (
        <ul className="mt-3 space-y-3 overflow-y-auto pr-1">
          {articles.map((article) => (
            <li key={`${article.article_id}-${article.symbol}`}>
              <ArticleCard article={article} />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function ArticleCard({ article }: { article: Article }) {
  const [expanded, setExpanded] = useState(false)
  const summary = article.summary ?? ''
  const truncated = summary.length > 180 && !expanded

  return (
    <Card className="p-4 transition-colors hover:border-white/[0.14]">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium leading-snug text-zinc-100 hover:text-emerald-400"
          >
            {article.title}
          </a>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-500">
            {article.source && <span>{article.source}</span>}
            <span>{formatRelativeTime(article.published_at)}</span>
          </div>
        </div>

        <div className="flex shrink-0 flex-col items-end gap-1.5">
          <span
            className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${getSentimentBg(article.sentiment_score)}`}
          >
            {getSentimentLabel(article.sentiment_score)}
          </span>
          <span className="font-mono text-xs text-zinc-400">
            {formatScore(article.sentiment_score)}
          </span>
        </div>
      </div>

      {summary && (
        <p className="mt-3 text-sm leading-relaxed text-zinc-400">
          {truncated ? `${summary.slice(0, 180)}…` : summary}
          {summary.length > 180 && (
            <button
              type="button"
              onClick={() => setExpanded((e) => !e)}
              className="ml-1 text-xs text-emerald-500 hover:text-emerald-400"
            >
              {expanded ? 'Show less' : 'Read more'}
            </button>
          )}
        </p>
      )}

      <div className="mt-3 flex items-center gap-2">
        <span className="text-[10px] font-medium uppercase tracking-wider text-zinc-600">
          Relevance
        </span>
        <div className="h-1.5 max-w-32 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
          <div
            className="h-full rounded-full bg-emerald-500/70"
            style={{ width: `${Math.round(article.confidence * 100)}%` }}
          />
        </div>
        <span className="font-mono text-xs text-zinc-500">
          {Math.round(article.confidence * 100)}%
        </span>
      </div>
    </Card>
  )
}
