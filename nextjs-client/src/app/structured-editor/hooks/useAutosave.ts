import { useCallback, useRef, useEffect } from 'react'

interface UseAutosaveOptions {
  delay?: number
  onSave: (data: any) => Promise<void>
  onError?: (error: Error) => void
}

export function useAutosave<T>(data: T, options: UseAutosaveOptions) {
  const { delay = 800, onSave, onError } = options
  const timeoutRef = useRef<NodeJS.Timeout>()
  const lastSavedRef = useRef<T>()
  const isSavingRef = useRef(false)

  const save = useCallback(async (dataToSave: T) => {
    if (isSavingRef.current || !dataToSave) return
    
    try {
      isSavingRef.current = true
      await onSave(dataToSave)
      lastSavedRef.current = dataToSave
    } catch (error) {
      console.error('Autosave failed:', error)
      if (onError) {
        onError(error as Error)
      }
    } finally {
      isSavingRef.current = false
    }
  }, [onSave, onError])

  const debouncedSave = useCallback((dataToSave: T) => {
    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    // Set new timeout
    timeoutRef.current = setTimeout(() => {
      save(dataToSave)
    }, delay)
  }, [save, delay])

  // Auto-save when data changes
  useEffect(() => {
    // Skip if data is null or undefined
    if (!data) {
      return
    }
    
    // Skip if data hasn't changed or is the same as last saved
    if (JSON.stringify(data) === JSON.stringify(lastSavedRef.current)) {
      return
    }

    debouncedSave(data)
  }, [data, debouncedSave])

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return {
    save: (dataToSave: T) => save(dataToSave),
    isSaving: isSavingRef.current
  }
}
