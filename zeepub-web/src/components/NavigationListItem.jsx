import React from 'react';

const NavigationListItem = ({ item, onNavigate }) => {
    const { title, summary, cover_url } = item;

    return (
        <div
            onClick={() => onNavigate(item)}
            className="flex items-center px-4 py-3 cursor-pointer hover:bg-white/5 active:bg-white/10 transition-colors border-b border-white/5 last:border-b-0"
        >
            <div className="flex-shrink-0 mr-4">
                <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-lg overflow-hidden shadow-inner">
                    {cover_url ? (
                        <img
                            src={cover_url}
                            alt={title}
                            className="w-full h-full object-cover"
                            loading="lazy"
                        />
                    ) : (
                        <span className="text-white">📚</span>
                    )}
                </div>
            </div>

            <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-white truncate">
                    {title}
                </h3>
                {summary && (
                    <p className="text-xs text-gray-400 truncate mt-0.5">
                        {summary}
                    </p>
                )}
            </div>

            <div className="flex-shrink-0 ml-3 text-gray-600">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
                </svg>
            </div>
        </div>
    );
};

export default NavigationListItem;
