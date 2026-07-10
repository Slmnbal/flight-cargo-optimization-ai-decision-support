const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

type QueryValue = string | number | boolean | undefined | null
// Query param taşıyıcı tipler (FlightsQuery, CargoRequestsQuery, ...) index
// signature'sız interface'ler -- object'ten geniş bir generic kullanmak,
// TypeScript'in "interface'ler otomatik index signature almaz" kısıtını
// Record<string, QueryValue> ile çakıştırmadan aşıyor.
type QueryParams = Record<string, QueryValue> | object

function buildQueryString(params?: QueryParams): string {
  if (!params) return ''
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params) as [string, QueryValue][]) {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value))
    }
  }
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

async function request<T>(
  path: string,
  options: { method?: string; params?: QueryParams; body?: unknown } = {},
): Promise<T> {
  const { method = 'GET', params, body } = options
  const url = `${API_BASE_URL}${path}${buildQueryString(params)}`

  const response = await fetch(url, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!response.ok) {
    let detail = response.statusText
    try {
      const errorBody = await response.json()
      detail = errorBody?.detail ?? detail
    } catch {
      // response gövdesi JSON değilse statusText ile devam et
    }
    throw new ApiError(response.status, detail)
  }

  if (response.status === 204) {
    return undefined as T
  }
  return response.json() as Promise<T>
}

export const apiClient = {
  get: <T>(path: string, params?: QueryParams) => request<T>(path, { params }),
  post: <T>(path: string, body?: unknown, params?: QueryParams) =>
    request<T>(path, { method: 'POST', body, params }),
}
