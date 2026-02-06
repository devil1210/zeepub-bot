import React from 'react';
import { Star, Download, Book, PlusCircle } from 'lucide-react';
import { Series } from '@shared/types';
import { getCoverUrl } from '@shared/utils/imageUtils';
import { ProgressiveImage } from '@shared/components/ProgressiveImage';

interface SearchCardListProps {
    series: Series;
    settings: any;
    onClick: () => void;
}

export const SearchCardList: React.FC<SearchCardListProps> = React.memo(({ series, settings, onClick }) => {
    return (
        <div
            onClick={onClick}
            className="group flex gap-5 p-4 rounded-[2rem] glass-panel hover:bg-white/[0.07] hover:border-white/20 hover:shadow-[0_20px_40px_-10px_rgba(0,0,0,0.4)] transition-all duration-500 cursor-pointer relative overflow-hidden mb-4"
        >
            {/* Left: Cover Image */}
            <div className="relative shrink-0 w-[100px] sm:w-[120px] aspect-[2/3] shadow-2xl rounded-premium-sm overflow-hidden bg-white/5 border border-white/10 group-hover:scale-[1.03] transition-transform duration-700">
                <ProgressiveImage
                    alt={series.title}
                    className="w-full h-full object-cover transition-all duration-1000 group-hover:scale-110"
                    src={getCoverUrl(series.coverUrl, series.coverThumbUrl, settings.coverQuality)}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
            </div>

            {/* Right: Details */}
            <div className="flex flex-col flex-1 min-w-0 py-1">
                {/* Title & Action */}
                <div className="flex justify-between items-start gap-4 mb-2">
                    <h3 className="text-white font-black text-base sm:text-lg md:text-xl leading-tight line-clamp-2 tracking-tight group-hover:text-primary transition-colors flex-1 min-w-0">
                        {series.title}
                    </h3>
                    <button
                        onClick={(e) => { e.stopPropagation(); }}
                        className="p-2.5 rounded-premium-sm bg-white/5 hover:bg-primary text-gray-400 hover:text-white transition-all duration-300 transform group-hover:scale-110 shadow-lg active:scale-90 shrink-0"
                    >
                        <PlusCircle className="w-4 h-4" />
                    </button>
                </div>

                {/* Author & Genres */}
                <div className="mb-4">
                    <p className="text-[10px] sm:text-xs text-primary font-black uppercase tracking-[0.15em] opacity-90">
                        {series.author}
                    </p>
                    {series.genre && (
                        <p className="text-[10px] sm:text-[11px] text-gray-500 font-medium italic opacity-70 mt-1 line-clamp-1">
                            {series.genre}
                        </p>
                    )}
                </div>

                {/* Stats Row */}
                <div className="flex items-center gap-5 text-[10px] font-black uppercase tracking-[0.15em] text-gray-500 mb-4">
                    <div className="flex items-center gap-1.5 text-yellow-500">
                        <Star className="w-3.5 h-3.5 fill-current" />
                        <span className="text-gray-300">{series.rating > 0 ? series.rating.toFixed(1) : '—'}</span>
                        <span className="opacity-50 font-bold">({series.voteCount || 0})</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-blue-400">
                        <Download className="w-3.5 h-3.5" />
                        <span>{series.downloadCount || 0}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-purple-400">
                        <Book className="w-3.5 h-3.5" />
                        <span>{series.volumesCount} Vols</span>
                    </div>
                </div>

                {/* Metadata Tags */}
                <div className="flex flex-wrap items-center gap-2 mt-auto">
                    {series.book_type && (
                        <span className="px-2.5 py-1 rounded-lg text-[8px] sm:text-[9px] font-black bg-white/5 text-gray-400 uppercase tracking-widest border border-white/10 group-hover:border-primary/40 group-hover:text-white transition-all">
                            {series.book_type}
                        </span>
                    )}
                    {series.format && (
                        <span className="px-2.5 py-1 rounded-lg text-[8px] sm:text-[9px] font-black bg-emerald-500/10 text-emerald-400 uppercase tracking-widest border border-emerald-500/20">
                            {series.format}
                        </span>
                    )}
                    {series.color_mode === 'color' && (
                        <span className="px-2.5 py-1 rounded-lg text-[8px] sm:text-[9px] font-black bg-gradient-to-r from-orange-400 to-pink-500 text-white uppercase tracking-widest shadow-lg">
                            Color
                        </span>
                    )}
                    {series.is_uncensored && (
                        <span className="px-2.5 py-1 rounded-lg text-[8px] sm:text-[9px] font-black bg-red-500/10 text-red-500 uppercase tracking-widest border border-red-500/20">
                            S/C
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
});
