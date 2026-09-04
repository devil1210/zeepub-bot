import React, { useState, useEffect } from 'react';
import {
    GitMerge,
    X,
    AlertTriangle,
    Check,
    Search,
    Loader2,
    BookOpen,
    ArrowRight
} from 'lucide-react';
import {
    workgroupsApi,
    TranslatorsGroupItem,
    WorkgroupMergeResponse
} from '@features/publisher/services/workgroupsApi';

interface FansubMergeModalProps {
    isOpen: boolean;
    onClose: () => void;
    workgroups: TranslatorsGroupItem[];
    initialTargetId?: number | null;
    initialSourceIds?: number[];
    onMergeSuccess: (res: WorkgroupMergeResponse) => void;
}

const EMPTY_SOURCES: number[] = [];

export const FansubMergeModal: React.FC<FansubMergeModalProps> = ({
    isOpen,
    onClose,
    workgroups,
    initialTargetId = null,
    initialSourceIds = EMPTY_SOURCES,
    onMergeSuccess
}) => {
    const [targetId, setTargetId] = useState<number | null>(initialTargetId);
    const [selectedSourceIds, setSelectedSourceIds] = useState<number[]>(initialSourceIds);
    const [searchTarget, setSearchTarget] = useState('');
    const [searchSource, setSearchSource] = useState('');
    const [merging, setMerging] = useState(false);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    const prevIsOpenRef = React.useRef(false);

    useEffect(() => {
        if (isOpen && !prevIsOpenRef.current) {
            setTargetId(initialTargetId ?? null);
            setSelectedSourceIds(initialSourceIds ? initialSourceIds.filter((id) => id !== initialTargetId) : []);
            setSearchTarget('');
            setSearchSource('');
            setErrorMsg(null);
        }
        prevIsOpenRef.current = isOpen;
    }, [isOpen, initialTargetId]);

    if (!isOpen) return null;

    const targetGroup = workgroups.find((w) => w.id === targetId);

    const availableSources = workgroups.filter(
        (w) => w.id !== targetId &&
        (!searchSource.trim() ||
            (w.name || '').toLowerCase().includes(searchSource.toLowerCase()) ||
            (w.siglas || '').toLowerCase().includes(searchSource.toLowerCase()) ||
            String(w.id).includes(searchSource.trim()))
    );

    const filteredTargets = workgroups.filter(
        (w) => !searchTarget.trim() ||
            (w.name || '').toLowerCase().includes(searchTarget.toLowerCase()) ||
            (w.siglas || '').toLowerCase().includes(searchTarget.toLowerCase()) ||
            String(w.id).includes(searchTarget.trim())
    );

    const toggleSource = (id: number) => {
        setSelectedSourceIds((prev) =>
            prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
        );
    };

    const selectedSources = workgroups.filter((w) => selectedSourceIds.includes(w.id));
    const totalBooksToTransfer = selectedSources.reduce(
        (sum, w) => sum + (w.books_count || 0),
        0
    );

    const handleConfirmMerge = async () => {
        if (!targetId) {
            setErrorMsg('Por favor selecciona el grupo canónico principal de destino.');
            return;
        }
        if (selectedSourceIds.length === 0) {
            setErrorMsg('Selecciona al menos un grupo duplicado para absorber.');
            return;
        }

        try {
            setMerging(true);
            setErrorMsg(null);
            const res = await workgroupsApi.merge(targetId, selectedSourceIds);
            if (res.success) {
                onMergeSuccess(res);
                onClose();
            } else {
                setErrorMsg(res.message || 'Error al fusionar grupos.');
            }
        } catch (err: any) {
            console.error('Error al fusionar fansubs:', err);
            setErrorMsg(err.message || 'Ocurrió un error inesperado al fusionar los grupos.');
        } finally {
            setMerging(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-200">
            <div className="bg-slate-900 border border-white/10 rounded-3xl max-w-2xl w-full shadow-2xl overflow-hidden my-8 flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="p-6 border-b border-white/10 flex items-center justify-between bg-slate-950/50">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center shrink-0">
                            <GitMerge className="w-5 h-5" />
                        </div>
                        <div>
                            <h3 className="text-base font-bold text-white flex items-center gap-2">
                                Fusionar Grupos de Traducción
                            </h3>
                            <p className="text-xs text-gray-400">
                                Unifica fansubs duplicados en un único registro canónico y reasigna sus libros.
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        disabled={merging}
                        className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-all"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-6 overflow-y-auto flex-1 custom-scrollbar">
                    {errorMsg && (
                        <div className="p-3.5 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-center gap-2.5">
                            <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
                            <span>{errorMsg}</span>
                        </div>
                    )}

                    {/* Step 1: Canonical Group */}
                    <div className="space-y-3">
                        <label className="text-xs font-bold text-gray-200 uppercase tracking-wider flex items-center justify-between">
                            <span>1. Grupo Canónico Principal (Destino que prevalece)</span>
                            {targetGroup && (
                                <span className="text-[11px] font-normal text-purple-400 font-mono">
                                    ID #{targetGroup.id} ({targetGroup.books_count || 0} libros actuales)
                                </span>
                            )}
                        </label>

                        <div className="relative">
                            <Search className="w-3.5 h-3.5 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                            <input
                                type="text"
                                value={searchTarget}
                                onChange={(e) => setSearchTarget(e.target.value)}
                                placeholder="Filtrar grupos por nombre o siglas..."
                                className="w-full pl-9 pr-8 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                            />
                            {searchTarget && (
                                <button
                                    type="button"
                                    onClick={() => setSearchTarget('')}
                                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white p-0.5 transition-colors"
                                >
                                    <X className="w-3.5 h-3.5" />
                                </button>
                            )}
                        </div>

                        <div className="max-h-36 overflow-y-auto space-y-1.5 pr-1 border border-white/5 rounded-2xl p-2 bg-slate-950/40">
                            {filteredTargets.length === 0 ? (
                                <div className="text-center py-4 text-xs text-gray-500">
                                    No se encontraron grupos
                                </div>
                            ) : (
                                filteredTargets.map((g) => {
                                    const isSelected = targetId === g.id;
                                    return (
                                        <button
                                            key={g.id}
                                            type="button"
                                            onClick={() => {
                                                setTargetId(g.id);
                                                setSelectedSourceIds((prev) => prev.filter((id) => id !== g.id));
                                            }}
                                            className={`w-full p-2.5 rounded-xl text-left flex items-center justify-between transition-all ${
                                                isSelected
                                                    ? 'bg-purple-600/20 border border-purple-500/50 text-white'
                                                    : 'bg-white/[0.02] hover:bg-white/5 border border-transparent text-gray-300'
                                            }`}
                                        >
                                            <div className="flex items-center gap-2.5 min-w-0">
                                                <div
                                                    className={`w-6 h-6 rounded-lg flex items-center justify-center text-[10px] font-bold ${
                                                        isSelected
                                                            ? 'bg-purple-500 text-white'
                                                            : 'bg-white/10 text-gray-400'
                                                    }`}
                                                >
                                                    {isSelected ? <Check className="w-3.5 h-3.5" /> : g.id}
                                                </div>
                                                <span className="text-xs font-bold truncate">{g.name}</span>
                                                {g.siglas && (
                                                    <span className="px-1.5 py-0.5 rounded bg-white/10 text-[10px] text-gray-400 font-mono">
                                                        {g.siglas}
                                                    </span>
                                                )}
                                            </div>
                                            <span className="text-[11px] text-gray-500 shrink-0 font-mono">
                                                {g.books_count || 0} libros
                                            </span>
                                        </button>
                                    );
                                })
                            )}
                        </div>
                    </div>

                    {/* Step 2: Duplicates to Merge */}
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <label className="text-xs font-bold text-gray-200 uppercase tracking-wider">
                                2. Grupos Duplicados a Absorber (Serán eliminados)
                            </label>
                            <span className="text-[11px] text-purple-400 font-mono font-bold">
                                {selectedSourceIds.length} seleccionados
                            </span>
                        </div>

                        <div className="relative">
                            <Search className="w-3.5 h-3.5 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                            <input
                                type="text"
                                value={searchSource}
                                onChange={(e) => setSearchSource(e.target.value)}
                                placeholder="Buscar duplicados a absorber..."
                                className="w-full pl-9 pr-8 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                            />
                            {searchSource && (
                                <button
                                    type="button"
                                    onClick={() => setSearchSource('')}
                                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white p-0.5 transition-colors"
                                >
                                    <X className="w-3.5 h-3.5" />
                                </button>
                            )}
                        </div>

                        <div className="max-h-44 overflow-y-auto space-y-1.5 pr-1 border border-white/5 rounded-2xl p-2 bg-slate-950/40">
                            {availableSources.length === 0 ? (
                                <div className="text-center py-4 text-xs text-gray-500">
                                    No hay otros grupos disponibles para absorber
                                </div>
                            ) : (
                                availableSources.map((g) => {
                                    const isChecked = selectedSourceIds.includes(g.id);
                                    return (
                                        <button
                                            key={g.id}
                                            type="button"
                                            onClick={() => toggleSource(g.id)}
                                            className={`w-full p-2.5 rounded-xl text-left flex items-center justify-between transition-all ${
                                                isChecked
                                                    ? 'bg-amber-500/15 border border-amber-500/40 text-amber-200'
                                                    : 'bg-white/[0.02] hover:bg-white/5 border border-transparent text-gray-300'
                                            }`}
                                        >
                                            <div className="flex items-center gap-2.5 min-w-0">
                                                <div
                                                    className={`w-4 h-4 rounded border flex items-center justify-center ${
                                                        isChecked
                                                            ? 'bg-amber-500 border-amber-500 text-black'
                                                            : 'border-white/20 bg-slate-900'
                                                    }`}
                                                >
                                                    {isChecked && <Check className="w-3 h-3 stroke-[3]" />}
                                                </div>
                                                <span className="text-xs font-bold truncate">{g.name}</span>
                                                {g.siglas && (
                                                    <span className="px-1.5 py-0.5 rounded bg-white/10 text-[10px] text-gray-400 font-mono">
                                                        {g.siglas}
                                                    </span>
                                                )}
                                                <span className="text-[10px] text-gray-500 font-mono">
                                                    ID #{g.id}
                                                </span>
                                            </div>
                                            <span className="text-[11px] font-mono text-amber-300/80 font-bold shrink-0">
                                                +{g.books_count || 0} libros
                                            </span>
                                        </button>
                                    );
                                })
                            )}
                        </div>
                    </div>

                    {/* Impact Summary Banner */}
                    {targetGroup && selectedSources.length > 0 && (
                        <div className="p-4 rounded-2xl bg-purple-950/30 border border-purple-500/30 space-y-2">
                            <div className="flex items-center gap-2 text-xs font-bold text-purple-300">
                                <GitMerge className="w-4 h-4 text-purple-400" />
                                <span>Resumen de la Operación</span>
                            </div>
                            <div className="text-xs text-gray-300 space-y-1 pl-6">
                                <p className="flex items-center gap-2">
                                    <span>Se absorberán {selectedSources.length} grupo(s):</span>
                                    <span className="text-amber-300 font-mono font-bold">
                                        {selectedSources.map((s) => `#${s.id} ${s.name}`).join(', ')}
                                    </span>
                                </p>
                                <p className="flex items-center gap-2">
                                    <ArrowRight className="w-3.5 h-3.5 text-purple-400" />
                                    <span>Destino canónico:</span>
                                    <strong className="text-white font-bold">{targetGroup.name}</strong>
                                    <span className="text-purple-400 font-mono">(ID #{targetGroup.id})</span>
                                </p>
                                <p className="flex items-center gap-2">
                                    <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                                    <span>Total libros a transferir:</span>
                                    <span className="text-emerald-400 font-mono font-bold">
                                        +{totalBooksToTransfer} libros
                                    </span>
                                    <span className="text-gray-400">
                                        (Total resultante:{' '}
                                        <strong className="text-white">
                                            {(targetGroup.books_count || 0) + totalBooksToTransfer}
                                        </strong>
                                        )
                                    </span>
                                </p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-white/10 bg-slate-950/60 flex items-center justify-between gap-3">
                    <button
                        type="button"
                        onClick={onClose}
                        disabled={merging}
                        className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 text-xs font-bold transition-all"
                    >
                        Cancelar
                    </button>

                    <button
                        type="button"
                        onClick={handleConfirmMerge}
                        disabled={merging || !targetId || selectedSourceIds.length === 0}
                        className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 disabled:pointer-events-none text-white text-xs font-bold flex items-center gap-2 shadow-xl shadow-purple-600/30 transition-all active:scale-95"
                    >
                        {merging ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span>Fusionando grupos...</span>
                            </>
                        ) : (
                            <>
                                <GitMerge className="w-4 h-4" />
                                <span>Confirmar Fusión Definitiva</span>
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};
