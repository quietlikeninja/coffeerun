import { useEffect, useState } from 'react'
import { api, type StatsOverview, type DrinkStat, type ColleagueStat } from '@/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { BarChart3, Coffee, Users, Calendar } from 'lucide-react'

export function Stats() {
  const [overview, setOverview] = useState<StatsOverview | null>(null)
  const [drinks, setDrinks] = useState<DrinkStat[]>([])
  const [colleagueStats, setColleagueStats] = useState<ColleagueStat[]>([])
  const [days, setDays] = useState<string>('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const params = days ? `?days=${days}` : ''
    Promise.all([
      api.get<StatsOverview>(`/stats/overview${params}`),
      api.get<DrinkStat[]>(`/stats/drinks${params}`),
      api.get<ColleagueStat[]>(`/stats/colleagues${params}`),
    ]).then(([o, d, c]) => {
      setOverview(o)
      setDrinks(d)
      setColleagueStats(c)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [days])

  if (loading) return <div className="py-8 text-center text-muted-foreground">Loading...</div>

  const maxDrinkCount = drinks.length > 0 ? drinks[0].count : 1

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Stats</h1>
        <Select
          value={days}
          onChange={(e) => { setLoading(true); setDays(e.target.value) }}
          className="w-36"
          aria-label="Time range"
        >
          <option value="">All time</option>
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
        </Select>
      </div>

      {/* Overview cards */}
      {overview && (
        <div className="grid grid-cols-2 gap-3">
          <Card>
            <CardContent className="pt-4 text-center">
              <Coffee className="h-5 w-5 mx-auto mb-1 text-primary" />
              <p className="text-2xl font-bold">{overview.total_orders}</p>
              <p className="text-xs text-muted-foreground">Total Orders</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <BarChart3 className="h-5 w-5 mx-auto mb-1 text-primary" />
              <p className="text-2xl font-bold">{overview.total_coffees}</p>
              <p className="text-xs text-muted-foreground">Total Coffees</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <Calendar className="h-5 w-5 mx-auto mb-1 text-primary" />
              <p className="text-2xl font-bold">{overview.orders_this_week}</p>
              <p className="text-xs text-muted-foreground">This Week</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 text-center">
              <Users className="h-5 w-5 mx-auto mb-1 text-primary" />
              <p className="text-lg font-bold">{overview.busiest_day || '-'}</p>
              <p className="text-xs text-muted-foreground">Busiest Day</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Popular drinks */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Popular Drinks</CardTitle>
        </CardHeader>
        <CardContent>
          {drinks.length === 0 ? (
            <p className="text-sm text-muted-foreground">No data yet.</p>
          ) : (
            <div className="space-y-2">
              {drinks.map((drink, i) => (
                <div key={i} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>{drink.drink_name}</span>
                    <span className="text-muted-foreground">{drink.count}</span>
                  </div>
                  <div className="h-2 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all"
                      style={{ width: `${(drink.count / maxDrinkCount) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Per-colleague stats */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">By Colleague</CardTitle>
        </CardHeader>
        <CardContent>
          {colleagueStats.length === 0 ? (
            <p className="text-sm text-muted-foreground">No data yet.</p>
          ) : (
            <div className="space-y-2">
              {colleagueStats.map((stat, i) => (
                <div key={i} className="flex justify-between text-sm py-1 border-b last:border-0">
                  <div>
                    <span className="font-medium">{stat.colleague_name}</span>
                    {stat.favourite_drink && (
                      <span className="text-muted-foreground ml-2">
                        Fav: {stat.favourite_drink}
                      </span>
                    )}
                  </div>
                  <span className="text-muted-foreground">{stat.order_count} orders</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
