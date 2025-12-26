import { getTelegramInitData } from "./telegram"
import { OPDSFeed } from "./opds-types"

export class OpdsClient {
    static async fetchFeed(url?: string, adminMode: boolean = false): Promise<OPDSFeed | null> {
        const initData = getTelegramInitData()

        const queryParams = new URLSearchParams()
        if (url) {
            queryParams.append("url", url)
        }
        if (adminMode) {
            queryParams.append("admin_mode", "true")
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
            return data as OPDSFeed
        } catch (e) {
            console.error("[OpdsClient] Unexpected Error:", e)
            return null
        }
    }
}
