import { getTelegramInitData } from "./telegram"

export async function callBotAPI(action: string, data?: any) {
  const initData = getTelegramInitData()

  const response = await fetch("/api/bot", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-telegram-init-data": initData,
    },
    body: JSON.stringify({ action, data }),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}

export async function fetchBotFeed(url?: string) {
  const initData = getTelegramInitData()
  const queryParam = url ? `?url=${encodeURIComponent(url)}` : ""

  const response = await fetch(`/api/feed${queryParam}`, {
    method: "GET",
    headers: {
      "X-Telegram-Data": initData,
    },
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}
