import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, type Order } from '@/api/client'
import { OrderSummary } from '@/components/OrderSummary'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Coffee } from 'lucide-react'

export function SharedOrder() {
  const { shareToken } = useParams<{ shareToken: string }>()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState(new Date())

  const fetchOrder = () => {
    if (!shareToken) return
    api.get<Order>(`/orders/share/${shareToken}`)
      .then((data) => {
        setOrder(data)
        setLastRefresh(new Date())
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchOrder()
    const interval = setInterval(fetchOrder, 30000) // refresh every 30s
    return () => clearInterval(interval)
  }, [shareToken]) // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Coffee className="h-6 w-6 animate-pulse text-primary" />
      </div>
    )
  }

  if (!order) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Order not found.</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-md mx-auto space-y-4">
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Coffee className="h-5 w-5 text-primary" />
            <span className="font-bold text-lg text-primary">CoffeeRun</span>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Coffee Order</CardTitle>
            <p className="text-sm text-muted-foreground">
              {new Date(order.created_at).toLocaleDateString('en-AU', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </p>
          </CardHeader>
          <CardContent>
            <OrderSummary items={order.consolidated} />
          </CardContent>
        </Card>

        <p className="text-xs text-center text-muted-foreground">
          Last updated: {lastRefresh.toLocaleTimeString()}
          <br />
          Auto-refreshes every 30 seconds
        </p>
      </div>
    </div>
  )
}
