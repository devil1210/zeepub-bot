import React from 'react';

interface QuoteWidgetProps {
    quote: string;
    author: string;
    settings: any;
}

export const QuoteWidget: React.FC<QuoteWidgetProps> = ({ quote, author, settings }) => {
    return (
        <div className="glass-panel p-10 rounded-[2.5rem] border border-white/5 bg-gradient-to-br from-primary/10 via-transparent to-transparent relative overflow-hidden group shadow-2xl">
            <div className="absolute -top-10 -left-10 text-white opacity-[0.03] font-black text-9xl">“</div>
            <p className="text-gray-300 text-base italic font-medium leading-relaxed relative z-10 text-center px-4">{quote}</p>
            <div className="flex items-center justify-center gap-4 mt-6 relative z-10">
                <div className="w-8 h-px bg-white/10"></div>
                <p className="text-primary text-[10px] font-black uppercase tracking-[0.2em] opacity-80">{author}</p>
                <div className="w-8 h-px bg-white/10"></div>
            </div>
            <div
                className="absolute -right-8 -bottom-8 w-32 h-32 bg-primary/5 rounded-full blur-3xl group-hover:scale-150 transition-all duration-1000"
                style={{ opacity: settings.cardGlowIntensity }}
            ></div>
        </div>
    );
};
