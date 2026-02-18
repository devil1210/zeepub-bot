import React, { memo } from 'react';
import { ProgressiveImage } from '@shared/components/ProgressiveImage';

interface LibraryCardProps {
    book: {
        id: any;
        title: string;
        author: string;
        vol: string | number;
        time: string;
        cover: string;
        isNew?: boolean;
        updated?: boolean;
    };
    onClick: () => void;
}

export const LibraryCard = memo<LibraryCardProps>(({ book, onClick }) => {
    return (
        <div
            onClick={onClick}
            className={`group relative flex flex-col rounded-[2.5rem] transition-all duration-500 glass-panel hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 overflow-hidden cursor-pointer bg-slate-900/50 ${book.isNew ? 'border-primary/30 ring-1 ring-primary/20' : 'border-white/5'}`}
        >
            {/* Image Container */}
            <div className="relative aspect-[2/3] w-full shrink-0 overflow-hidden">
                <div className="absolute top-3 right-3 z-20 flex flex-col gap-2 items-end">
                    {book.isNew && (
                        <div className="bg-primary text-white px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest shadow-xl animate-pulse">
                            Nuevo
                        </div>
                    )}
                    {book.updated && (
                        <div className="bg-emerald-500 text-white px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest shadow-xl">
                            Upd
                        </div>
                    )}
                </div>

                <ProgressiveImage
                    src={book.cover}
                    alt={book.title}
                    className="w-full h-full object-cover transition-all duration-1000 group-hover:scale-110 grayscale-[30%] group-hover:grayscale-0"
                    containerClassName="w-full h-full"
                />

                {/* Subtle Gradient for depth only, no text overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-40 transition-opacity duration-500 pointer-events-none"></div>

                {/* Glow Effect */}
                <div className="absolute -inset-full bg-primary/20 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
            </div>

            {/* Content */}
            <div className="flex flex-col gap-2 p-5 relative z-10 flex-1 bg-white/5 backdrop-blur-sm">
                <h3 className="line-clamp-2 text-[15px] font-black text-white group-hover:text-primary transition-colors tracking-tight leading-tight min-h-[2.5em]">{book.title}</h3>

                <div className="mt-auto pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-gray-400">
                    <span className="bg-white/5 px-2 py-1 rounded border border-white/5">Vol {book.vol}</span>
                    <span className="opacity-50">{book.time}</span>
                </div>
            </div>
        </div>
    );
});

LibraryCard.displayName = 'LibraryCard';
