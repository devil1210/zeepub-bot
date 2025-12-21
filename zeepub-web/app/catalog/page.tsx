"use client"

import { Card } from "@/components/ui/card"
import { Library, ExternalLink, BookMarked } from "lucide-react"

export default function CatalogPage() {
    const libraries = [
        {
            name: "Biblioteca Principal",
            description: "Catálogo completo de ePubs disponibles",
            url: "/opds",
            icon: Library,
        },
        {
            name: "Novedades",
            description: "Últimos libros agregados al catálogo",
            url: "/opds/recent",
            icon: BookMarked,
        },
        {
            name: "Más Descargados",
            description: "Los libros más populares",
            url: "/opds/popular",
            icon: ExternalLink,
        },
    ]

    return (
        <div className="min-h-screen bg-background">
            <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
                <div className="max-w-2xl mx-auto px-4 py-3">
                    <h1 className="text-lg font-semibold text-center">Mi Catálogo</h1>
                </div>
            </header>

            <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
                {/* Header */}
                <div className="text-center mb-6">
                    <Library className="w-16 h-16 text-primary mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-foreground mb-2">Bibliotecas OPDS</h2>
                    <p className="text-sm text-muted-foreground">
                        Accede a diferentes catálogos de libros electrónicos
                    </p>
                </div>

                {/* Libraries List */}
                <div className="space-y-3">
                    {libraries.map((library, index) => {
                        const Icon = library.icon
                        return (
                            <a key={index} href={library.url} target="_blank" rel="noopener noreferrer">
                                <Card className="p-5 hover:bg-secondary/50 transition-colors cursor-pointer border-border">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                                            <Icon className="w-6 h-6 text-primary" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h3 className="font-semibold text-foreground mb-1">{library.name}</h3>
                                            <p className="text-sm text-muted-foreground">{library.description}</p>
                                        </div>
                                        <ExternalLink className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                                    </div>
                                </Card>
                            </a>
                        )
                    })}
                </div>

                {/* Info Card */}
                <Card className="p-5 border-border bg-secondary/30 mt-8">
                    <h4 className="font-semibold text-foreground mb-2">¿Qué es OPDS?</h4>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                        OPDS (Open Publication Distribution System) es un formato estándar para distribuir catálogos
                        de libros electrónicos. Puedes usar estas URLs en cualquier lector compatible con OPDS.
                    </p>
                </Card>
            </div>
        </div>
    )
}
