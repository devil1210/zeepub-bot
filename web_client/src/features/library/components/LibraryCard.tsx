import React, { memo } from 'react';
import { Send, CheckCircle2 } from 'lucide-react';
import { ProgressiveImage } from '@shared/components/ProgressiveImage';
import { useNavigation } from '@shared/contexts/NavigationContext';
import { api } from '@shared/services/api';

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
    const { state: navState } = useNavigation();
    const [status, setStatus] = React.useState<'idle' | 'loading' | 'success' | 'error'>('idle');

    const handlePost = async (e: React.MouseEvent) => {
        e.stopPropagation();
        if (!navState.selectedChannelId || status === 'loading') return;

        setStatus('loading');
        try {
            // Assume we have an endpoint for direct publishing
            await api.publishToChannel(book.id, navState.selectedChannelId);
            setStatus('success');
            setTimeout(() => setStatus('idle'), 3000);
        } catch (err) {
            console.error("Error publishing:", err);
            setStatus('error');
            setTimeout(() => setStatus('idle'), 3000);
        }
    };

    const hasChannel = !!navState.selectedChannelId;

    return (
        <div
            onClick={onClick}
            className={`group relative flex flex-col rounded-premium-lg transition-all duration-500 glass-panel hover:border-primary/50 hover:shadow-premium overflow-hidden cursor-pointer bg-white/5 border-white/5 ${book.isNew ? 'ring-1 ring-primary/30' : ''} ${hasChannel ? 'ring-2 ring-primary/40 shadow-premium' : 'shadow-premium'}`}
        >
            {/* Image Container */}
            <div className="relative aspect-[2/3] w-full shrink-0 overflow-hidden bg-black/40">
                <div className="absolute top-3 right-3 z-20 flex flex-col gap-2 items-end">
                    {book.isNew && (
                        <div className="bg-primary text-white px-3 py-1 rounded-premium-sm text-[9px] font-black uppercase tracking-widest shadow-lg animate-pulse backdrop-blur-[var(--glass-blur)]">
                            Nuevo
                        </div>
                    )}
                    {book.updated && (
                        <div className="bg-emerald-500/80 text-white px-3 py-1 rounded-premium-sm text-[9px] font-black uppercase tracking-widest shadow-lg backdrop-blur-[var(--glass-blur)] border border-white/10">
                            Upd
                        </div>
                    )}
                </div>

                <ProgressiveImage
                    src={book.cover}
                    alt={book.title}
                    className="w-full h-full object-contain transition-all duration-1000 group-hover:scale-105"
                    containerClassName="w-full h-full"
                />

                {/* Post Overlay Button */}
                {hasChannel && (
                    <div className="absolute inset-0 z-30 flex items-center justify-center bg-black/40 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-all duration-300">
                        <button
                            onClick={handlePost}
                            disabled={status === 'loading'}
                            className={`px-8 py-4 rounded-full font-black uppercase tracking-[0.2em] text-[12px] transition-all flex items-center gap-3 shadow-2xl ${status === 'success'
                                ? 'bg-emerald-500 text-white scale-110'
                                : status === 'error'
                                    ? 'bg-red-500 text-white'
                                    : 'bg-primary text-white hover:scale-110 active:scale-95'
                                }`}
                        >
                            {status === 'loading' ? (
                                <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                            ) : status === 'success' ? (
                                <CheckCircle2 className="w-5 h-5" />
                            ) : (
                                <Send className="w-5 h-5" />
                            )}
                            {status === 'success' ? 'Enviado' : status === 'error' ? 'Error' : 'Postear'}
                        </button>
                    </div>
                )}

                {/* Subtle Gradient for depth */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60 group-hover:opacity-80 transition-opacity duration-500 pointer-events-none"></div>

                {/* Glow Effect */}
                <div className="absolute -inset-full bg-primary/10 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
            </div>

            {/* Content */}
            <div className={`flex flex-col gap-2 p-5 relative z-10 flex-1 transition-colors ${hasChannel ? 'bg-primary/5' : 'bg-white/[0.02]'}`}>
                <h3 className="line-clamp-2 text-[15px] font-black text-white group-hover:text-primary transition-colors tracking-tight leading-tight min-h-[2.5em]">{book.title}</h3>

                <div className="mt-auto pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-gray-400">
                    <span className="bg-white/5 px-2 py-1 rounded-premium-sm border border-white/5">Vol {book.vol}</span>
                    <span className="opacity-50">{book.time}</span>
                </div>
            </div>
        </div>
    );
});

LibraryCard.displayName = 'LibraryCard';
