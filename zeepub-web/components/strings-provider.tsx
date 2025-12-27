"use client"

import React, { createContext, useContext, useEffect, useState } from "react"
import { AppStrings, DEFAULT_STRINGS, fetchAppStrings } from "@/lib/strings"

interface StringsContextType {
    strings: AppStrings
    t: (key: keyof AppStrings) => string
    isLoading: boolean
}

const StringsContext = createContext<StringsContextType>({
    strings: DEFAULT_STRINGS,
    t: (key) => DEFAULT_STRINGS[key],
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

    const t = (key: keyof AppStrings) => strings[key] || DEFAULT_STRINGS[key]

    return (
        <StringsContext.Provider value={{ strings, t, isLoading }}>
            {children}
        </StringsContext.Provider>
    )
}

export const useStrings = () => useContext(StringsContext)
