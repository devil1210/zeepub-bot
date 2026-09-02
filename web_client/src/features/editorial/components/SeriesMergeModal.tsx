import React from 'react';
import { GitMerge, X } from 'lucide-react';

interface SeriesMergeModalProps {
    isOpen: boolean;
    onClose: () => void;
    mergeSourceHash: string;
    setMergeSourceHash: (val: string) => void;
    onConfirmMerge: () => void;
    merging: boolean;
}

export const SeriesMergeModal: React.FC<SeriesMergeModalProps> = ({
    isOpen,
    onClose,
    mergeSourceHash,
    setMergeSourceHash,
    onConfirmMerge,
    merging,
}) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-white/10 rounded-3xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                        <GitMerge className="w-4 h-4 text-purple-400" /> Fusionar con Otra Serie
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <X className="w-4 h-4" />
                    </button>
                </div>
                <p className="text-xs text-gray-400">
                    Introduce el hash o identificador de la serie duplicada que deseas absorber dentro de esta serie principal.
                </p>
                <input
                    type="text"
                    value={mergeSourceHash}
                    onChange={(e) => setMergeSourceHash(e.target.value)}
                    placeholder="series_hash_de_la_serie_duplicada"
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white font-mono"
                />
                <div className="flex justify-end gap-2 pt-2">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 text-xs font-bold"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={onConfirmMerge}
                        disabled={merging || !mergeSourceHash.trim()}
                        className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold shadow-lg disabled:opacity-50"
                    >
                        {merging ? 'Fusionando...' : 'Confirmar Fusión'}
                    </button>
                </div>
            </div>
        </div>
    );
};
