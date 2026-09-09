import { OptimizeResult } from '../types'
import Panel from './Panel'

export default function ExplanationPanel({ result }: { result: OptimizeResult }) {
  const explanation = result.explanation ?? []

  return (
    <Panel title="Why This Plan?" className="mb-5">
      <ol className="space-y-1.5 text-sm text-gray-800 list-decimal list-inside">
        {explanation.map((line, i) => (
          <li key={i}>{line}</li>
        ))}
      </ol>

      <div className="mt-4 pt-4 border-t border-rail-border grid grid-cols-3 gap-4">
        <ScoreBox label="Optimization Score" value={result.optimization_score} highlight />
        <ScoreBox label="Alternative — Manual Approach" value={result.manual_baseline?.score} />
        <ScoreBox label="Alternative — Other Subsection" value={result.alternative_score ?? undefined} />
      </div>
    </Panel>
  )
}

function ScoreBox({ label, value, highlight }: { label: string; value?: number; highlight?: boolean }) {
  return (
    <div className="border border-rail-border p-3 text-center">
      <div className={`text-2xl font-bold ${highlight ? 'text-rail-blue' : 'text-gray-700'}`}>
        {value !== undefined ? value.toFixed(1) : '—'}
      </div>
      <div className="text-[11px] text-gray-500 mt-1">{label}</div>
    </div>
  )
}
