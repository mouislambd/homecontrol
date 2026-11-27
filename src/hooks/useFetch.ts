import { useCallback, useEffect, useRef, useState } from 'react'
import { errorMessage } from '../api/client'

export function useFetch<T>(loader: () => Promise<T>, reloadKey?: unknown) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const loaderRef = useRef(loader)
  const requestId = useRef(0)

  useEffect(() => {
    loaderRef.current = loader
  }, [loader])

  const reload = useCallback(async () => {
    const id = ++requestId.current
    setLoading(true)
    try {
      const next = await loaderRef.current()
      if (id !== requestId.current) return
      setData(next)
      setError(null)
    } catch (err) {
      if (id !== requestId.current) return
      setError(errorMessage(err))
    } finally {
      if (id === requestId.current) setLoading(false)
    }
  }, [])

  useEffect(() => {
    queueMicrotask(() => void reload())
  }, [reload, reloadKey])

  return { data, loading, error, reload, setData }
}
