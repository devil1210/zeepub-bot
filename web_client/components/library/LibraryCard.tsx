import React from 'react';

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

export const LibraryCard: React.FC<LibraryCardProps> = ({ book, onClick }) => {
    return (
        <div
            onClick={onClick}
            className={`group relative flex flex-col gap-4 rounded-[2.5rem] p-4 transition-all duration-700 glass-panel hover:bg-white/[0.08] hover:border-primary/40 hover:-translate-y-2 cursor-pointer shadow-premium ${book.isNew ? 'border-primary/30 ring-1 ring-primary/20' : ''}`}
        >
            {/* Status Badges */}
            <div className="absolute top-6 right-6 z-20 flex flex-col gap-2">
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

            {/* Image Container */}
            <div className="relative aspect-[2/3] w-full overflow-hidden rounded-[1.75rem] bg-white/5 shadow-2xl border border-white/10">
                <div
                    className="absolute inset-0 bg-cover bg-center transition-all duration-1000 group-hover:scale-110 grayscale-[30%] group-hover:grayscale-0"
                    style={{ backgroundImage: `url("${book.cover}")` }}
                ></div>

                <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black via-black/40 to-transparent"></div>

                {book.updated && (
                    <div className="absolute bottom-4 left-4 flex items-center gap-2">
                        <div className="relative flex h-3 w-3">
                            <div className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></div>
                            <div className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></div>
                        </div>
                        <span className="text-[10px] font-black text-white uppercase tracking-[0.2em] drop-shadow-md">Updated</span>
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="flex flex-col gap-1 px-1">
                <h3 className="truncate text-[15px] font-black text-white group-hover:text-primary transition-colors tracking-tight">{book.title}</h3>
                <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-gray-500">
                    <span>Vol {book.vol}</span>
                    <span className="opacity-50">{book.time}</span>
                </div>
            </div>

            {/* Hover Accent Glow */}
            <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
        </div>
    );
};
