import React from 'react';

const NavigationListItem = ({ item, onNavigate, isLast }) => {
    const { title, summary, cover_url } = item;

    return (
        <div
            onClick={() => onNavigate(item)}
            style={{ display: 'flex', alignItems: 'center', padding: '11px 16px', cursor: 'pointer', borderBottom: isLast ? 'none' : '1px solid rgba(255,255,255,0.06)' }}
            className="transition-colors active:bg-white/10"
        >
            <div style={{ flex: 'none', width: '44px', height: '44px', borderRadius: '50%', backgroundColor: '#17212b', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', marginRight: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
                {cover_url ? (
                    <img
                        src={cover_url}
                        alt={title}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        loading="lazy"
                    />
                ) : (
                    <span style={{ fontSize: '22px', opacity: 0.7 }}>📁</span>
                )}
            </div>

            <div style={{ flex: 1, minWidth: 0, paddingRight: '8px' }}>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: '17px', fontWeight: '600', color: '#ffffff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', lineHeight: 1.2 }}>
                        {title}
                    </span>
                    {summary && (
                        <span style={{ fontSize: '14px', color: '#ffffff', opacity: 0.7, marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', lineHeight: 1.2 }}>
                            {summary}
                        </span>
                    )}
                </div>
            </div>

            <div style={{ flex: 'none', color: '#546675', marginLeft: '8px' }}>
                <svg style={{ width: '16px', height: '16px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                </svg>
            </div>
        </div>
    );
};

export default NavigationListItem;
