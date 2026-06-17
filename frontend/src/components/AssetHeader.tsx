import type { TrackedAsset } from '../api/types'

interface AssetHeaderProps {
  asset: TrackedAsset | null
  centered?: boolean
}

export function AssetHeader({ asset, centered = false }: AssetHeaderProps) {
  const align = centered ? 'text-center' : ''

  if (!asset) {
    return (
      <div className={`px-1 py-2 ${align}`}>
        <p className="text-zinc-500">Select an asset</p>
      </div>
    )
  }

  return (
    <div className={`px-1 py-2 ${align}`}>
      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        Selected asset
      </p>
      <div
        className={`mt-1 flex items-baseline gap-3 ${centered ? 'justify-center' : ''}`}
      >
        <h1 className="font-mono text-3xl font-bold tracking-tight text-zinc-50">
          {asset.symbol}
        </h1>
        {asset.company_name && (
          <span className="text-lg text-zinc-300">{asset.company_name}</span>
        )}
      </div>
      {asset.sector && (
        <p className="mt-1 text-sm text-zinc-500">{asset.sector}</p>
      )}
    </div>
  )
}
