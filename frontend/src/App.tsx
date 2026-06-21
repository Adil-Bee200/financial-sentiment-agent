import { AssetHeader } from './components/AssetHeader'
import { ArticleList } from './components/ArticleList'
import { PipelinePanel } from './components/PipelinePanel'
import { SentimentMetrics } from './components/SentimentMetrics'
import { SentimentGauge } from './components/SentimentGauge'
import { Sidebar } from './components/Sidebar'
import {
  ApiConnectingBanner,
  ApiConnectingPanel,
  ErrorBanner,
} from './components/StatusStates'
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
    elapsedSeconds,
    reload,
  } = useDashboard()

  const hasData = assets.length > 0

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[#080b12] text-zinc-100">
      {loading && <ApiConnectingBanner elapsedSeconds={elapsedSeconds} />}
      {error && !loading && <ErrorBanner message={error} onRetry={reload} />}

      <div className="flex min-h-0 flex-1 overflow-hidden">
        <Sidebar
          assets={assets}
          dailyBySymbol={dailyBySymbol}
          selectedSymbol={selectedSymbol}
          onSelect={setSelectedSymbol}
          loading={loading && !hasData}
        />

        <main className="flex min-w-0 flex-1 flex-col overflow-y-auto">
          {loading && !hasData ? (
            <ApiConnectingPanel />
          ) : (
            <>
              <div className="shrink-0 border-b border-white/[0.08] px-6 py-8">
                <div className="mx-auto flex w-full max-w-6xl flex-col items-center text-center">
                  <AssetHeader asset={selectedAsset} centered />
                  <div className="mt-6 w-full max-w-2xl">
                    <SentimentGauge daily={selectedDaily} />
                  </div>
                </div>
                <div className="mx-auto w-full max-w-6xl">
                  <SentimentMetrics
                    history={sentimentHistory}
                    momentum={
                      sentimentHistory.at(-1)?.momentum ??
                      selectedDaily?.momentum
                    }
                    rolling7d={
                      sentimentHistory.at(-1)?.rolling_7d_sentiment ??
                      selectedDaily?.rolling_7d_sentiment
                    }
                  />
                </div>
              </div>

              <div className="px-6 py-5 pb-10">
                <ArticleList articles={articles} symbol={selectedSymbol} />
              </div>
            </>
          )}
        </main>

        <PipelinePanel
          status={pipeline}
          health={health}
          alerts={alerts}
          loading={loading && !hasData}
        />
      </div>
    </div>
  )
}

export default App
