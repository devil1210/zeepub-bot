import React from 'react';

const BookListItem = ({ book, onDownload, isFacebookPublisher, onFacebookPost, isLast }) => {
    const { title, author, summary, cover_url } = book;

    // Extraer formato del summary si existe
    const formatMatch = summary?.match(/Format:\s*(\w+)/i);
    const format = formatMatch ? formatMatch[1] : 'EPUB';

    return (
        <div
            onClick={() => onDownload(book)}
            className={`group relative flex items-center px-4 py-[11px] transition-colors active:bg-white/10 cursor-pointer ${!isLast ? 'border-b border-[rgba(255,255,255,0.06)]' : ''}`}
        >
            <div className="flex-none w-11 h-11 rounded-full bg-telegram-dark flex items-center justify-center text-[22px] overflow-hidden shadow-inner border border-white/5 mr-4 transition-transform active:scale-90">
                {cover_url ? (
                    <img
                        src={cover_url}
                        alt={title}
                        className="w-full h-full object-cover"
                        loading="lazy"
                    />
                ) : (
                    <span className="opacity-70 grayscale">📖</span>
                )}
            </div>

            <div className="flex-1 min-w-0 pr-2">
                <div className="flex flex-col">
                    <span className="text-[17px] font-semibold text-white leading-tight truncate">
                        {title}
                    </span>
                    <span className="text-[14px] text-telegram-hint mt-0.5 truncate leading-tight">
                        {author} • <span className="text-[11px] font-bold text-telegram-link uppercase tracking-tighter">{format}</span>
                    </span>
                </div>
            </div>

            <div className="flex-none flex items-center gap-3">
                {isFacebookPublisher && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onFacebookPost(book);
                        }}
                        className="p-1.5 bg-blue-600/5 text-telegram-link rounded-lg hover:bg-blue-600/10 transition-all border border-blue-500/10 active:scale-90"
                        title="Publicar en Facebook"
                    >
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.791-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                        </svg>
                    </button>
                )}
                <div className="text-[#546675]">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                    </svg>
                </div>
            </div>
        </div>
    );
};

export default BookListItem;
