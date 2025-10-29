import { useEffect, useState } from 'react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { toast } from 'react-hot-toast'
import { 
  getOKXBalance, 
  getOKXPositions, 
  getOKXOpenOrders, 
  getOKXOrderHistory,
  getOKXTrades,
  getOKXAccountSummary,
  type OKXBalance,
  type OKXPosition,
  type OKXOrder,
  type OKXTrade,
  type OKXAccountSummary
} from '@/lib/api'
import { RefreshCcw, TrendingUp, TrendingDown, DollarSign, Briefcase, ShoppingCart } from 'lucide-react'

interface OKXAccountViewProps {
  accountId: number
}

export default function OKXAccountView({ accountId }: OKXAccountViewProps) {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  
  // Data states
  const [balance, setBalance] = useState<OKXBalance[]>([])
  const [positions, setPositions] = useState<OKXPosition[]>([])
  const [openOrders, setOpenOrders] = useState<OKXOrder[]>([])
  const [orderHistory, setOrderHistory] = useState<OKXOrder[]>([])
  const [trades, setTrades] = useState<OKXTrade[]>([])
  const [summary, setSummary] = useState<OKXAccountSummary | null>(null)

  const fetchAllData = async () => {
    try {
      setRefreshing(true)
      
      // Fetch critical data first (fast)
      const summaryRes = await getOKXAccountSummary(accountId)
      if (summaryRes.success) setSummary(summaryRes.summary)
      
      // Then fetch detailed data in parallel
      const [balanceRes, positionsRes, openOrdersRes] = await Promise.all([
        getOKXBalance(accountId),
        getOKXPositions(accountId),
        getOKXOpenOrders(accountId)
      ])

      if (balanceRes.success) setBalance(balanceRes.assets)
      if (positionsRes.success) setPositions(positionsRes.positions)
      if (openOrdersRes.success) setOpenOrders(openOrdersRes.orders)
      
      // Fetch history data lazily (only when user needs it)
      // This reduces initial load time
      // orderHistoryRes and tradesRes will be fetched when user clicks the tab

    } catch (error) {
      console.error('Failed to fetch OKX data:', error)
      toast.error('Failed to load OKX account data')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }
  
  // Lazy load order history
  const fetchOrderHistory = async () => {
    if (orderHistory.length > 0) return // Already loaded
    try {
      const res = await getOKXOrderHistory(accountId)
      if (res.success) setOrderHistory(res.orders)
    } catch (error) {
      console.error('Failed to fetch order history:', error)
    }
  }
  
  // Lazy load trades
  const fetchTrades = async () => {
    if (trades.length > 0) return // Already loaded
    try {
      const res = await getOKXTrades(accountId)
      if (res.success) setTrades(res.trades)
    } catch (error) {
      console.error('Failed to fetch trades:', error)
    }
  }

  useEffect(() => {
    fetchAllData()
  }, [accountId]) // Add accountId dependency

  const handleRefresh = () => {
    fetchAllData()
    toast.success('Refreshing OKX data...')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-muted-foreground">Loading OKX account data...</div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col space-y-6 p-6">
      {/* Header with Refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold">OKX Account</h2>
          <p className="text-muted-foreground">Real-time data from OKX exchange</p>
        </div>
        <Button onClick={handleRefresh} disabled={refreshing} variant="outline">
          <RefreshCcw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Balance</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${summary.total_balance_usdt.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">USDT equivalent</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Free Balance</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${summary.free_usdt.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">Available</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Positions Value</CardTitle>
              <Briefcase className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${summary.positions_value.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">{summary.positions_count} positions</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Unrealized P&L</CardTitle>
              {summary.unrealized_pnl >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${summary.unrealized_pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                ${summary.unrealized_pnl.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground">Open positions</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Open Orders</CardTitle>
              <ShoppingCart className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.open_orders_count}</div>
              <p className="text-xs text-muted-foreground">Pending</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Used Margin</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${summary.used_usdt.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">In use</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs for different data views */}
      <Tabs defaultValue="balance" className="flex-1" onValueChange={(value) => {
        // Lazy load data when user switches to history or trades tab
        if (value === 'history') fetchOrderHistory()
        if (value === 'trades') fetchTrades()
      }}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="balance">Balance</TabsTrigger>
          <TabsTrigger value="positions">Positions ({positions.length})</TabsTrigger>
          <TabsTrigger value="open-orders">Open Orders ({openOrders.length})</TabsTrigger>
          <TabsTrigger value="history">Order History</TabsTrigger>
          <TabsTrigger value="trades">Trades</TabsTrigger>
        </TabsList>

        {/* Balance Tab */}
        <TabsContent value="balance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Account Balance</CardTitle>
              <CardDescription>Your available assets on OKX</CardDescription>
            </CardHeader>
            <CardContent>
              {balance.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Currency</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                      <TableHead className="text-right">Free</TableHead>
                      <TableHead className="text-right">Used</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {balance.map((asset) => (
                      <TableRow key={asset.currency}>
                        <TableCell className="font-medium">{asset.currency}</TableCell>
                        <TableCell className="text-right">{asset.total.toFixed(8)}</TableCell>
                        <TableCell className="text-right">{asset.free.toFixed(8)}</TableCell>
                        <TableCell className="text-right">{asset.used.toFixed(8)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center text-muted-foreground py-8">No balance data</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Positions Tab */}
        <TabsContent value="positions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Current Positions</CardTitle>
              <CardDescription>Your open perpetual swap positions</CardDescription>
            </CardHeader>
            <CardContent>
              {positions.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Symbol</TableHead>
                      <TableHead>Side</TableHead>
                      <TableHead className="text-right">Contracts</TableHead>
                      <TableHead className="text-right">Notional</TableHead>
                      <TableHead className="text-right">Entry Price</TableHead>
                      <TableHead className="text-right">Mark Price</TableHead>
                      <TableHead className="text-right">Unrealized P&L</TableHead>
                      <TableHead className="text-right">ROI</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {positions.map((pos, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="font-medium">{pos.symbol}</TableCell>
                        <TableCell>
                          <Badge variant={pos.side === 'long' ? 'default' : 'destructive'}>
                            {pos.side.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">{pos.contracts}</TableCell>
                        <TableCell className="text-right">${pos.notional.toLocaleString()}</TableCell>
                        <TableCell className="text-right">${pos.entryPrice.toFixed(4)}</TableCell>
                        <TableCell className="text-right">${pos.markPrice.toFixed(4)}</TableCell>
                        <TableCell className={`text-right ${pos.unrealizedPnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                          ${pos.unrealizedPnl.toFixed(2)}
                        </TableCell>
                        <TableCell className={`text-right ${pos.percentage >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                          {pos.percentage.toFixed(2)}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center text-muted-foreground py-8">No open positions</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Open Orders Tab */}
        <TabsContent value="open-orders" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Open Orders</CardTitle>
              <CardDescription>Orders waiting to be filled</CardDescription>
            </CardHeader>
            <CardContent>
              {openOrders.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Order ID</TableHead>
                      <TableHead>Symbol</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Side</TableHead>
                      <TableHead className="text-right">Price</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead className="text-right">Filled</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Time</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {openOrders.map((order) => (
                      <TableRow key={order.id}>
                        <TableCell className="font-mono text-xs">{order.id.substring(0, 8)}</TableCell>
                        <TableCell className="font-medium">{order.symbol}</TableCell>
                        <TableCell>{order.type}</TableCell>
                        <TableCell>
                          <Badge variant={order.side === 'buy' ? 'default' : 'destructive'}>
                            {order.side.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">${order.price.toFixed(4)}</TableCell>
                        <TableCell className="text-right">{order.amount}</TableCell>
                        <TableCell className="text-right">{order.filled}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{order.status}</Badge>
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {new Date(order.datetime).toLocaleString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center text-muted-foreground py-8">No open orders</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Order History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Order History</CardTitle>
              <CardDescription>Recent completed orders (last 7 days)</CardDescription>
            </CardHeader>
            <CardContent>
              {orderHistory.length > 0 ? (
                <div className="max-h-[500px] overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Order ID</TableHead>
                        <TableHead>Symbol</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Side</TableHead>
                        <TableHead className="text-right">Price</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                        <TableHead className="text-right">Filled</TableHead>
                        <TableHead className="text-right">Avg Price</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Time</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {orderHistory.map((order) => (
                        <TableRow key={order.id}>
                          <TableCell className="font-mono text-xs">{order.id.substring(0, 8)}</TableCell>
                          <TableCell className="font-medium">{order.symbol}</TableCell>
                          <TableCell>{order.type}</TableCell>
                          <TableCell>
                            <Badge variant={order.side === 'buy' ? 'default' : 'destructive'}>
                              {order.side.toUpperCase()}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">${order.price.toFixed(4)}</TableCell>
                          <TableCell className="text-right">{order.amount}</TableCell>
                          <TableCell className="text-right">{order.filled}</TableCell>
                          <TableCell className="text-right">
                            ${((order as any).average || 0).toFixed(4)}
                          </TableCell>
                          <TableCell>
                            <Badge variant={order.status === 'closed' ? 'secondary' : 'outline'}>
                              {order.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">
                            {new Date(order.datetime).toLocaleString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-8">No order history</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trades Tab */}
        <TabsContent value="trades" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Trade History</CardTitle>
              <CardDescription>Recent executed trades (last 7 days)</CardDescription>
            </CardHeader>
            <CardContent>
              {trades.length > 0 ? (
                <div className="max-h-[500px] overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Trade ID</TableHead>
                        <TableHead>Symbol</TableHead>
                        <TableHead>Side</TableHead>
                        <TableHead className="text-right">Price</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                        <TableHead className="text-right">Cost</TableHead>
                        <TableHead className="text-right">Fee</TableHead>
                        <TableHead>Time</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {trades.map((trade) => (
                        <TableRow key={trade.id}>
                          <TableCell className="font-mono text-xs">{trade.id.substring(0, 8)}</TableCell>
                          <TableCell className="font-medium">{trade.symbol}</TableCell>
                          <TableCell>
                            <Badge variant={trade.side === 'buy' ? 'default' : 'destructive'}>
                              {trade.side.toUpperCase()}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">${trade.price.toFixed(4)}</TableCell>
                          <TableCell className="text-right">{trade.amount}</TableCell>
                          <TableCell className="text-right">${trade.cost.toFixed(2)}</TableCell>
                          <TableCell className="text-right">
                            {trade.fee ? `${trade.fee.cost} ${trade.fee.currency}` : '-'}
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">
                            {new Date(trade.datetime).toLocaleString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-8">No trade history</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
