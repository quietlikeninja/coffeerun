const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

// Types matching backend schemas
export interface User {
  id: string
  email: string
  role: 'admin' | 'viewer'
  created_at: string | null
}

export interface DrinkType {
  id: string
  name: string
  display_order: number
  is_active: boolean
}

export interface Size {
  id: string
  name: string
  abbreviation: string
  display_order: number
  is_active: boolean
}

export interface MilkOption {
  id: string
  name: string
  display_order: number
  is_active: boolean
}

export interface CoffeeOption {
  id: string
  colleague_id: string
  drink_type_id: string
  drink_type_name: string | null
  size_id: string
  size_name: string | null
  size_abbreviation: string | null
  milk_option_id: string | null
  milk_option_name: string | null
  sugar: number
  notes: string | null
  is_default: boolean
  display_order: number
  created_at: string
}

export interface Colleague {
  id: string
  name: string
  usually_in: boolean
  display_order: number
  is_active: boolean
  coffee_options: CoffeeOption[]
  created_at: string
  updated_at: string
}

export interface ConsolidatedItem {
  count: number
  drink_type_name: string
  size_name: string
  size_abbreviation: string
  milk_option_name: string | null
  sugar: number
  notes: string | null
  display_text: string
}

export interface OrderItem {
  id: string
  order_id: string
  colleague_id: string
  colleague_name: string | null
  coffee_option_id: string
  drink_type_name: string
  size_name: string
  size_abbreviation: string
  milk_option_name: string | null
  sugar: number
  notes: string | null
  created_at: string
}

export interface Order {
  id: string
  share_token: string
  created_by: string
  created_at: string
  items: OrderItem[]
  consolidated: ConsolidatedItem[]
}

export interface OrderListItem {
  id: string
  share_token: string
  created_at: string
  item_count: number
}

export interface StatsOverview {
  total_orders: number
  total_coffees: number
  busiest_day: string | null
  orders_this_week: number
  orders_this_month: number
}

export interface DrinkStat {
  drink_name: string
  count: number
}

export interface ColleagueStat {
  colleague_name: string
  order_count: number
  favourite_drink: string | null
}
