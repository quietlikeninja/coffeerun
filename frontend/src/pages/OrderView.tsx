import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, type Order } from '@/api/client'
import { OrderSummary, orderToClipboardText } from '@/components/OrderSummary'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Copy, Share2, ArrowLeft, Check } from 'lucide-react'

export function OrderView() {
  const { id } = useParams<{ id: string }>()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [sharedCopied, setSharedCopied] = useState(false)

  useEffect(() => {
    if (!id) return
    api.get<Order>(`/orders/${id}`).then(setOrder).catch(() => {}).finally(() => setLoading(false))
  }, [id])

  const handleCopy = async () => {
    if (!order) return
    const text = orderToClipboardText(order.consolidated)
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleShare = async () => {
    if (!order) return
    const url = `${window.location.origin}/shared/${order.share_token}`
    await navigator.clipboard.writeText(url)
    setSharedCopied(true)
    setTimeout(() => setSharedCopied(false), 2000)
  }

  if (loading) {
    return <div className="flex justify-center py-12"><p>Loading...</p></div>
  }

  if (!order) {
    return <div className="text-center py-12"><p>Order not found.</p></div>
  }

  return (
    <div className="space-y-4">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back
      </Link>

      <Card>
        <CardHeader>
          <CardTitle>Order Summary</CardTitle>
          <p className="text-sm text-muted-foreground">
            {new Date(order.created_at).toLocaleDateString('en-AU', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        </CardHeader>
        <CardContent>
          <OrderSummary items={order.consolidated} />
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button onClick={handleCopy} variant="outline" className="flex-1">
          {copied ? <Check className="h-4 w-4 mr-1" /> : <Copy className="h-4 w-4 mr-1" />}
          {copied ? 'Copied!' : 'Copy order'}
        </Button>
        <Button onClick={handleShare} variant="outline" className="flex-1">
          {sharedCopied ? <Check className="h-4 w-4 mr-1" /> : <Share2 className="h-4 w-4 mr-1" />}
          {sharedCopied ? 'Link copied!' : 'Share link'}
        </Button>
      </div>

      {/* Individual items */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Individual Orders ({order.items.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {order.items.map((item) => (
              <div key={item.id} className="flex justify-between text-sm py-1 border-b last:border-0">
                <span className="font-medium">{item.colleague_name}</span>
                <span className="text-muted-foreground">
                  {item.size_abbreviation} {item.milk_option_name ? `${item.milk_option_name} ` : ''}
                  {item.drink_type_name}
                  {item.sugar > 0 ? `, ${item.sugar}s` : ''}
                  {item.notes ? ` (${item.notes})` : ''}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
