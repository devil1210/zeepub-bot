import { getTelegramInitData } from "./telegram"
import { OPDSFeed } from "./opds-types"

const feedCache = new Map<string, { data: OPDSFeed; timestamp: number }>()
const CACHE_TTL = 1000 * 60 * 60 * 6 // 6 hours

export class OpdsClient {
    static async fetchFeed(url?: string, adminMode: boolean = false, useCache: boolean = true): Promise<OPDSFeed | null> {
        const initData = getTelegramInitData()

        // Detectar si debemos usar la librería local
        const useLocalLibrary = localStorage.getItem("useLocalLibrary") === "true"

        if (useLocalLibrary && !url?.startsWith("http")) {
            // Si es local y no es una URL externa explicitly, usar el API local
            return this.fetchLocalLibrary(url)
        }

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

    static async fetchLocalLibrary(url?: string): Promise<OPDSFeed | null> {
        const initData = getTelegramInitData()

        let apiPath = "/api/library/catalog"
        if (url && url.includes("source_id=")) {
            // Re-use source_id and folder from simulated "URL"
            const params = new URLSearchParams(url.split("?")[1])
            apiPath += `?source_id=${params.get("source_id")}&folder=${params.get("folder") || ""}`
        }

        try {
            const response = await fetch(apiPath, {
                headers: { "X-Telegram-Data": initData }
            })
            if (!response.ok) return null
            const items = await response.json()

            // Map local items to OPDSFeed format
            return {
                title: "Biblioteca Local",
                currentPage: 1,
                totalItems: items.length,
                totalPages: 1,
                entries: items.map((item: any) => ({
                    id: item.id,
                    title: item.title,
                    author: item.author,
                    summary: item.summary,
                    cover_url: item.cover ? `/api/library/covers/${item.cover.split('/').pop()}` : undefined,
                    is_folder: item.is_folder,
                    series: item.series,
                    seriesIndex: item.seriesIndex,
                    tags: item.tags,
                    year: item.modifiedAt?.split("-")[0],
                    links: [
                        {
                            rel: item.is_folder ? "subsection" : "http://opds-spec.org/acquisition",
                            href: item.is_folder
                                ? `local?source_id=${item.source_id}&folder=${item.folder_path}`
                                : item.downloadUrl,
                            type: item.is_folder ? "application/atom+xml;profile=opds-catalog;kind=navigation" : "application/epub+zip"
                        }
                    ]
                })),
                links: []
            } as any as OPDSFeed
        } catch (e) {
            console.error("[OpdsClient] Local fetch error:", e)
            return null
        }
    }

    static async search(query: string, pageUrl?: string): Promise<any> {
        const initData = getTelegramInitData()
        const useLocalLibrary = localStorage.getItem("useLocalLibrary") === "true"

        if (useLocalLibrary && !pageUrl?.startsWith("http")) {
            const response = await fetch(`/api/library/search?query=${encodeURIComponent(query)}`, {
                headers: { "X-Telegram-Data": initData }
            })
            if (!response.ok) return { results: [] }
            const items = await response.json()
            return {
                results: items.map((item: any) => ({
                    id: item.id,
                    title: item.title,
                    author: item.author,
                    summary: item.summary,
                    cover: item.cover ? `/api/library/covers/${item.cover.split('/').pop()}` : undefined,
                    isFolder: false,
                    downloadUrl: item.downloadUrl,
                    series: item.series,
                    seriesIndex: item.seriesIndex,
                    tags: item.tags,
                    romaji: item.romajiTitle,
                    cleanTitle: item.title
                })),
                currentPage: 1,
                totalPages: 1
            }
        }

        // Default to Bot API search
        const response = await fetch("/api/bot", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-telegram-init-data": initData,
            },
            body: JSON.stringify({
                action: "search",
                data: { query, pageUrl }
            }),
        })
        if (!response.ok) return { results: [] }
        return response.json()
    }

    static clearCache() {
        feedCache.clear()
    }
}
