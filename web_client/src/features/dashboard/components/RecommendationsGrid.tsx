import React from 'react';
import { ArrowRight, Star } from 'lucide-react';
import { RecommendationCard } from './RecommendationCard';

interface RecommendationsGridProps {
    loading: boolean;
    recommendations: any[];
    settings: any;
    onNavigate: (id: string) => void;
    onExploreMore: () => void;
}

export const RecommendationsGrid: React.FC<RecommendationsGridProps> = ({
    loading,
    recommendations,
    settings,
    onNavigate,
    onExploreMore
}) => {
    return (
        <div className="animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
            <div className="flex items-center justify-between mb-8">
                <div className="flex flex-col">
                    <h3 className="text-xs font-black text-gray-500 uppercase tracking-[0.25em] flex items-center gap-2 mb-1">
                        <Star className="w-3.5 h-3.5 text-yellow-500 fill-yellow-500" />
                        Selección Especial
                    </h3>
                    <span className="text-white text-xl font-black">Lecturas Recomendadas</span>
                </div>
                <button
                    onClick={onExploreMore}
                    className="px-5 py-2.5 rounded-premium-sm text-[10px] font-black uppercase tracking-widest bg-[var(--panel-bg-subtle)] hover:bg-[var(--panel-bg)] text-gray-300 transition-all border border-[var(--panel-border)] flex items-center gap-2 group"
                >
                    Explorar Todo <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 md:gap-8">
                {loading ? (
                    Array(4).fill(0).map((_, i) => (
                        <div key={i} className="aspect-[2/3] rounded-premium-lg bg-[var(--panel-bg-subtle)] animate-shimmer border border-[var(--panel-border)] bg-gradient-to-r from-transparent via-white/5 to-transparent bg-[length:200%_100%] shadow-inner"></div>
                    ))
                ) : (
                    recommendations.map((book, i) => (
                        <RecommendationCard
                            key={book.id || i}
                            book={book}
                            settings={settings}
                            onClick={() => onNavigate(`book:${book.id}`)}
                            index={i}
                        />
                    ))
                )}
            </div>
        </div>
    );
};
