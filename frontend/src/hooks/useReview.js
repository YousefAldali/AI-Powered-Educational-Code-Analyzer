import { useState, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

// Hook to call the CodeTutor API and manage loading/error state
export function useReview() {
    const [result, setResult] = useState(null)
    const [isLoading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const submit = useCallback(async ({ code, language, file }) => {
        setLoading(true)
        setError(null)
        setResult(null)

        try {
            let body
            let headers = {}

            if (file) {
                // Multipart file upload
                const form = new FormData()
                form.append('file', file)
                form.append('language', language)
                body = form
                // Let the browser set the Content-Type (boundary included)
            } else {
                // JSON body with raw code
                body = JSON.stringify({ code, language })
                headers['Content-Type'] = 'application/json'
            }

            const res = await fetch(`${API_BASE}/api/review`, {
                method: 'POST',
                headers,
                body,
            })

            // Safe JSON parsing — handle empty or non-JSON responses
            const text = await res.text()
            let data
            try {
                data = text ? JSON.parse(text) : null
            } catch {
                throw new Error(
                    `Server returned invalid response (${res.status}). ` +
                    'Make sure the Flask backend is running on port 5000.'
                )
            }

            if (!data) {
                throw new Error(
                    'Empty response from server. ' +
                    'Make sure the Flask backend is running: cd flask && python app.py'
                )
            }

            if (!res.ok) {
                throw new Error(data.error ?? `Server error: ${res.status}`)
            }

            setResult(data)
        } catch (err) {
            if (err.name === 'TypeError' && err.message.includes('fetch')) {
                setError('Cannot reach the server. Make sure the Flask backend is running on port 5000.')
            } else {
                setError(err.message ?? 'Unknown error')
            }
        } finally {
            setLoading(false)
        }
    }, [])

    return { result, isLoading, error, submit }
}
