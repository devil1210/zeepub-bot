import React, { useState } from 'react';
import { BookOpen, X } from 'lucide-react';
import { getCoverUrl } from '@shared/utils/imageUtils';

interface BookCoverProps {
    title: string;
    coverUrl: any;
    coverThumbUrl: string;
    settings: any;
}

export const BookCover: React.FC<BookCoverProps> = ({ title, coverUrl, coverThumbUrl, settings }) => {
    const [isFullscreen, setIsFullscreen] = useState(false);

    return (
        <>
            <div
                className="relative w-[85%] sm:w-[50%] lg:w-full mx-auto lg:mx-0 group cursor-pointer"
                onClick={() => setIsFullscreen(true)}
            >
                {/* Outer Glow */}
                <div className="absolute -inset-4 bg-primary/20 rounded-[2.5rem] blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-1000"></div>

                <div className="relative aspect-[2/3] rounded-[2.2rem] overflow-hidden shadow-premium border border-white/10 group-hover:border-white/30 group-hover:-translate-y-2 transition-all duration-700 bg-white/5">
                    <img
                        src={getCoverUrl(coverUrl, coverThumbUrl, 'mediana')}
                        alt={title}
                        className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"></div>

                    {/* Shimmer Effect */}
                    <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-[1.5s] ease-in-out pointer-events-none z-10"></div>

                    {/* Floating Zoom Badge */}
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-black/20 z-20">
                        <div className="p-4 bg-white/10 backdrop-blur-md rounded-full border border-white/20 shadow-lg group-hover:scale-110 transition-transform duration-300">
                            <BookOpen className="w-8 h-8 text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.5)]" />
                        </div>
                    </div>
                </div>
            </div>

            {/* Fullscreen Overlay */}
            {isFullscreen && (
                <div
                    className="fixed inset-0 z-[100] bg-black/95 flex items-center justify-center p-4 animate-in fade-in duration-300"
                    onClick={() => setIsFullscreen(false)}
                >
                    <button
                        className="absolute top-6 right-6 p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors z-[101]"
                        onClick={(e) => { e.stopPropagation(); setIsFullscreen(false); }}
                    >
                        <X className="w-6 h-6 text-white" />
                    </button>
                    <img
                        src={getCoverUrl(coverUrl, coverThumbUrl, 'original')}
                        alt={title}
                        className="max-w-full max-h-full object-contain rounded-lg shadow-2xl animate-in zoom-in-95 duration-300"
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
            )}
        </>
    );
};
