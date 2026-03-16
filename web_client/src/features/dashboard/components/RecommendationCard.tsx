import React from 'react';
import { Star } from 'lucide-react';
import { getCoverUrl } from '@shared/utils/imageUtils';

interface RecommendationCardProps {
    book: any;
    settings: any;
    onClick: () => void;
    index: number;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({ book, settings, onClick, index }) => {
    return (
        <div
            className="group cursor-pointer flex flex-col"
            onClick={onClick}
        >
            <div className="relative aspect-[2/3] rounded-premium-lg overflow-hidden mb-4 border border-[var(--panel-border)] shadow-premium group-hover:scale-[1.04] group-hover:shadow-primary/30 transition-all duration-700 ring-1 ring-white/5">
                <img
                    src={getCoverUrl(book, book.cover_thumb || book.cover, settings.coverQuality)}
                    alt={book.title}
                    loading="lazy"
                    className="w-full h-full object-cover transition-all duration-1000 group-hover:scale-110"
                />
                <div className="absolute top-3 right-3 z-10">
                    <span className="bg-black/40 backdrop-blur-[var(--glass-blur)] text-white text-[9px] font-black px-2 py-0.5 rounded-premium-sm uppercase tracking-widest border border-white/5">
                        {book.book_type || 'EPUB'}
                    </span>
                </div>
                <div className="absolute top-10 right-3 z-10 flex flex-col gap-1.5 items-end">
                    {book.color_mode === 'color' && (
                        <span className="px-1.5 py-0.5 rounded-premium-sm text-[8px] font-black bg-gradient-to-r from-orange-400 to-pink-500 text-white uppercase tracking-wider shadow-sm">
                            A Color
                        </span>
                    )}
                    {book.is_uncensored && (
                        <span className="px-1.5 py-0.5 rounded-premium-sm text-[8px] font-black bg-red-500/10 text-red-500 uppercase tracking-wider border border-red-500/30">
                            S/C
                        </span>
                    )}
                </div>
                <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col justify-end p-5 backdrop-blur-[4px]">
                    <div className="flex items-center gap-1.5 text-yellow-400 mb-2">
                        <Star className="w-3 h-3 fill-current" />
                        <span className="text-xs font-black">{book.rating_average > 0 ? book.rating_average.toFixed(1) : '—'}</span>
                    </div>
                    <span className="text-sm font-black text-white leading-tight drop-shadow-lg">{book.cleanTitle || book.title}</span>
                    <span className="text-[10px] text-gray-400 mt-1 font-bold uppercase tracking-widest truncate">{book.author || 'Zeepub Author'}</span>
                    {book.categories && (
                        <span className="text-[9px] text-gray-500 font-medium italic mt-0.5 line-clamp-1 opacity-80">
                            {Array.isArray(book.categories) ? book.categories.join(', ') : book.categories}
                        </span>
                    )}
                </div>
            </div>
            <div className="text-center px-2">
                <p className="text-sm font-black text-white truncate mb-0.5 group-hover:text-primary transition-colors">{book.cleanTitle || book.title}</p>
                <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest opacity-60">Volumen {book.volumeNumber ?? book.volume ?? book.seriesIndex ?? (index + 1)}</p>
            </div>
        </div>
    );
};
