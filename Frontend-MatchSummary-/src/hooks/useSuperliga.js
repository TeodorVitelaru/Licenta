import { useState, useEffect, useCallback, useRef } from 'react'
import { superligaService } from '../services'

export const useSuperligaStandings = (params = {}, autoFetch = true) => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const fetchingRef = useRef(false)
  const hasFetchedRef = useRef(false)
  const paramsRef = useRef(params)
  const mountedRef = useRef(true)

  useEffect(() => {
    const paramsString = JSON.stringify(params)
    const currentParamsString = JSON.stringify(paramsRef.current)
    if (paramsString !== currentParamsString) {
      paramsRef.current = params
      hasFetchedRef.current = false
    }
  }, [params])

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  const fetchStandings = useCallback(async () => {
    if (fetchingRef.current) {
      return
    }

    fetchingRef.current = true
    setLoading(true)
    setError(null)

    try {
      const standings = await superligaService.getStandings(paramsRef.current)

      if (standings && Array.isArray(standings) && standings.length > 0) {
        if (mountedRef.current) {
          setData(standings)
          hasFetchedRef.current = true
        } else {
          setData(standings)
          hasFetchedRef.current = true
        }
      } else if (mountedRef.current) {
        setError('Nu s-au primit date de la API')
        setData(null)
        hasFetchedRef.current = false
      }
    } catch (err) {
      setError(err.message || 'Eroare la incarcarea clasamentului')
      setData(null)
      hasFetchedRef.current = false
    } finally {
      setLoading(false)
      fetchingRef.current = false
    }
  }, [])

  const refetch = useCallback(async () => {
    hasFetchedRef.current = false
    fetchingRef.current = false
    await fetchStandings()
  }, [fetchStandings])

  useEffect(() => {
    if (autoFetch && !hasFetchedRef.current && !fetchingRef.current && mountedRef.current) {
      fetchStandings()
    }
  }, [autoFetch])

  return { data, loading, error, refetch }
}
