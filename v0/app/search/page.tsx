"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Search, BookOpen, Download } from "lucide-react"
import Link from "next/link"

interface Book {
  id: string
  title: string
  author: string
  year?: string
  size?: string
  cover?: string
}

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [books, setBooks] = useState<Book[]>([
    {
      id: "1",
      title: "El Quijote",
      author: "Miguel de Cervantes",
      year: "1605",
      size: "2.3 MB",
      cover: "/book-cover-quijote.jpg",
    },
    {
      id: "2",
      title: "Cien Años de Soledad",
      author: "Gabriel García Márquez",
      year: "1967",
      size: "1.8 MB",
      cover: "/book-cover-solitude.jpg",
    },
  ])

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-4">
          <Link href="/">
            <button className="text-foreground/60 hover:text-foreground">
              <ArrowLeft className="w-6 h-6" />
            </button>
          </Link>
          <h1 className="text-lg font-semibold">Buscar Libros</h1>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-6">
        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Buscar por título, autor..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 h-12 bg-card border-border rounded-xl"
            />
          </div>
        </div>

        {/* Results */}
        <div className="space-y-3">
          {books.map((book) => (
            <Card key={book.id} className="p-4 border-border">
              <div className="flex gap-4">
                <div className="w-16 h-24 bg-secondary rounded-lg flex-shrink-0 overflow-hidden">
                  <img src={book.cover || "/placeholder.svg"} alt={book.title} className="w-full h-full object-cover" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-foreground mb-1 line-clamp-2">{book.title}</h3>
                  <p className="text-sm text-muted-foreground mb-2">{book.author}</p>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    {book.year && <span>{book.year}</span>}
                    {book.size && <span>• {book.size}</span>}
                  </div>
                  <Button size="sm" className="mt-3 bg-primary hover:bg-primary/90 h-8 text-xs">
                    <Download className="w-3 h-3 mr-1" />
                    Descargar
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Empty State */}
        {books.length === 0 && (
          <div className="text-center py-12">
            <BookOpen className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
            <p className="text-muted-foreground">No se encontraron resultados</p>
          </div>
        )}
      </div>
    </div>
  )
}
