import { AssetHeader } from './components/AssetHeader'
import { ArticleList } from './components/ArticleList'
import { PipelinePanel } from './components/PipelinePanel'
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
    articles,
    pipeline,
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

      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <div className="border-b border-white/[0.08] px-6 py-5">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <AssetHeader asset={selectedAsset} />
            <div className="w-full max-w-xs shrink-0">
              <SentimentGauge
                score={selectedDaily?.avg_sentiment ?? null}
                articleCount={selectedDaily?.article_count ?? 0}
              />
            </div>
          </div>
        </div>

        <div className="flex min-h-0 flex-1 flex-col overflow-hidden px-6 py-5">
          <ArticleList articles={articles} symbol={selectedSymbol} />
        </div>
      </main>

      <PipelinePanel status={pipeline} />
    </div>
  )
}

export default App
