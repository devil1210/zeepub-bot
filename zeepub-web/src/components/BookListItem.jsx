import React from 'react';

const BookListItem = ({ book, onDownload, isFacebookPublisher, onFacebookPost }) => {
    const { title, author, summary, cover_url } = book;

    // Extraer formato del summary si existe
    const formatMatch = summary?.match(/Format:\s*(\w+)/i);
    const format = formatMatch ? formatMatch[1] : null;
    const cleanSummary = summary?.replace(/Format:\s*\w+\s*/i, '').trim();

    return (
        <div
            onClick={() => onDownload(book)}
            className="flex items-center px-4 py-3 cursor-pointer hover:bg-white/5 active:bg-white/10 transition-colors border-b border-white/5 last:border-b-0"
        >
            <div className="flex-shrink-0 mr-4">
                <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-lg overflow-hidden shadow-inner">
                    {cover_url ? (
                        <img
                            src={cover_url}
                            alt={title}
                            className="w-full h-full object-cover"
                            loading="lazy"
                        />
                    ) : (
                        <span className="text-gray-400">📚</span>
                    )}
                </div>
            </div>

            <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-white truncate">
                    {title}
                </h3>
                <p className="text-xs text-gray-400 truncate mt-0.5">
                    {author} {format && `• ${format}`}
                </p>
                {cleanSummary && (
                    <p className="text-[10px] text-gray-500 truncate mt-0.5 opacity-80">
                        {cleanSummary}
                    </p>
                )}
            </div>

            <div className="flex items-center ml-2">
                {isFacebookPublisher && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onFacebookPost(book);
                        }}
                        className="p-2 text-blue-400 hover:text-blue-300 transition-colors mr-1"
                        title="Publicar en Facebook"
                    >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.791-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                        </svg>
                    </button>
                )}
                <div className="text-gray-600 ml-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                    </svg>
                </div>
            </div>
        </div>
    );
};

export default BookListItem;
