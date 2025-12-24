"use client"

import { createContext, useContext, type ReactNode } from "react"
import { useTelegram } from "@/hooks/use-telegram"

interface TelegramContextType {
  webApp: any
  user: any
  isReady: boolean
}

const TelegramContext = createContext<TelegramContextType>({
  webApp: null,
  user: null,
  isReady: false,
})

export function TelegramProvider({ children }: { children: ReactNode }) {
  const telegram = useTelegram()

  return <TelegramContext.Provider value={telegram}>{children}</TelegramContext.Provider>
}

export function useTelegramContext() {
  return useContext(TelegramContext)
}
