import React from 'react';
import { Star, Book } from 'lucide-react';
import { Series } from '@shared/types';
import { getCoverUrl } from '@shared/utils/imageUtils';
import { ProgressiveImage } from '@shared/components/ProgressiveImage';

interface SearchCardGridProps {
    series: Series;
    settings: any;
    onClick: () => void;
}

export const SearchCardGrid: React.FC<SearchCardGridProps> = React.memo(({ series, settings, onClick }) => {
    const pref = settings?.titleLanguage || 'english';
    const mainTitle = pref === 'spanish'
        ? (series.spanishTitle || series.englishTitle || series.title)
        : pref === 'romaji'
            ? (series.romajiTitle || series.title || series.englishTitle)
            : (series.englishTitle || series.romajiTitle || series.title);

    const subTitle = pref === 'english'
        ? (series.romajiTitle && series.romajiTitle !== mainTitle ? series.romajiTitle : (series.spanishTitle !== mainTitle ? series.spanishTitle : null))
        : (series.englishTitle && series.englishTitle !== mainTitle ? series.englishTitle : (series.romajiTitle !== mainTitle ? series.romajiTitle : null));

    return (
        <div
            onClick={onClick}
            className="group relative bg-[#0f1115] rounded-[2.5rem] overflow-hidden border border-white/5 hover:border-primary/40 shadow-2xl hover:shadow-primary/20 hover:-translate-y-2 transition-all duration-700 flex flex-col h-full cursor-pointer"
        >
            {/* Image Container */}
            <div className="relative aspect-[2/3] overflow-hidden bg-black/80">
                <ProgressiveImage
                    alt={mainTitle}
                    className="object-contain w-full h-full group-hover:scale-110 transition-transform duration-1000 opacity-90 group-hover:opacity-100"
                    src={getCoverUrl(series.coverUrl, series.coverThumbUrl, settings.coverQuality === 'pequeña' ? 'mediana' : settings.coverQuality)}
                />

                {/* Floating Badges */}
                <div className="absolute top-4 right-4 flex flex-col gap-2 scale-90 origin-top-right">
                    <span className="bg-black/80 backdrop-blur-xl text-white text-[9px] font-black px-2.5 py-1 rounded-lg uppercase tracking-[0.2em] border border-white/10">
                        {series.book_type || 'NOVELA'}
                    </span>
                    {series.color_mode === 'color' && (
                        <span className="bg-gradient-to-br from-orange-400 to-pink-500 text-white text-[8px] font-black px-2 py-0.5 rounded-md uppercase tracking-widest shadow-xl">COLOR</span>
                    )}
                    {series.is_uncensored && (
                        <span className="bg-red-600 text-white text-[8px] font-black px-2 py-0.5 rounded-md uppercase tracking-widest shadow-xl">S/C</span>
                    )}
                </div>

                {/* Overlay Info */}
                <div className="absolute inset-x-0 bottom-0 p-5 bg-gradient-to-t from-black via-black/40 to-transparent">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-1.5 text-yellow-500">
                            <Star className="w-3 h-3 fill-current" />
                            <span className="text-[11px] font-black">{series.rating > 0 ? series.rating.toFixed(1) : '—'}</span>
                        </div>
                        <div className="flex items-center gap-1 text-purple-400">
                            <Book className="w-3 h-3" />
                            <span className="text-[10px] font-black uppercase tracking-wider">{series.volumesCount} Vols</span>
                        </div>
                    </div>
                    <h3 className="text-white font-black text-base leading-tight line-clamp-2 drop-shadow-xl group-hover:text-primary transition-colors">
                        {mainTitle}
                    </h3>
                    {subTitle && (
                        <p className="text-gray-400 text-[10px] italic font-medium mt-1 line-clamp-1 truncate opacity-80">
                            {subTitle}
                        </p>
                    )}
                    <p className="text-gray-400 text-[10px] font-bold uppercase tracking-widest mt-1.5 truncate">
                        {series.author}
                    </p>
                    {series.genre && (
                        <p className="text-[9px] text-gray-500 italic opacity-60 truncate">
                            {series.genre}
                        </p>
                    )}
                </div>
            </div>

            {/* Hover Accent Glow */}
            <div className="absolute -inset-20 bg-primary/5 blur-[80px] opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
        </div>
    );
});
