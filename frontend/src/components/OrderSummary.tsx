import { type ConsolidatedItem } from '@/api/client'

interface OrderSummaryProps {
  items: ConsolidatedItem[]
}

export function OrderSummary({ items }: OrderSummaryProps) {
  if (items.length === 0) {
    return <p className="text-muted-foreground text-center py-4">No items in this order.</p>
  }

  return (
    <div className="space-y-2">
      {items.map((item, i) => (
        <div key={i} className="font-mono text-sm py-1 border-b border-border last:border-0">
          {item.display_text}
        </div>
      ))}
    </div>
  )
}

export function orderToClipboardText(items: ConsolidatedItem[]): string {
  return items.map((item) => item.display_text).join('\n')
}
