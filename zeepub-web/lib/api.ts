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
