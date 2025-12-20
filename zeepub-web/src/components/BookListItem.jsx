import React from 'react';

const BookListItem = ({ book, onDownload, isFacebookPublisher, onFacebookPost, isLast }) => {
    const { title, author, summary, cover_url } = book;

    // Extraer formato del summary si existe
    const formatMatch = summary?.match(/Format:\s*(\w+)/i);
    const format = formatMatch ? formatMatch[1] : 'EPUB';

    return (
        <div
            onClick={() => onDownload(book)}
            style={{ display: 'flex', alignItems: 'center', padding: '11px 16px', cursor: 'pointer', borderBottom: isLast ? 'none' : '1px solid rgba(255,255,255,0.01)' }}
            className="transition-colors active:bg-white/10"
        >
            <div style={{ flex: 'none', width: '44px', height: '44px', borderRadius: '50%', backgroundColor: '#17212b', display: 'flex', alignItems: 'center', justifyCenter: 'center', overflow: 'hidden', marginRight: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
                {cover_url ? (
                    <img
                        src={cover_url}
                        alt={title}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        loading="lazy"
                    />
                ) : (
                    <span style={{ fontSize: '22px', opacity: 0.7 }}>📖</span>
                )}
            </div>

            <div style={{ flex: 1, minWidth: 0, paddingRight: '8px' }}>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: '17px', fontWeight: '600', color: '#ffffff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', lineHeight: 1.2 }}>
                        {title}
                    </span>
                    <span style={{ fontSize: '14px', color: '#ffffff', opacity: 0.8, marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', lineHeight: 1.2 }}>
                        {author} • <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#2481cc', textTransform: 'uppercase' }}>{format}</span>
                    </span>
                </div>
            </div>

            <div style={{ flex: 'none', display: 'flex', alignItems: 'center', gap: '12px' }}>
                {isFacebookPublisher && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onFacebookPost(book);
                        }}
                        style={{ padding: '6px', backgroundColor: 'rgba(36, 129, 204, 0.05)', color: '#2481cc', borderRadius: '8px', border: '1px solid rgba(36, 129, 204, 0.1)', cursor: 'pointer' }}
                        className="active:scale-90 transition-all"
                        title="Publicar en Facebook"
                    >
                        <svg style={{ width: '14px', height: '14px' }} fill="currentColor" viewBox="0 0 24 24">
                            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.791-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                        </svg>
                    </button>
                )}
                <div style={{ color: '#546675' }}>
                    <svg style={{ width: '16px', height: '16px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                    </svg>
                </div>
            </div>
        </div>
    );
};

export default BookListItem;
