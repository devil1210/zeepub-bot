"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, Download, FileText, User, Library, ChevronRight, BookOpen } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { callBotAPI } from "@/lib/api"
import { useTelegramContext } from "@/components/telegram-provider"
import { useStrings } from "@/components/strings-provider"
import { Pagination } from "@/components/pagination"

interface Book {
  id: string
  title: string
  author: string
  summary?: string
  cover?: string
  download_url?: string
  subsection_url?: string
  detail_url?: string
  is_folder: boolean
}

interface PaginationState {
  nextPage?: string | null
  prevPage?: string | null
  currentPage: number
  totalPages?: number | null
}

import { AccessGuard } from "@/components/access-guard"
import { TransparentHeader } from "@/components/transparent-header"
import { Loader2 } from "lucide-react"

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [books, setBooks] = useState<Book[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [pagination, setPagination] = useState<PaginationState>({
    currentPage: 1,
  })
  const { webApp } = useTelegramContext()
  const { t } = useStrings()
  const router = useRouter()
  const searchTimeout = useRef<NodeJS.Timeout | null>(null)

  // Replicando funcionalidad v3.13.8: Búsqueda dinámica (debounce)
  useEffect(() => {
    if (!searchQuery.trim()) {
      setBooks([])
      setPagination({ currentPage: 1 })
      return
    }

    if (searchTimeout.current) {
      clearTimeout(searchTimeout.current)
    }

    searchTimeout.current = setTimeout(() => {
      handleSearch()
    }, 600) // 600ms delay

    return () => {
      if (searchTimeout.current) {
        clearTimeout(searchTimeout.current)
      }
    }
  }, [searchQuery])

  const handleSearch = async (pageUrl?: string) => {
    if (!searchQuery.trim() && !pageUrl) return

    setIsLoading(true)
    try {
      const result = await callBotAPI("search", {
        query: searchQuery,
        pageUrl: pageUrl
      })
      setBooks(result.results || [])
      setPagination({
        nextPage: result.nextPage,
        prevPage: result.prevPage,
        currentPage: result.currentPage || 1,
        totalPages: result.totalPages
      })

      // Save search state to sessionStorage
      sessionStorage.setItem("search-state", JSON.stringify({
        query: searchQuery,
        pageUrl: pageUrl,
        currentPage: result.currentPage || 1
      }))

      // If navigating pages, scroll to top
      if (pageUrl) {
        window.scrollTo(0, 0)
      }
    } catch (error) {
      console.error("[v0] Search error:", error)
      webApp?.showAlert?.("Error al buscar libros")
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = async (e: React.MouseEvent, book: Book) => {
    e.stopPropagation()
    if (!book.download_url) {
      webApp?.showAlert?.("No hay link de descarga")
      return
    }

    try {
      webApp?.showPopup?.({
        title: "Descargando",
        message: `Se está enviando "${book.title}" a tu chat...`,
      })
      await callBotAPI("download", {
        bookId: book.download_url,
        title: book.title
      })
    } catch (error) {
      console.error("[v0] Download error:", error)
      webApp?.showAlert?.("Error al procesar la descarga")
    }
  }

  const handleBookClick = (book: Book) => {
    const detailUrl = book.detail_url || (book.id?.startsWith("http") ? book.id : null)

    if (detailUrl) {
      // Save current search state before navigating
      sessionStorage.setItem("search-state", JSON.stringify({
        query: searchQuery,
        currentPage: pagination.currentPage,
        nextPage: pagination.nextPage,
        prevPage: pagination.prevPage
      }))
      router.push(`/book?id=${encodeURIComponent(detailUrl)}`)
    } else if (book.is_folder && book.subsection_url) {
      // Use window.location.href to avoid history issues with deep links in catalog
      window.location.href = `/catalog?feed_url=${encodeURIComponent(book.subsection_url)}`
    }
  }

  return (
    <AccessGuard>
      <div className="min-h-screen bg-background pt-safe">
        <TransparentHeader />


        <div className="max-w-2xl mx-auto px-4 py-6 text-foreground">
          {/* Search */}
          <div className="mb-6">
            <div className="relative flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder={t("search_placeholder")}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  className="pl-12 h-12 bg-card border-border rounded-xl"
                />
              </div>
              <Button onClick={() => handleSearch()} disabled={isLoading} className="h-12 px-6 bg-primary hover:bg-primary/90">
                {isLoading ? <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" /> : t("search_button")}
              </Button>
            </div>
          </div>

          {/* Results */}
          <div className="space-y-3">
            {books.map((book, index) => (
              <Card
                key={book.id}
                onClick={() => handleBookClick(book)}
                className="p-4 border-border hover:bg-secondary/20 active:scale-[0.98] transition-all cursor-pointer group"
              >
                <div className="flex gap-4">
                  <div className="w-16 h-24 bg-secondary rounded-lg flex-shrink-0 overflow-hidden shadow-sm border border-border/50">
                    {book.cover ? (
                      <img src={book.cover} alt={book.title} className="w-full h-full object-cover" />
                    ) : book.is_folder ? (
                      <div className="w-full h-full flex items-center justify-center bg-primary/10">
                        <BookOpen className="w-8 h-8 text-primary" />
                      </div>
                    ) : (
                      <img src="/placeholder.svg" alt={book.title} className="w-full h-full object-cover" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0 flex flex-col">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-semibold text-foreground line-clamp-2 leading-tight group-hover:text-primary transition-colors">
                        {book.title}
                      </h3>
                      {book.is_folder && (
                        <span className="px-2 py-0.5 rounded-full bg-primary/20 text-primary text-[10px] font-bold uppercase tracking-wider flex-shrink-0">
                          {t("book_series")}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-primary font-medium mb-1 truncate">{book.author}</p>
                    <p className="text-xs text-muted-foreground line-clamp-2 italic mb-2">
                      {book.is_folder ? t("book_section") : t("book_details_hint")}
                    </p>

                    {!book.is_folder && book.download_url && (
                      <Button
                        size="sm"
                        onClick={(e) => handleDownload(e, book)}
                        className="h-8 text-[10px] px-3 bg-primary hover:bg-primary/90 self-start group/btn"
                      >
                        <Download className="w-3 h-3 mr-1.5" />
                        {t("book_download")}
                      </Button>
                    )}
                  </div>
                  <div className="flex items-center">
                    <ChevronRight className="w-5 h-5 text-muted-foreground/30 group-hover:text-primary transition-colors" />
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Pagination Component */}
          {(books.length > 0 || !!searchQuery) && (
            <Pagination
              currentPage={pagination.currentPage}
              totalPages={pagination.totalPages}
              hasNextPage={!!pagination.nextPage}
              hasPrevPage={!!pagination.prevPage}
              hasUpPage={!!searchQuery} // Replicando v3.13.8: "Subir" limpia búsqueda
              onNextPage={() => pagination.nextPage && handleSearch(pagination.nextPage)}
              onPrevPage={() => pagination.prevPage && handleSearch(pagination.prevPage)}
              onUpPage={() => {
                setSearchQuery("")
                setBooks([])
                setPagination({ currentPage: 1 })
              }}
              isLoading={isLoading}
            />
          )}

          {/* Empty State */}
          {books.length === 0 && !isLoading && (
            <div className="text-center py-12">
              <BookOpen className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">
                {searchQuery ? t("search_empty") : t("search_prompt")}
              </p>
            </div>
          )}
        </div>
      </div>
    </AccessGuard>
  )
}
