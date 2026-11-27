export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Unable to complete the request.'
}

export async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const hasBody = typeof init?.body === 'string'
  const response = await fetch(url, {
    ...init,
    headers: {
      ...(hasBody ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })

  const payload: unknown = await response.json().catch(() => null)

  if (!response.ok) {
    const detail =
      typeof payload === 'object' &&
      payload !== null &&
      'detail' in payload
        ? String((payload as { detail: unknown }).detail)
        : `Request failed with status ${response.status}`
    throw new Error(detail)
  }

  return payload as T
}

export function jsonBody(value: unknown): RequestInit {
  return { method: 'POST', body: JSON.stringify(value) }
}
