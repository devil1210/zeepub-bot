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
        <div>
            {/* Group/Translator Badges */}
            <div className="mb-4 flex flex-wrap items-center gap-2 text-[10px] font-black uppercase tracking-wider">
                <button
                    onClick={() => onSearch(group, 'group')}
                    className="bg-primary/10 text-primary border border-primary/20 px-2 py-1 rounded-md hover:bg-primary hover:text-white transition-colors cursor-pointer"
                >
                    {group}
                </button>
                <span className="text-gray-400 dark:text-gray-600 px-1">/</span>
                <button
                    onClick={() => onSearch(translator, 'translator')}
                    className="bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-400 border border-black/5 dark:border-white/10 px-2 py-1 rounded-md hover:bg-gray-200 dark:hover:bg-white/10 hover:text-black dark:hover:text-white transition-colors cursor-pointer"
                >
                    {translator}
                </button>
                {color_mode === 'color' && (
                    <span className="bg-gradient-to-r from-orange-400 to-pink-500 text-white px-2 py-1 rounded-md shadow-sm">
                        A Color
                    </span>
                )}
                {is_uncensored && (
                    <span className="bg-red-500/10 text-red-500 border border-red-500/20 px-2 py-1 rounded-md">
                        Sin Censura
                    </span>
                )}
            </div>

            <h1 className="text-2xl sm:text-3xl lg:text-5xl font-extrabold text-gray-900 dark:text-white leading-tight mb-2">
                {displayTitle}
            </h1>
            <h2 className="text-sm sm:text-lg text-gray-500 dark:text-gray-400 italic font-serif mb-6 leading-relaxed">
                {romajiTitle}
            </h2>

            {/* Author/Stats Row */}
            <div className="flex flex-wrap items-center gap-x-6 gap-y-3 text-sm text-gray-600 dark:text-gray-400 border-b border-black/5 dark:border-white/5 pb-6 mb-2">
                <button onClick={() => onSearch(author, 'author')} className="flex items-center gap-2 text-gray-900 dark:text-white group">
                    <User className="w-4 h-4 text-primary group-hover:scale-110 transition-transform" />
                    <span className="font-bold group-hover:underline cursor-pointer group-hover:text-primary transition-colors">{author}</span>
                </button>

                <div className="flex items-center gap-1.5 text-yellow-500">
                    <Star className="w-4 h-4 fill-current" />
                    <span className="text-gray-900 dark:text-white font-bold">{rating > 0 ? rating.toFixed(1) : '—'}</span>
                    {ratingCount > 0 && (
                        <span className="text-xs text-gray-400 font-medium">({ratingCount})</span>
                    )}
                </div>
                <div className="flex items-center gap-1.5 text-primary">
                    <Download className="w-4 h-4" />
                    <span className="text-gray-900 dark:text-white font-bold">{downloadCount}</span>
                </div>

                <button onClick={() => onSearch(illustrator, 'illustrator')} className="flex items-center gap-2 group hover:text-black dark:hover:text-gray-200 transition-colors">
                    <PenTool className="w-4 h-4" />
                    <span>{illustrator}</span>
                </button>
                <div className="flex items-center gap-2">
                    <Hash className="w-4 h-4" />
                    <span>{(!volumeNumber || volumeNumber === 0) ? 'Volumen Único' : `Volumen ${volumeNumber}`}</span>
                </div>
                <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    <span>{publishedDate}</span>
                </div>
                {translator && (
                    <button onClick={() => onSearch(translator, 'translator')} className="flex items-center gap-2 group hover:text-black dark:hover:text-gray-200 transition-colors">
                        <Languages className="w-4 h-4 text-indigo-500" />
                        <span className="font-bold group-hover:underline">{translator}</span>
                    </button>
                )}
                {lastUpdated !== 'N/A' && (
                    <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                        <Clock className="w-4 h-4" />
                        <span className="font-bold">Actualizado: {lastUpdated}</span>
                    </div>
                )}
            </div>
        </div>
    );
};
