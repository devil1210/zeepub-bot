import React from 'react';
import { Calendar, Clock, Download, Hash, Languages, PenTool, Star, User } from 'lucide-react';

interface BookHeaderProps {
    displayTitle: string;
    romajiTitle: string;
    author: string;
    rating: number;
    ratingCount: number;
    downloadCount: number;
    illustrator: string;
    volumeNumber: number;
    publishedDate: string;
    translator: string;
    lastUpdated: string;
    group: string;
    color_mode?: string;
    is_uncensored?: boolean;
    onSearch: (term: string, type?: string) => void;
}

export const BookHeader: React.FC<BookHeaderProps> = ({
    displayTitle,
    romajiTitle,
    author,
    rating,
    ratingCount,
    downloadCount,
    illustrator,
    volumeNumber,
    publishedDate,
    translator,
    lastUpdated,
    group,
    color_mode,
    is_uncensored,
    onSearch
}) => {
    return (
        <div className="relative">
            {/* Mobile: Stats Liquid Card */}
            <div className="md:hidden mb-6">
                <div className="glass-panel p-4 rounded-premium-sm border border-white/10 shadow-lg flex items-center justify-between">
                    <div className="flex flex-col items-center gap-1">
                        <span className="text-[10px] uppercase font-black text-gray-400 tracking-wider">Rating</span>
                        <div className="flex items-center gap-1.5 text-yellow-400">
                            <Star className="w-4 h-4 fill-yellow-400" />
                            <span className="text-white font-bold text-lg">{rating > 0 ? rating.toFixed(1) : '-'}</span>
                        </div>
                    </div>
                    <div className="w-px h-8 bg-white/10" />
                    <div className="flex flex-col items-center gap-1">
                        <span className="text-[10px] uppercase font-black text-gray-400 tracking-wider">Descargas</span>
                        <div className="flex items-center gap-1.5 text-primary">
                            <Download className="w-4 h-4" />
                            <span className="text-white font-bold text-lg">{downloadCount}</span>
                        </div>
                    </div>
                    <div className="w-px h-8 bg-white/10" />
                    <div className="flex flex-col items-center gap-1">
                        <span className="text-[10px] uppercase font-black text-gray-400 tracking-wider">Año</span>
                        <div className="flex items-center gap-1.5 text-emerald-400">
                            <Calendar className="w-4 h-4" />
                            <span className="text-white font-bold text-lg">{publishedDate?.split('-')[0] || 'N/A'}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Badges Row */}
            <div className="mb-4 flex flex-wrap items-center gap-2 text-[10px] font-black uppercase tracking-wider">
                <button
                    onClick={() => onSearch(group, 'group')}
                    className="bg-primary/10 text-primary border border-primary/20 px-3 py-1.5 rounded-full hover:bg-primary hover:text-white transition-colors cursor-pointer"
                >
                    {group}
                </button>
                {color_mode === 'color' && (
                    <span className="bg-gradient-to-r from-orange-400 to-pink-500 text-white px-3 py-1.5 rounded-full shadow-lg shadow-orange-500/20">
                        A Color
                    </span>
                )}
                {is_uncensored && (
                    <span className="bg-red-500/10 text-red-500 border border-red-500/20 px-3 py-1.5 rounded-full shadow-lg shadow-red-500/10">
                        Sin Censura
                    </span>
                )}
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white leading-tight mb-2 tracking-tight drop-shadow-xl">
                {displayTitle}
            </h1>
            <h2 className="text-base sm:text-lg text-white/50 italic font-medium mb-6 leading-relaxed">
                {romajiTitle}
            </h2>

            {/* Desktop Stats Row - Simplified */}
            <div className="hidden md:flex flex-wrap items-center gap-x-8 gap-y-3 text-sm text-gray-400 border-b border-white/5 pb-6 mb-2">
                <button onClick={() => onSearch(author, 'author')} className="flex items-center gap-2 text-white group">
                    <User className="w-4 h-4 text-primary group-hover:scale-110 transition-transform" />
                    <span className="font-bold group-hover:underline cursor-pointer group-hover:text-primary transition-colors">{author}</span>
                </button>
                <div className="flex items-center gap-2">
                    <Hash className="w-4 h-4 text-gray-500" />
                    <span>{(!volumeNumber || volumeNumber === 0) ? 'Volumen Único' : `Volumen ${volumeNumber}`}</span>
                </div>
                {translator && (
                    <button onClick={() => onSearch(translator, 'translator')} className="flex items-center gap-2 group hover:text-white transition-colors">
                        <Languages className="w-4 h-4 text-indigo-400" />
                        <span className="font-bold group-hover:underline">{translator}</span>
                    </button>
                )}
            </div>
        </div>
    );
};
