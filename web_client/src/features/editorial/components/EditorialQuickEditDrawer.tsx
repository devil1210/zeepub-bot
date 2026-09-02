import React, { useState, useEffect } from 'react';
import { X, Save, Sparkles, BookOpen, Layers, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '@shared/services/api';

interface QuickEditDrawerProps {
    isOpen: boolean;
    itemType: 'epub' | 'series' | 'volume';
    itemData: any;
    onClose: () => void;
    onSaveSuccess: () => void;
}

export const EditorialQuickEditDrawer: React.FC<QuickEditDrawerProps> = ({
    isOpen,
    itemType,
    itemData,
    onClose,
    onSaveSuccess,
}) => {
    const [formData, setFormData] = useState<any>({});
    const [saving, setSaving] = useState(false);
    const [aiSuggesting, setAiSuggesting] = useState(false);
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    useEffect(() => {
        if (itemData) {
            setFormData({
                title: itemData.title || itemData.name || '',
                spanish_title: itemData.spanish_title || itemData.name_spanish || '',
                english_title: itemData.english_title || itemData.name_english || '',
                volume: itemData.volume || itemData.volume_number || '',
                author: itemData.author || '',
                illustrator: itemData.illustrator || '',
                demography: itemData.demography || '',
                synopsis: itemData.synopsis || itemData.description || '',
                series_id: itemData.series_id || itemData.series_hash || '',
                status: itemData.status || 'ready',
            });
            setStatusMsg(null);
        }
    }, [itemData]);

    if (!isOpen || !itemData) return null;

    const handleFieldChange = (field: string, value: any) => {
        setFormData((prev: any) => ({ ...prev, [field]: value }));
    };

    const handleAiAutoFill = async () => {
        setAiSuggesting(true);
        setStatusMsg(null);
        try {
            const rawTitle = formData.title || itemData.filename || '';
            const res = await api.rpc('ai_suggest_metadata', { title: rawTitle });
            if (res && res.metadata) {
                setFormData((prev: any) => ({
                    ...prev,
                    english_title: res.metadata.english_title || prev.english_title,
                    spanish_title: res.metadata.spanish_title || prev.spanish_title,
                    author: res.metadata.author || prev.author,
                    volume: res.metadata.volume || prev.volume,
                    demography: res.metadata.demography || prev.demography,
                }));
                setStatusMsg({ type: 'success', text: 'Metadatos sugeridos por IA completados' });
            }
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: 'No se pudieron generar sugerencias de IA' });
        } finally {
            setAiSuggesting(false);
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setStatusMsg(null);
        try {
            if (itemType === 'series') {
                const sId = itemData.series_hash || itemData.id;
                await api.updateSeriesGrid(sId, {
                    name: formData.title,
                    name_spanish: formData.spanish_title,
                    name_english: formData.english_title,
                    author: formData.author,
                    illustrator: formData.illustrator,
                    demography: formData.demography,
                    synopsis: formData.synopsis,
                });
            } else {
                const bId = itemData.book_hash || itemData.id;
                await api.updateBookGrid(bId, {
                    title: formData.title,
                    spanish_title: formData.spanish_title,
                    volume: formData.volume,
                    author: formData.author,
                    illustrator: formData.illustrator,
                    demography: formData.demography,
                    synopsis: formData.synopsis,
                });
            }

            setStatusMsg({ type: 'success', text: 'Cambios guardados con éxito' });
            setTimeout(() => {
                onSaveSuccess();
                onClose();
            }, 800);
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error al guardar cambios' });
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="absolute inset-y-0 right-0 max-w-full flex pl-10">
                <div className="w-screen max-w-md bg-slate-900 border-l border-white/10 shadow-2xl flex flex-col h-full">
                    {/* Header */}
                    <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-slate-950/60">
                        <div className="flex items-center gap-2">
                            {itemType === 'series' ? (
                                <Layers className="w-5 h-5 text-indigo-400" />
                            ) : (
                                <BookOpen className="w-5 h-5 text-emerald-400" />
                            )}
                            <div>
                                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                                    Edición Rápida: {itemType === 'series' ? 'Serie' : 'Volumen / EPUB'}
                                </h3>
                                <p className="text-[11px] text-gray-400 font-mono truncate max-w-[240px]">
                                    {itemData.id || itemData.book_hash}
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Status Alert */}
                    {statusMsg && (
                        <div
                            className={`mx-6 mt-4 p-3 rounded-xl flex items-center gap-2 text-xs font-medium ${
                                statusMsg.type === 'success'
                                    ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                                    : 'bg-red-500/10 text-red-300 border border-red-500/20'
                            }`}
                        >
                            {statusMsg.type === 'success' ? (
                                <CheckCircle2 className="w-4 h-4 shrink-0" />
                            ) : (
                                <AlertCircle className="w-4 h-4 shrink-0" />
                            )}
                            <span>{statusMsg.text}</span>
                        </div>
                    )}

                    {/* Body Form */}
                    <form onSubmit={handleSave} className="flex-1 overflow-y-auto p-6 space-y-4">
                        {/* Quick AI Tool */}
                        <div className="flex justify-between items-center bg-indigo-500/10 border border-indigo-500/20 p-3 rounded-xl">
                            <span className="text-xs font-semibold text-indigo-300">Asistente Editorial IA</span>
                            <button
                                type="button"
                                onClick={handleAiAutoFill}
                                disabled={aiSuggesting}
                                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 transition-all active:scale-95 disabled:opacity-50"
                            >
                                {aiSuggesting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                                Auto-completar
                            </button>
                        </div>

                        <div>
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Título Canónico (Inglés/Oficial)</label>
                            <input
                                type="text"
                                value={formData.title}
                                onChange={(e) => handleFieldChange('title', e.target.value)}
                                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white focus:border-indigo-500 focus:outline-none"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Título en Español</label>
                            <input
                                type="text"
                                value={formData.spanish_title}
                                onChange={(e) => handleFieldChange('spanish_title', e.target.value)}
                                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white focus:border-indigo-500 focus:outline-none"
                            />
                        </div>

                        {itemType !== 'series' && (
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Volumen</label>
                                    <input
                                        type="text"
                                        value={formData.volume}
                                        onChange={(e) => handleFieldChange('volume', e.target.value)}
                                        className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white focus:border-indigo-500 focus:outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Demografía</label>
                                    <input
                                        type="text"
                                        value={formData.demography}
                                        onChange={(e) => handleFieldChange('demography', e.target.value)}
                                        placeholder="Seinen, Shonen, etc."
                                        className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white focus:border-indigo-500 focus:outline-none"
                                    />
                                </div>
                            </div>
                        )}

                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Autor</label>
                                <input
                                    type="text"
                                    value={formData.author}
                                    onChange={(e) => handleFieldChange('author', e.target.value)}
                                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white focus:border-indigo-500 focus:outline-none"
                                />
                            </div>
                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Ilustrador</label>
                                <input
                                    type="text"
                                    value={formData.illustrator}
                                    onChange={(e) => handleFieldChange('illustrator', e.target.value)}
                                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white focus:border-indigo-500 focus:outline-none"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Sinopsis / Reseña Editorial</label>
                            <textarea
                                value={formData.synopsis}
                                onChange={(e) => handleFieldChange('synopsis', e.target.value)}
                                rows={5}
                                className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white focus:border-indigo-500 focus:outline-none resize-none"
                            />
                        </div>
                    </form>

                    {/* Footer */}
                    <div className="p-4 border-t border-white/10 bg-slate-950/60 flex items-center justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-xs font-bold text-gray-400 hover:text-white transition-colors"
                        >
                            Cancelar
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={saving}
                            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/30 active:scale-95 transition-all disabled:opacity-50"
                        >
                            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            Guardar Cambios
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
