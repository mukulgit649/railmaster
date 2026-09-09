type Tone = 'critical' | 'warning' | 'medium' | 'success' | 'neutral' | 'info'

const toneClasses: Record<Tone, string> = {
  critical: 'bg-red-50 text-rail-red border-red-200',
  warning: 'bg-yellow-50 text-rail-yellow border-yellow-200',
  medium: 'bg-orange-50 text-orange-700 border-orange-200',
  success: 'bg-green-50 text-rail-green border-green-200',
  neutral: 'bg-gray-100 text-gray-700 border-gray-300',
  info: 'bg-blue-50 text-rail-blue border-blue-200',
}

export default function StatusBadge({ text, tone }: { text: string; tone: Tone }) {
  return (
    <span
      className={`inline-block px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide border ${toneClasses[tone]}`}
    >
      {text}
    </span>
  )
}

export function priorityTone(priority: string): Tone {
  switch (priority) {
    case 'CRITICAL':
      return 'critical'
    case 'HIGH':
      return 'warning'
    case 'MEDIUM':
      return 'medium'
    case 'LOW':
      return 'neutral'
    default:
      return 'neutral'
  }
}

export function trainPriorityTone(priority: string): Tone {
  return priority === 'HIGH' ? 'warning' : 'neutral'
}

/** DCI (0-100, from the priority model) -> a CRITICAL/HIGH/MEDIUM/LOW label. */
export function dciToPriority(dci: number): 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' {
  if (dci >= 70) return 'CRITICAL'
  if (dci >= 50) return 'HIGH'
  if (dci >= 32) return 'MEDIUM'
  return 'LOW'
}
