"use client"

import React, { createContext, useContext, useEffect, useState } from "react"
import { AppStrings, DEFAULT_STRINGS, fetchAppStrings } from "@/lib/strings"

interface StringsContextType {
    strings: AppStrings
    t: (key: keyof AppStrings, replacements?: Record<string, string>) => string
    isLoading: boolean
}

const StringsContext = createContext<StringsContextType>({
    strings: DEFAULT_STRINGS,
    t: (key, replacements) => {
        let text = DEFAULT_STRINGS[key]
        if (replacements) {
            Object.entries(replacements).forEach(([k, v]) => {
                text = text.replace(`[${k}]`, v)
            })
        }
        return text
    },
    isLoading: true,
})

export function StringsProvider({ children }: { children: React.ReactNode }) {
    const [strings, setStrings] = useState<AppStrings>(DEFAULT_STRINGS)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        async function load() {
            const data = await fetchAppStrings()
            setStrings(data)
            setIsLoading(false)
        }
        load()
    }, [])

    const t = (key: keyof AppStrings, replacements?: Record<string, string>) => {
        let text = strings[key] || DEFAULT_STRINGS[key]
        if (replacements) {
            Object.entries(replacements).forEach(([k, v]) => {
                text = text.replace(`[${k}]`, v)
            })
        }
        return text
    }

    return (
        <StringsContext.Provider value={{ strings, t, isLoading }}>
            {children}
        </StringsContext.Provider>
    )
}

export const useStrings = () => useContext(StringsContext)
