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
export async function checkAccess(userId: number) {
  const initData = getTelegramInitData()

  const response = await fetch("/api/user/access", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-telegram-init-data": initData,
    },
    body: JSON.stringify({ user_id: userId }),
  })

  if (!response.ok) {
    throw new Error(`Access check error: ${response.statusText}`)
  }

  return response.json()
}

// Obtener información del nivel de usuario
export async function getUserLevel(userId: number) {
  const initData = getTelegramInitData()

  const response = await fetch("/api/user/access", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-telegram-init-data": initData,
    },
    body: JSON.stringify({ user_id: userId }),
  })

  if (!response.ok) {
    throw new Error(`User level error: ${response.statusText}`)
  }

  const data = await response.json()
  return data.level // Retorna solo la información del nivel
}
