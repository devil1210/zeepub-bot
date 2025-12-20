import React from 'react';

const NavigationListItem = ({ item, onNavigate, isLast }) => {
    const { title, summary, cover_url } = item;

    return (
        <div
            onClick={() => onNavigate(item)}
            className={`group relative flex items-center px-5 py-3 transition-colors active:bg-white/10 cursor-pointer ${!isLast ? 'border-b border-[rgba(255,255,255,0.06)]' : ''}`}
        >
            <div className="flex-none w-11 h-11 rounded-full bg-telegram-dark flex items-center justify-center text-xl overflow-hidden shadow-inner border border-white/5 mr-4 transition-transform active:scale-90">
                {cover_url ? (
                    <img
                        src={cover_url}
                        alt={title}
                        className="w-full h-full object-cover"
                        loading="lazy"
                    />
                ) : (
                    <span className="opacity-70">📁</span>
                )}
            </div>

            <div className="flex-1 min-w-0 pr-4">
                <div className="flex flex-col">
                    <span className="text-[14px] font-semibold text-white leading-tight truncate">
                        {title}
                    </span>
                    {summary && (
                        <span className="text-[12px] text-telegram-hint mt-0.5 truncate leading-tight opacity-90">
                            {summary}
                        </span>
                    )}
                </div>
            </div>

            <div className="flex-none text-gray-600 transition-colors">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                </svg>
            </div>
        </div>
    );
};

export default NavigationListItem;
