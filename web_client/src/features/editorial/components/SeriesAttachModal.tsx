import React from 'react';
import { Link2, X, Search, Loader2 } from 'lucide-react';

interface SeriesAttachModalProps {
    isOpen: boolean;
    onClose: () => void;
    searchQuery: string;
    setSearchQuery: (val: string) => void;
    onSearch: () => void;
    searching: boolean;
    searchResults: any[];
    onAttach: (bookId: string) => void;
}

export const SeriesAttachModal: React.FC<SeriesAttachModalProps> = ({
    isOpen,
    onClose,
    searchQuery,
    setSearchQuery,
    onSearch,
    searching,
    searchResults,
    onAttach,
}) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-white/10 rounded-3xl p-6 max-w-xl w-full space-y-4 shadow-2xl">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <Link2 className="w-4 h-4 text-indigo-400" /> Vincular Libro EPUB a la Serie
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <X className="w-4 h-4" />
                    </button>
                </div>

                <div className="flex gap-2">
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && onSearch()}
                        placeholder="Buscar libro por título o hash..."
                        className="flex-1 px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white"
                    />
                    <button
                        onClick={onSearch}
                        disabled={searching}
                        className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md"
                    >
                        {searching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                    </button>
                </div>

                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {searchResults.map((sb) => (
                        <div
                            key={sb.id}
                            className="p-3 rounded-2xl bg-slate-950/70 border border-white/5 flex items-center justify-between gap-3 text-xs"
                        >
                            <div className="min-w-0">
                                <div className="font-bold text-white truncate">{sb.title}</div>
                                <div className="text-[10px] text-gray-400">Vol. {sb.volume || '—'} • {sb.author || 'Sin autor'}</div>
                            </div>
                            <button
                                onClick={() => onAttach(sb.id)}
                                className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shrink-0"
                            >
                                Vincular
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
