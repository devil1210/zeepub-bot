"use client"

import { Star, X } from "lucide-react"

interface RatingBreakdownPopupProps {
    show: boolean;
    onClose: () => void;
    book: any;
    ratingBreakdown: any;
}

export function RatingBreakdownPopup({ show, onClose, book, ratingBreakdown }: RatingBreakdownPopupProps) {
    if (!show) return null;

    const stats = ratingBreakdown || { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
    const total = Object.values(stats).reduce((a: any, b: any) => a + b, 0) as number;
    const maxVal = Math.max(...(Object.values(stats) as number[]), 1);

    return (
        <div
            className="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-300"
            onClick={onClose}
        >
            <div
                className="w-full max-w-sm bg-card border border-primary/20 rounded-3xl p-6 shadow-2xl relative overflow-hidden animate-in zoom-in-95 duration-200"
                onClick={e => e.stopPropagation()}
            >
                {/* Background Glow */}
                <div className="absolute -top-24 -right-24 w-48 h-48 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 rounded-full bg-secondary/50 hover:bg-secondary transition-colors"
                >
                    <X className="w-4 h-4" />
                </button>

                <div className="text-center mb-6">
                    <h3 className="text-lg font-black tracking-tight mb-1">Calificaciones</h3>
                    <div className="flex items-center justify-center gap-2">
                        <div className="flex items-center gap-1 text-primary">
                            <Star className="w-5 h-5 fill-primary" />
                            <span className="text-2xl font-black">{(book.rating_average || 0).toFixed(1)}</span>
                        </div>
                        <span className="text-xs text-muted-foreground font-bold">Resumen de {total} votos</span>
                    </div>
                </div>

                <div className="space-y-3 mb-2">
                    {[5, 4, 3, 2, 1].map((star) => {
                        const count = stats[star] || 0;
                        const percentage = total > 0 ? (count / total) * 100 : 0;
                        return (
                            <div key={star} className="flex items-center gap-3">
                                <div className="flex items-center gap-1 w-8">
                                    <span className="text-xs font-bold">{star}</span>
                                    <Star className="w-3 h-3 fill-primary text-primary opacity-60" />
                                </div>
                                <div className="flex-1 h-2.5 bg-secondary/50 rounded-full overflow-hidden border border-border/5">
                                    <div
                                        className="h-full bg-primary shadow-[0_0_8px_rgba(var(--primary),0.4)] transition-all duration-1000 ease-out"
                                        style={{ width: `${percentage}%` }}
                                    />
                                </div>
                                <span className="text-[10px] font-bold text-muted-foreground w-8 text-right">
                                    {count}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
