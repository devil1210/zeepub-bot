import React, { useState } from 'react';
import {
    Sparkles,
    Edit2,
    Save,
    Check,
    X
} from 'lucide-react';

interface DiffHighlighterProps {
    oldText: string;
    newText: string;
}

const DiffHighlighter: React.FC<DiffHighlighterProps> = ({ oldText, newText }) => {
    if (!oldText || !newText) return <>{newText}</>;

    const oldWords = oldText.split(' ');
    const newWords = newText.split(' ');

    return (
        <span className="leading-relaxed">
            {newWords.map((word, i) => {
                const isMatch = oldWords.includes(word);
                return (
                    <span
                        key={i}
                        className={isMatch ? "" : "bg-green-500/20 text-green-300 px-0.5 rounded border-b border-green-500/30 font-bold"}
                    >
                        {word}{' '}
                    </span>
                );
            })}
        </span>
    );
};

interface ProposalModalProps {
    isOpen: boolean;
    proposal: any;
    approvedChanges?: any[];
    applyRenames?: boolean;
    applyMeta?: boolean;
    editedSeries?: string;
    editedSpanish?: string;
    isEditingSeries?: boolean;
    editingBookId?: number | null;
    processingProposal?: boolean;
    onClose: () => void;
    onApply: () => void;
    setApplyRenames?: (val: boolean) => void;
    setApplyMeta?: (val: boolean) => void;
    setEditedSeries?: (val: string) => void;
    setEditedSpanish?: (val: string) => void;
    setIsEditingSeries?: (val: boolean) => void;
    toggleChange?: (bookId: number) => void;
    handleEditFilename?: (bookId: number, name: string) => void;
    setEditingBookId?: (id: number | null) => void;
}

export const ProposalModal: React.FC<ProposalModalProps> = ({
    isOpen,
    proposal,
    approvedChanges,
    applyRenames,
    applyMeta,
    editedSeries,
    editedSpanish,
    isEditingSeries,
    editingBookId,
    processingProposal = false,
    onClose,
    onApply,
    setApplyRenames,
    setApplyMeta,
    setEditedSeries,
    setEditedSpanish,
    setIsEditingSeries,
    toggleChange,
    handleEditFilename,
    setEditingBookId
}) => {
    const [localApproved, setLocalApproved] = useState<any[]>(() => proposal?.changes || []);
    const [localRenames, setLocalRenames] = useState(true);
    const [localMeta, setLocalMeta] = useState(true);
    const [localSeries, setLocalSeries] = useState(proposal?.proposed_series || '');
    const [localSpanish, setLocalSpanish] = useState(proposal?.proposed_spanish || '');
    const [localIsEditing, setLocalIsEditing] = useState(false);
    const [localEditingId, setLocalEditingId] = useState<number | null>(null);

    const actualApprovedChanges = approvedChanges !== undefined ? approvedChanges : localApproved;
    const actualApplyRenames = applyRenames !== undefined ? applyRenames : localRenames;
    const actualApplyMeta = applyMeta !== undefined ? applyMeta : localMeta;
    const actualEditedSeries = editedSeries !== undefined ? editedSeries : localSeries;
    const actualEditedSpanish = editedSpanish !== undefined ? editedSpanish : localSpanish;
    const actualIsEditingSeries = isEditingSeries !== undefined ? isEditingSeries : localIsEditing;
    const actualEditingBookId = editingBookId !== undefined ? editingBookId : localEditingId;

    const doSetApplyRenames = setApplyRenames || setLocalRenames;
    const doSetApplyMeta = setApplyMeta || setLocalMeta;
    const doSetEditedSeries = setEditedSeries || setLocalSeries;
    const doSetEditedSpanish = setEditedSpanish || setLocalSpanish;
    const doSetIsEditingSeries = setIsEditingSeries || setLocalIsEditing;
    const doSetEditingBookId = setEditingBookId || setLocalEditingId;
    const doToggleChange = toggleChange || ((id: number) => {
        setLocalApproved(prev => {
            const exists = prev.some(c => c.book_id === id);
            if (exists) return prev.filter(c => c.book_id !== id);
            const found = proposal?.changes?.find((c: any) => c.book_id === id);
            return found ? [...prev, found] : prev;
        });
    });
    const doHandleEditFilename = handleEditFilename || ((id: number, name: string) => {
        if (proposal?.changes) {
            const ch = proposal.changes.find((c: any) => c.book_id === id);
            if (ch) ch.proposed_filename = name;
        }
    });

    if (!isOpen || !proposal) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
            <div className="w-full max-w-4xl max-h-[90vh] bg-[#0c0e12] border border-white/10 rounded-[2.5rem] shadow-2xl flex flex-col overflow-hidden relative">

                {/* Header */}
                <div className="p-6 border-b border-white/10 flex items-center justify-between bg-white/5">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-2xl bg-primary/20 text-primary border border-primary/30">
                            <Sparkles className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="text-xl font-black text-white tracking-tight">Propuesta de Refinamiento IA</h3>
                            <p className="text-xs text-gray-400 font-medium mt-0.5">
                                Confirma o ajusta los cambios sugeridos antes de aplicar a la biblioteca.
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-3 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-500 hover:text-white rounded-xl hover:bg-white/5 transition-all"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Scrollable Body */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">

                    {/* Series Title Review */}
                    <div className="glass-panel p-5 rounded-premium-sm border border-white/10 bg-white/5 relative group">
                        <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">
                                        Nombre de la Serie (Español / Principal)
                                    </span>
                                    {!actualIsEditingSeries && (
                                        <button
                                            onClick={() => doSetIsEditingSeries(true)}
                                            className="text-xs font-bold text-gray-400 hover:text-white flex items-center gap-1.5 transition-colors"
                                        >
                                            <Edit2 className="w-3.5 h-3.5" />
                                            Editar Título
                                        </button>
                                    )}
                                </div>

                                {actualIsEditingSeries ? (
                                    <div className="space-y-3 pt-2">
                                        <div>
                                            <label className="text-[10px] uppercase font-bold text-gray-400">Título Serie (Principal)</label>
                                            <input
                                                type="text"
                                                value={actualEditedSeries}
                                                onChange={(e) => doSetEditedSeries(e.target.value)}
                                                className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-primary outline-none"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] uppercase font-bold text-gray-400">Título Español</label>
                                            <input
                                                type="text"
                                                value={actualEditedSpanish}
                                                onChange={(e) => doSetEditedSpanish(e.target.value)}
                                                className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-primary outline-none"
                                            />
                                        </div>
                                        <button
                                            onClick={() => doSetIsEditingSeries(false)}
                                            className="px-4 py-1.5 bg-primary text-white text-xs font-bold rounded-lg flex items-center gap-1.5"
                                        >
                                            <Check className="w-3.5 h-3.5" /> Listo
                                        </button>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        <div>
                                            <p className="text-lg font-bold text-green-100 break-words leading-relaxed whitespace-pre-wrap">
                                                <DiffHighlighter
                                                    oldText={proposal.current_series}
                                                    newText={actualEditedSeries}
                                                />
                                            </p>
                                            {actualEditedSpanish !== actualEditedSeries && (
                                                <p className="text-sm text-gray-400 mt-2 flex items-center gap-2">
                                                    <span className="text-[10px] font-black bg-white/5 px-1.5 rounded text-gray-500">ES</span>
                                                    {actualEditedSpanish}
                                                </p>
                                            )}
                                        </div>
                                        {proposal.reason && (
                                            <div className="bg-white/5 p-3 rounded-premium-sm border border-white/5">
                                                <p className="text-xs text-gray-400 leading-relaxed italic">
                                                    "{proposal.reason}"
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Tags Detected */}
                    {proposal.global_tags?.length > 0 && (
                        <div>
                            <h4 className="text-sm font-bold text-gray-300 uppercase tracking-wide mb-3">Tags Detectados</h4>
                            <div className="flex flex-wrap gap-2">
                                {proposal.global_tags?.map((tag: string) => (
                                    <span key={tag} className="px-3 py-1 rounded-lg bg-blue-500/20 border border-blue-500/30 text-blue-300 text-xs font-bold">
                                        {tag}
                                    </span>
                                ))}
                                {proposal.is_uncensored_series && (
                                    <span className="px-3 py-1 rounded-lg bg-red-500/20 border border-red-500/30 text-red-300 text-xs font-bold">
                                        Uncensored
                                    </span>
                                )}
                            </div>
                        </div>
                    )}

                    {/* File Renames */}
                    <div>
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="text-sm font-bold text-gray-300 uppercase tracking-wide">
                                Archivos a Renombrar ({actualApprovedChanges.length}/{proposal.changes?.length || 0})
                            </h4>
                            <label className="flex items-center gap-2 text-xs font-bold text-primary cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={actualApplyRenames}
                                    onChange={(e) => doSetApplyRenames(e.target.checked)}
                                    className="rounded border-white/20 bg-white/5"
                                />
                                Habilitar Renombrado
                            </label>
                        </div>

                        <div className="space-y-2">
                            {proposal.changes?.map((change: any) => {
                                const isSelected = actualApprovedChanges.some((c: any) => (c.book_id || c) === change.book_id);
                                return (
                                    <div
                                        key={change.book_id}
                                        className={`p-3 rounded-premium-sm border flex items-center gap-4 text-sm transition-all group ${isSelected && actualApplyRenames
                                            ? 'bg-white/5 border-white/10 opacity-100'
                                            : 'bg-black/20 border-white/5 opacity-40 grayscale'
                                            }`}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={isSelected}
                                            onChange={() => doToggleChange(change.book_id)}
                                            disabled={!actualApplyRenames}
                                            className="w-5 h-5 rounded-lg border-white/20 bg-white/5 cursor-pointer accent-primary"
                                        />
                                        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                                            <div className="text-red-300/50 break-words line-through decoration-red-500/30 text-[11px] leading-tight">
                                                {change.current_filename}
                                            </div>
                                            <div className="flex items-center gap-2 group/field">
                                                {actualEditingBookId === change.book_id ? (
                                                    <div className="flex-1 flex items-center gap-2 animate-in slide-in-from-right-2 duration-200">
                                                        <input
                                                            type="text"
                                                            autoFocus
                                                            value={change.proposed_filename}
                                                            onChange={(e) => doHandleEditFilename(change.book_id, e.target.value)}
                                                            onKeyDown={(e) => e.key === 'Enter' && doSetEditingBookId(null)}
                                                            onBlur={() => doSetEditingBookId(null)}
                                                            className="flex-1 bg-black/60 border border-primary/50 rounded px-2 py-1 text-xs text-white outline-none focus:ring-1 ring-primary"
                                                        />
                                                        <button
                                                            onClick={() => doSetEditingBookId(null)}
                                                            className="p-3 min-w-[44px] min-h-[44px] flex items-center justify-center text-green-400 hover:text-green-300 transition-colors"
                                                        >
                                                            <Check className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                ) : (
                                                    <>
                                                        <div className="flex-1 text-green-300 font-medium break-words leading-tight text-[13px]">
                                                            <DiffHighlighter
                                                                oldText={change.current_filename}
                                                                newText={change.proposed_filename}
                                                            />
                                                        </div>
                                                        <button
                                                            onClick={() => doSetEditingBookId(change.book_id)}
                                                            className="p-3 min-w-[44px] min-h-[44px] flex items-center justify-center rounded bg-white/5 hover:bg-white/10 text-gray-500 hover:text-white transition-all opacity-0 group-hover:opacity-100"
                                                            title="Editar nombre"
                                                        >
                                                            <Edit2 className="w-3.5 h-3.5" />
                                                        </button>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                </div>

                {/* Footer */}
                <div className="p-6 border-t border-white/10 bg-white/5 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="min-h-[44px] flex items-center justify-center px-6 py-3 rounded-premium-sm font-bold text-gray-400 hover:bg-white/5 transition-all"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={onApply}
                        disabled={processingProposal}
                        className="min-h-[44px] flex items-center justify-center px-8 py-3 rounded-premium-sm font-bold bg-primary hover:bg-primary/90 text-white gap-2 transition-all shadow-lg shadow-primary/20"
                    >
                        {processingProposal ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                Aplicando...
                            </>
                        ) : (
                            <>
                                <Save className="w-4 h-4" />
                                Aplicar Cambios
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};
