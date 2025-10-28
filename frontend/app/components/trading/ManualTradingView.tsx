import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { toast } from 'react-hot-toast'
import { 
  placeOKXOrder, 
  getOKXBalance, 
  getOKXPositions, 
  getOKXOpenOrders,
  type OKXBalance,
  type OKXPosition,
  type OKXOrder
} from '@/lib/api'
import { RefreshCcw, TrendingUp, TrendingDown, DollarSign, Wallet } from 'lucide-react'

// Popular trading pairs
const TRADING_PAIRS = [
  'BTC-USDT-SWAP',
  'ETH-USDT-SWAP',
  'SOL-USDT-SWAP',
  'BNB-USDT-SWAP',
  'XRP-USDT-SWAP',
  'DOGE-USDT-SWAP',
  'ADA-USDT-SWAP',
  'AVAX-USDT-SWAP',
  'MATIC-USDT-SWAP',
  'LINK-USDT-SWAP'
]

export default function ManualTradingView() {
  // Trading form state
  const [symbol, setSymbol] = useState('BTC-USDT-SWAP')
  const [side, setSide] = useState<'buy' | 'sell'>('buy')
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market')
  const [amount, setAmount] = useState('')
  const [price, setPrice] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Data state
  const [balance, setBalance] = useState<OKXBalance[]>([])
  const [positions, setPositions] = useState<OKXPosition[]>([])
  const [openOrders, setOpenOrders] = useState<OKXOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchAllData = async () => {
    try {
      setRefreshing(true)
      const [balanceRes, positionsRes, ordersRes] = await Promise.all([
        getOKXBalance(),
        getOKXPositions(),
        getOKXOpenOrders()
      ])

      if (balanceRes.success) setBalance(balanceRes.assets)
      if (positionsRes.success) setPositions(positionsRes.positions)
      if (ordersRes.success) setOpenOrders(ordersRes.orders)
    } catch (error) {
      console.error('Failed to fetch data:', error)
      toast.error('Failed to load account data')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchAllData()
  }, [])

  const handleSubmitOrder = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Please enter a valid amount')
      return
    }

    if (orderType === 'limit' && (!price || parseFloat(price) <= 0)) {
      toast.error('Please enter a valid price for limit order')
      return
    }

    setIsSubmitting(true)

    try {
      const result = await placeOKXOrder({
        symbol,
        side,
        quantity: parseFloat(amount),  // 使用quantity字段名
        orderType,
        price: orderType === 'limit' ? parseFloat(price) : undefined
      })

      if (result.success) {
        toast.success(`${side.toUpperCase()} order placed successfully!`)
        // Clear form
        setAmount('')
        setPrice('')
        // Refresh data
        fetchAllData()
      } else {
        toast.error(result.error || 'Failed to place order')
      }
    } catch (error: any) {
      console.error('Order error:', error)
      toast.error(error.message || 'Failed to place order')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRefresh = () => {
    fetchAllData()
    toast.success('Refreshing data...')
  }

  // Calculate total USDT balance
  const totalUSDT = balance
    .filter(b => b.currency === 'USDT')
    .reduce((sum, b) => sum + parseFloat(String(b.free || 0)), 0)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-muted-foreground">Loading trading interface...</div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold">Manual Trading</h2>
          <p className="text-muted-foreground">Trade on OKX with your account</p>
        </div>
        <Button onClick={handleRefresh} disabled={refreshing} variant="outline">
          <RefreshCcw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Balance Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Available Balance</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalUSDT.toFixed(2)} USDT</div>
            <p className="text-xs text-muted-foreground">Available for trading</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Positions</CardTitle>
            <Wallet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{positions.length}</div>
            <p className="text-xs text-muted-foreground">Active positions</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Orders</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{openOrders.length}</div>
            <p className="text-xs text-muted-foreground">Pending orders</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Trading Form */}
        <Card>
          <CardHeader>
            <CardTitle>Place Order</CardTitle>
            <CardDescription>Execute trades on OKX exchange</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmitOrder} className="space-y-4">
              {/* Trading Pair */}
              <div className="space-y-2">
                <Label>Trading Pair</Label>
                <Select value={symbol} onValueChange={setSymbol}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TRADING_PAIRS.map(pair => (
                      <SelectItem key={pair} value={pair}>
                        {pair}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Side Selection */}
              <div className="space-y-2">
                <Label>Side</Label>
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    type="button"
                    variant={side === 'buy' ? 'default' : 'outline'}
                    onClick={() => setSide('buy')}
                    className={side === 'buy' ? 'bg-green-600 hover:bg-green-700' : ''}
                  >
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Buy / Long
                  </Button>
                  <Button
                    type="button"
                    variant={side === 'sell' ? 'default' : 'outline'}
                    onClick={() => setSide('sell')}
                    className={side === 'sell' ? 'bg-red-600 hover:bg-red-700' : ''}
                  >
                    <TrendingDown className="h-4 w-4 mr-2" />
                    Sell / Short
                  </Button>
                </div>
              </div>

              {/* Order Type */}
              <div className="space-y-2">
                <Label>Order Type</Label>
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    type="button"
                    variant={orderType === 'market' ? 'default' : 'outline'}
                    onClick={() => setOrderType('market')}
                  >
                    Market
                  </Button>
                  <Button
                    type="button"
                    variant={orderType === 'limit' ? 'default' : 'outline'}
                    onClick={() => setOrderType('limit')}
                  >
                    Limit
                  </Button>
                </div>
              </div>

              {/* Amount */}
              <div className="space-y-2">
                <Label htmlFor="amount">Amount (Contracts)</Label>
                <Input
                  id="amount"
                  type="number"
                  step="1"
                  min="1"
                  placeholder="Enter amount"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Minimum: 1 contract
                </p>
              </div>

              {/* Price (for limit orders) */}
              {orderType === 'limit' && (
                <div className="space-y-2">
                  <Label htmlFor="price">Limit Price (USDT)</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="Enter price"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    required
                  />
                </div>
              )}

              {/* Submit Button */}
              <Button 
                type="submit" 
                className="w-full"
                disabled={isSubmitting}
                variant={side === 'buy' ? 'default' : 'destructive'}
              >
                {isSubmitting ? 'Placing Order...' : `${side.toUpperCase()} ${symbol.split('-')[0]}`}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Positions & Orders */}
        <Card>
          <CardHeader>
            <CardTitle>Account Status</CardTitle>
            <CardDescription>Your current positions and orders</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="positions" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="positions">Positions ({positions.length})</TabsTrigger>
                <TabsTrigger value="orders">Orders ({openOrders.length})</TabsTrigger>
              </TabsList>

              <TabsContent value="positions" className="space-y-4">
                {positions.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No open positions
                  </div>
                ) : (
                  <div className="space-y-2">
                    {positions.slice(0, 5).map((pos, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <div className="font-medium">{pos.symbol}</div>
                          <div className="text-sm text-muted-foreground">
                            {pos.side} • {pos.contracts} contracts
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-medium">
                            {pos.unrealizedPnl >= 0 ? '+' : ''}
                            {pos.unrealizedPnl.toFixed(2)} USDT
                          </div>
                          <Badge variant={pos.unrealizedPnl >= 0 ? 'default' : 'destructive'}>
                            {pos.percentage.toFixed(2)}%
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="orders" className="space-y-4">
                {openOrders.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No pending orders
                  </div>
                ) : (
                  <div className="space-y-2">
                    {openOrders.slice(0, 5).map((order, idx) => (
                      <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <div className="font-medium">{order.symbol}</div>
                          <div className="text-sm text-muted-foreground">
                            {order.side} • {order.amount} @ {order.price || 'Market'}
                          </div>
                        </div>
                        <Badge>{order.status}</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
