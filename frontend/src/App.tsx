import { AssetHeader } from './components/AssetHeader'
import { ArticleList } from './components/ArticleList'
import { PipelinePanel } from './components/PipelinePanel'
import { SentimentMetrics } from './components/SentimentMetrics'
import { SentimentGauge } from './components/SentimentGauge'
import { Sidebar } from './components/Sidebar'
import { ErrorState, LoadingState } from './components/StatusStates'
import { useDashboard } from './hooks/useDashboard'

function App() {
  const {
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
    reload,
  } = useDashboard()

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} onRetry={reload} />

  return (
    <div className="flex h-screen overflow-hidden bg-[#080b12] text-zinc-100">
      <Sidebar
        assets={assets}
        dailyBySymbol={dailyBySymbol}
        selectedSymbol={selectedSymbol}
        onSelect={setSelectedSymbol}
      />

      <main className="flex min-w-0 flex-1 flex-col overflow-y-auto">
        <div className="shrink-0 border-b border-white/[0.08] px-6 py-8">
          <div className="mx-auto flex w-full max-w-6xl flex-col items-center text-center">
            <AssetHeader asset={selectedAsset} centered />
            <div className="mt-6 w-full max-w-2xl">
              <SentimentGauge
                score={selectedDaily?.avg_sentiment ?? null}
                articleCount={selectedDaily?.article_count ?? 0}
                asOfDate={selectedDaily?.date}
              />
            </div>
            <div className="w-full">
              <SentimentMetrics
                history={sentimentHistory}
                momentum={
                  sentimentHistory.at(-1)?.momentum ?? selectedDaily?.momentum
                }
              />
            </div>
          </div>
        </div>

        <div className="px-6 py-5 pb-10">
          <ArticleList articles={articles} symbol={selectedSymbol} />
        </div>
      </main>

      <PipelinePanel status={pipeline} health={health} alerts={alerts} />
    </div>
  )
}

export default App
