import { getTelegramInitData } from "./telegram"
import { OPDSFeed } from "./opds-types"

const feedCache = new Map<string, { data: OPDSFeed; timestamp: number }>()
const CACHE_TTL = 1000 * 60 * 60 // 60 minutes

export class OpdsClient {
    static async fetchFeed(url?: string, adminMode: boolean = false, useCache: boolean = true): Promise<OPDSFeed | null> {
        const initData = getTelegramInitData()

        const queryParams = new URLSearchParams()
        if (url) {
            queryParams.append("url", url)
        }
        if (adminMode) {
            queryParams.append("admin_mode", "true")
        }

        const cacheKey = `${url || "root"}-${adminMode}`
        if (useCache) {
            const cached = feedCache.get(cacheKey)
            if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
                console.log(`[OpdsClient] Returning CACHED feed: ${cacheKey}`)
                return cached.data
            }
        }

        const targetUrl = `/api/feed?${queryParams.toString()}`

        console.log(`[OpdsClient] Fetching JSON feed: ${targetUrl}`)

        try {
            const response = await fetch(targetUrl, {
                method: "GET",
                headers: {
                    "X-Telegram-Data": initData
                }
            })

            if (!response.ok) {
                const text = await response.text().catch(() => "No error body")
                console.error(`[OpdsClient] API error (${response.status}):`, text)
                return null
            }

            const data = await response.json()

            // Cache the result
            feedCache.set(cacheKey, { data, timestamp: Date.now() })

            return data as OPDSFeed
        } catch (e) {
            console.error("[OpdsClient] Unexpected Error:", e)
            return null
        }
    }

    static clearCache() {
        feedCache.clear()
    }
}
