import { XMLParser } from "fast-xml-parser"
import { getTelegramInitData } from "./telegram"
import { OPDSFeed, OPDSEntry, OPDSLink } from "./opds-types"

const parser = new XMLParser({
    ignoreAttributes: false,
    attributeNamePrefix: "",
    isArray: (name) => ["entry", "link", "content", "author"].indexOf(name) !== -1
})

export class OpdsClient {
    static async fetchFeed(url?: string, adminMode: boolean = false): Promise<OPDSFeed | null> {
        const initData = getTelegramInitData()

        let targetUrl = `/api/tunnel/opds`
        const queryParams = new URLSearchParams()

        if (url) {
            queryParams.append("url", url)
        } else {
            queryParams.append("url", "/")
        }

        if (adminMode) {
            queryParams.append("admin_mode", "true")
        }

        targetUrl += `?${queryParams.toString()}`

        console.log(`[OpdsClient] Fetching: ${targetUrl} (Original: ${url || 'root'})`)

        try {
            const response = await fetch(targetUrl, {
                method: "GET",
                headers: {
                    "X-Telegram-Data": initData
                }
            })

            if (!response.ok) {
                const text = await response.text().catch(() => "No error body")
                console.error(`[OpdsClient] Tunnel error (${response.status}):`, text)
                return null
            }

            const xmlText = await response.text()
            if (!xmlText || xmlText.trim().length === 0) {
                console.error("[OpdsClient] Empty XML response")
                return null
            }

            const result = parser.parse(xmlText)

            if (!result.feed) {
                console.error("[OpdsClient] Invalid feed structure:", result)
                return null
            }

            return this.mapFeed(result.feed, url)
        } catch (e) {
            console.error("[OpdsClient] Unexpected Error:", e)
            return null
        }
    }

    private static mapFeed(rawFeed: any, originalUrl: string = ""): OPDSFeed {
        const entries = (rawFeed.entry || []).map((e: any) => this.mapEntry(e, originalUrl))
        const links = (rawFeed.link || []).map((l: any) => this.mapLink(l))

        // Extract pagination
        const nextLink = links.find((l: OPDSLink) => l.rel === "next")
        const prevLink = links.find((l: OPDSLink) => l.rel === "previous" || l.rel === "prev")

        // Basic pagination guess (can be improved)
        let currentPage = 1
        if (originalUrl && originalUrl.includes("page=")) {
            const match = originalUrl.match(/page=(\d+)/)
            if (match) currentPage = parseInt(match[1])
        }

        return {
            title: typeof rawFeed.title === 'string' ? rawFeed.title : (rawFeed.title?.["#text"] || "Catalog"),
            links,
            entries,
            nextPage: nextLink?.href || null,
            prevPage: prevLink?.href || null,
            currentPage,
            totalPages: null // Hard to guess from XML without specific opensearch tags
        }
    }

    private static mapEntry(raw: any, baseUrl: string): OPDSEntry {
        const links: OPDSLink[] = (raw.link || []).map((l: any) => this.mapLink(l))

        // Find special links
        const coverLink = links.find(l =>
            l.rel.includes("image") ||
            l.rel.includes("cover") ||
            l.type?.startsWith("image/")
        )

        const subsectionLink = links.find(l => l.rel === "subsection")

        // Fallback for cover in content
        let coverUrl = coverLink?.href
        if (!coverUrl && raw.content) {
            const contentArray = Array.isArray(raw.content) ? raw.content : [raw.content]
            const imgContent = contentArray.find((c: any) => c.type?.startsWith("image/"))
            if (imgContent) coverUrl = imgContent.src || imgContent["@_src"] // Check how fast-xml-parser parses attributes on content? 
            // Wait, fast-xml-parser with no prefix puts attributes as keys.
            // But content usually has text. If it's empty tag with src, it's just keys.
        }

        const author = raw.author?.[0]?.name || "Unknown"
        const title = typeof raw.title === 'string' ? raw.title : (raw.title?.["#text"] || "No title")

        return {
            id: raw.id || "",
            title: title,
            author: typeof author === 'string' ? author : (author?.["#text"] || "Unknown"), // Author name might be object
            summary: raw.summary?.["#text"] || raw.content?.["#text"] || "",
            cover_url: coverUrl,
            subsection_url: subsectionLink?.href,
            detail_url: links.find(l => l.rel === "self")?.href,
            links: links
        }
    }

    private static mapLink(raw: any): OPDSLink {
        return {
            href: raw.href,
            rel: raw.rel,
            type: raw.type,
            title: raw.title
        }
    }
}
