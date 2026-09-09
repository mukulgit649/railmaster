import React from 'react'

export default function Panel({
  title,
  action,
  children,
  className = '',
}: {
  title?: string
  action?: React.ReactNode
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`bg-white border border-rail-border ${className}`}>
      {title && (
        <div className="flex items-center justify-between border-b border-rail-border px-4 py-2">
          <h2 className="text-xs font-bold uppercase tracking-wide text-gray-700">{title}</h2>
          {action}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  )
}
