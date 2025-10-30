import { useState } from 'react'
import { toast } from 'react-hot-toast'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const CRYPTO_SYMBOLS = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE', 'ADA', 'MATIC', 'DOT', 'AVAX']

interface OKXTradingPanelProps {
  onRefresh?: () => void
}

export default function OKXTradingPanel({ onRefresh }: OKXTradingPanelProps) {
  const [symbol, setSymbol] = useState('BTC')
  const [side, setSide] = useState<'buy' | 'sell'>('buy')
  const [quantity, setQuantity] = useState<string>('0.001')
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market')
  const [price, setPrice] = useState<string>('')
  const [posSide, setPosSide] = useState<'long' | 'short'>('long')
  const [reduceOnly, setReduceOnly] = useState(false)
  const [loading, setLoading] = useState(false)

  const handlePlaceOrder = async () => {
    if (!quantity || parseFloat(quantity) <= 0) {
      toast.error('Please enter a valid quantity')
      return
    }

    if (orderType === 'limit' && (!price || parseFloat(price) <= 0)) {
      toast.error('Please enter a valid price for limit order')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/okx-account/order?account_id=1', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: `${symbol}-USDT-SWAP`,  // OKX永续合约格式
          side,
          order_type: orderType,
          quantity: parseFloat(quantity),
          price: orderType === 'limit' ? parseFloat(price) : undefined,
          pos_side: posSide,
          td_mode: 'cross',
          reduce_only: reduceOnly
        })
      })

      const data = await response.json()
      
      if (data.success) {
        toast.success(`Order placed successfully: ${data.order_id}`)
        // 清空表单
        setQuantity('0.001')
        setPrice('')
        // 刷新数据
        if (onRefresh) {
          setTimeout(onRefresh, 1000)
        }
      } else {
        toast.error(`Failed to place order: ${data.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Failed to place order:', error)
      toast.error('Failed to place order')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>🔴 OKX Real Trading</CardTitle>
        <CardDescription>
          Place orders directly on OKX exchange. Be careful - this is real money!
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Symbol Selection */}
        <div className="space-y-2">
          <Label>Symbol</Label>
          <div className="flex flex-wrap gap-2">
            {CRYPTO_SYMBOLS.map(s => (
              <Button
                key={s}
                variant={symbol === s ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSymbol(s)}
              >
                {s}
              </Button>
            ))}
          </div>
        </div>

        {/* Order Type */}
        <div className="space-y-2">
          <Label>Order Type</Label>
          <div className="flex gap-2">
            <Button
              variant={orderType === 'market' ? 'default' : 'outline'}
              onClick={() => setOrderType('market')}
              className="flex-1"
            >
              Market
            </Button>
            <Button
              variant={orderType === 'limit' ? 'default' : 'outline'}
              onClick={() => setOrderType('limit')}
              className="flex-1"
            >
              Limit
            </Button>
          </div>
        </div>

        {/* Price (for limit orders) */}
        {orderType === 'limit' && (
          <div className="space-y-2">
            <Label htmlFor="price">Price (USDT)</Label>
            <Input
              id="price"
              type="number"
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="Enter price"
            />
          </div>
        )}

        {/* Quantity */}
        <div className="space-y-2">
          <Label htmlFor="quantity">Quantity</Label>
          <Input
            id="quantity"
            type="number"
            step="0.001"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="Enter quantity"
          />
        </div>

        {/* Position Side (OKX双向持仓) */}
        <div className="space-y-2">
          <Label>Position Side (OKX Dual-Position Mode)</Label>
          <div className="flex gap-2">
            <Button
              variant={posSide === 'long' ? 'default' : 'outline'}
              onClick={() => setPosSide('long')}
              className="flex-1"
            >
              Long (多仓)
            </Button>
            <Button
              variant={posSide === 'short' ? 'default' : 'outline'}
              onClick={() => setPosSide('short')}
              className="flex-1"
            >
              Short (空仓)
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            选择持仓方向：Long(开多/平多) 或 Short(开空/平空)
          </p>
        </div>

        {/* Reduce Only */}
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="reduceOnly"
            checked={reduceOnly}
            onChange={(e) => setReduceOnly(e.target.checked)}
            className="h-4 w-4"
          />
          <Label htmlFor="reduceOnly" className="cursor-pointer">
            Reduce Only (只平仓，不开新仓)
          </Label>
        </div>

        {/* Side Selection */}
        <div className="flex gap-2">
          <Button
            variant={side === 'buy' ? 'default' : 'outline'}
            onClick={() => setSide('buy')}
            className="flex-1 bg-green-600 hover:bg-green-700"
            disabled={loading}
          >
            BUY
          </Button>
          <Button
            variant={side === 'sell' ? 'default' : 'outline'}
            onClick={() => setSide('sell')}
            className="flex-1 bg-red-600 hover:bg-red-700"
            disabled={loading}
          >
            SELL
          </Button>
        </div>

        {/* Place Order Button */}
        <Button
          onClick={handlePlaceOrder}
          disabled={loading}
          className="w-full"
          size="lg"
        >
          {loading ? 'Placing Order...' : 'Place Order on OKX'}
        </Button>

        {/* Warning */}
        <div className="text-sm text-muted-foreground bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-md">
          ⚠️ <strong>Warning:</strong> Orders will be executed on OKX real exchange. 
          Make sure you understand the risks involved in cryptocurrency trading.
        </div>
      </CardContent>
    </Card>
  )
}
