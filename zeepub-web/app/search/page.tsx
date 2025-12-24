"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Search, BookOpen, ChevronLeft, ChevronRight } from "lucide-react"
import { callBotAPI } from "@/lib/api"
import { useTelegramContext } from "@/components/telegram-provider"
import { AccessGuard } from "@/components/access-guard"

interface Book {
  id: string
  title: string
  author: string
  year?: string
  size?: string
  cover?: string
}

interface SearchResponse {
  results: Book[]
  nextPage?: string
  prevPage?: string
  currentPage: number
  totalPages?: number
}

export default function SearchPage() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState("")
  const [books, setBooks] = useState<Book[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [pagination, setPagination] = useState<{
    nextPage?: string
    prevPage?: string
    currentPage: number
    totalPages?: number
  }>({
    currentPage: 1,
  })
  const { webApp } = useTelegramContext()

  const handleSearch = async (pageUrl?: string) => {
    if (!searchQuery.trim() && !pageUrl) return

    setIsLoading(true)
    try {
      const result: SearchResponse = await callBotAPI("search", {
        query: searchQuery,
        pageUrl: pageUrl,
      })
      setBooks(result.results || [])
      setPagination({
        nextPage: result.nextPage,
        prevPage: result.prevPage,
        currentPage: result.currentPage || 1,
        totalPages: result.totalPages,
      })
    } catch (error) {
      console.error("[v0] Search error:", error)
      webApp?.showAlert?.("Error al buscar libros")
    } finally {
      setIsLoading(false)
    }
  }

  const handleNextPage = () => {
    if (pagination.nextPage) {
      handleSearch(pagination.nextPage)
    }
  }

  const handlePrevPage = () => {
    if (pagination.prevPage) {
      handleSearch(pagination.prevPage)
    }
  }

  const handleBookClick = (bookId: string) => {
    router.push(`/book?id=${encodeURIComponent(bookId)}`)
  }

  return (
    <AccessGuard>
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
          <div className="max-w-2xl mx-auto px-4 py-3">
            <h1 className="text-lg font-semibold text-center">Buscar Libros</h1>
          </div>
        </header>

        <div className="max-w-2xl mx-auto px-4 py-6">
          {/* Search */}
          <div className="mb-6">
            <div className="relative flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  type="text"
                  placeholder="Buscar por título, autor..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  className="pl-12 h-12 bg-card border-border rounded-xl"
                />
              </div>
              <Button
                onClick={() => handleSearch()}
                disabled={isLoading}
                className="h-12 px-6 bg-primary hover:bg-primary/90"
              >
                {isLoading ? "Buscando..." : "Buscar"}
              </Button>
            </div>
          </div>

          {books.length > 0 && (
            <div className="mb-4 text-center">
              <p className="text-sm text-muted-foreground">
                Página {pagination.currentPage}
                {pagination.totalPages && ` de ${pagination.totalPages}`}
              </p>
            </div>
          )}

          {/* Results */}
          <div className="space-y-3">
            {books.map((book) => (
              <Card
                key={book.id}
                onClick={() => handleBookClick(book.id)}
                className="p-4 border-border cursor-pointer hover:bg-secondary/20 transition-colors active:scale-[0.98]"
              >
                <div className="flex gap-4">
                  <div className="w-16 h-24 bg-secondary rounded-lg flex-shrink-0 overflow-hidden">
                    <img
                      src={book.cover || "/placeholder.svg"}
                      alt={book.title}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-foreground mb-1 line-clamp-2">{book.title}</h3>
                    <p className="text-sm text-muted-foreground mb-2">{book.author}</p>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      {book.year && <span>{book.year}</span>}
                      {book.size && <span>• {book.size}</span>}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {books.length > 0 && (pagination.prevPage || pagination.nextPage) && (
            <div className="mt-6 flex items-center justify-center gap-3">
              <Button
                variant="outline"
                onClick={handlePrevPage}
                disabled={!pagination.prevPage || isLoading}
                className="h-11 px-5 bg-card border-border hover:bg-secondary/50 disabled:opacity-40"
              >
                <ChevronLeft className="w-5 h-5 mr-1" />
                Anterior
              </Button>

              <div className="px-4 py-2 bg-card border border-border rounded-lg">
                <span className="text-sm font-medium text-foreground">{pagination.currentPage}</span>
              </div>

              <Button
                variant="outline"
                onClick={handleNextPage}
                disabled={!pagination.nextPage || isLoading}
                className="h-11 px-5 bg-card border-border hover:bg-secondary/50 disabled:opacity-40"
              >
                Siguiente
                <ChevronRight className="w-5 h-5 ml-1" />
              </Button>
            </div>
          )}

          {/* Empty State */}
          {books.length === 0 && !isLoading && (
            <div className="text-center py-12">
              <BookOpen className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
              <p className="text-muted-foreground">
                {searchQuery ? "No se encontraron resultados" : "Busca libros por título o autor"}
              </p>
            </div>
          )}
        </div>
      </div>
    </AccessGuard>
  )
}
