import React, { useState, useEffect } from 'react';
import {
    X,
    Save,
    Sparkles,
    BookOpen,
    Layers,
    CheckCircle2,
    AlertTriangle,
    Loader2,
    Copy,
    Check,
    RefreshCw,
    ExternalLink,
    Building2,
    FileSpreadsheet,
    Eye,
    Palette,
    ShieldAlert
} from 'lucide-react';
import { api } from '@shared/services/api';

interface EpubEditModalProps {
    isOpen: boolean;
    book?: any;
    bookData?: any;
    seriesData?: any;
    onClose: () => void;
    onSaveSuccess: () => void;
}

export const EpubEditModal: React.FC<EpubEditModalProps> = ({
    isOpen,
    book,
    bookData,
    seriesData,
    onClose,
    onSaveSuccess,
}) => {
    const currentBook = book || bookData;
    const [formData, setFormData] = useState<any>({});
    const [saving, setSaving] = useState(false);
    const [aiSuggesting, setAiSuggesting] = useState(false);
    const [isSyncing, setIsSyncing] = useState(false);
    const [copiedPath, setCopiedPath] = useState(false);
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    useEffect(() => {
        if (currentBook) {
            const seriesInfo = currentBook.series_info || seriesData || currentBook.series;
            const isSpanish = (str: string) => /[áéíóúñÁÉÍÓÚÑ]|\b(el|la|los|las|de|del|en|y|un|una|más|mundo|ordinario)\b/i.test(str);

            let initialEnglish = (
                currentBook.name_english ||
                seriesInfo?.series_english ||
                seriesInfo?.name_english ||
                (!isSpanish(currentBook.title || '') ? currentBook.title : '') ||
                ''
            );

            let initialSpanish = (
                currentBook.spanish_title ||
                currentBook.name_spanish ||
                seriesInfo?.series_spanish ||
                seriesInfo?.name_spanish ||
                (isSpanish(currentBook.title || '') ? currentBook.title : '') ||
                ''
            );

            if (initialSpanish && initialSpanish.includes('. ') && !initialSpanish.includes(': ')) {
                const parts = initialSpanish.split('. ');
                if (parts.length === 2 && parts[0].trim().length > 2) {
                    initialSpanish = `${parts[0].trim()}: ${parts[1].trim()}`;
                }
            }

            setFormData({
                title: currentBook.title || initialEnglish || '',
                spanish_title: initialSpanish,
                english_title: initialEnglish,
                volume: currentBook.volume !== undefined && currentBook.volume !== null ? currentBook.volume : '',
                edition: currentBook.edition || '',
                color_mode: currentBook.color_mode || 'bw',
                is_uncensored: Boolean(currentBook.is_uncensored),
                author: currentBook.author || seriesInfo?.author || '',
                illustrator: currentBook.illustrator || seriesInfo?.illustrator || '',
                demography: currentBook.demography || seriesInfo?.demography || '',
                translator: currentBook.translator || '',
                layout_by: currentBook.layout_by || currentBook.layoutBy || '',
                publisher: currentBook.publisher || currentBook.workgroup || currentBook.editorial || seriesInfo?.publisher || '',
                cover_url: currentBook.cover_url || currentBook.cover_image || '',
                description: currentBook.description || currentBook.synopsis || '',
                series_id: currentBook.series_id || seriesInfo?.id || '',
                filepath: currentBook.filepath || '',
                filename: currentBook.filename || '',
            });
            setStatusMsg(null);
        }
    }, [currentBook, seriesData]);

    if (!isOpen || !currentBook) return null;

    const handleCopyPath = () => {
        const path = formData.filepath || currentBook.filepath || currentBook.filename;
        if (!path) return;
        navigator.clipboard.writeText(path);
        setCopiedPath(true);
        setTimeout(() => setCopiedPath(false), 2000);
    };

    const handleAiAutoFill = async () => {
        setAiSuggesting(true);
        setStatusMsg(null);
        try {
            const rawTitle = formData.title || bookData.filename || '';
            const res = await api.rpc('ai_suggest_metadata', { title: rawTitle });
            if (res && res.metadata) {
                setFormData((prev: any) => ({
                    ...prev,
                    english_title: res.metadata.english_title || prev.english_title,
                    spanish_title: res.metadata.spanish_title || prev.spanish_title,
                    author: res.metadata.author || prev.author,
                    volume: res.metadata.volume !== undefined ? res.metadata.volume : prev.volume,
                    demography: res.metadata.demography || prev.demography,
                }));
                setStatusMsg({ type: 'success', text: 'Metadatos sugeridos por IA completados.' });
            }
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: 'No se pudieron generar sugerencias de IA' });
        } finally {
            setAiSuggesting(false);
        }
    };

    const handleSyncPhysicalEpub = async () => {
        const bId = bookData.id || bookData.book_hash;
        if (!bId || isSyncing) return;
        setIsSyncing(true);
        setStatusMsg(null);
        try {
            const res = await api.rpc('admin_sync_books', { book_ids: [bId] });
            if (res && res.success) {
                setStatusMsg({
                    type: 'success',
                    text: `✅ ${res.message || 'Metadatos sincronizados con éxito desde el archivo en disco.'}`
                });
                if (res.synced_items && res.synced_items[0]) {
                    const item = res.synced_items[0];
                    setFormData((prev: any) => ({
                        ...prev,
                        publisher: item.publisher || prev.publisher,
                        volume: item.volume !== undefined ? item.volume : prev.volume,
                    }));
                }
                if (onSaveSuccess) onSaveSuccess();
            } else {
                setStatusMsg({ type: 'error', text: res?.message || 'Error al sincronizar desde el archivo' });
            }
        } catch (err: any) {
            console.error('Error sincronizando archivo:', err);
            setStatusMsg({ type: 'error', text: err.message || 'Error al sincronizar con el archivo EPUB' });
        } finally {
            setIsSyncing(false);
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setStatusMsg(null);
        try {
            const bId = bookData.book_hash || bookData.id;
            await api.updateBookGrid(bId, {
                title: formData.english_title || formData.title,
                english_title: formData.english_title,
                spanish_title: formData.spanish_title,
                volume: formData.volume !== '' ? formData.volume : null,
                edition: formData.edition,
                color_mode: formData.color_mode,
                is_uncensored: formData.is_uncensored,
                author: formData.author,
                illustrator: formData.illustrator,
                demography: formData.demography,
                translator: formData.translator,
                layout_by: formData.layout_by,
                publisher: formData.publisher,
                cover_url: formData.cover_url,
                description: formData.description,
                synopsis: formData.description,
            });

            setStatusMsg({ type: 'success', text: 'Metadatos del volumen actualizados correctamente.' });
            if (onSaveSuccess) onSaveSuccess();
            setTimeout(() => {
                onClose();
            }, 1200);
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error al guardar los cambios' });
        } finally {
            setSaving(false);
        }
    };

    // Calculate metadata issues for typesetter guide
    const issues: string[] = [];
    if (!formData.volume && formData.volume !== 0) issues.push('Falta número de volumen');
    if (!formData.spanish_title) issues.push('Sin título en español');
    if (!formData.author) issues.push('Sin autor registrado');
    if (!formData.translator) issues.push('Sin traductor asignado');
    if (!formData.publisher) issues.push('Sin publisher en OPF/BD');

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-6 animate-in fade-in duration-200">
            <div className="w-full max-w-5xl bg-slate-900 border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
                {/* Modal Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-slate-950/70">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">
                            <BookOpen className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-base font-bold text-white flex items-center gap-2">
                                <span>Editor Editorial de Tomo / EPUB</span>
                                {formData.volume !== '' && (
                                    <span className="px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-mono text-xs font-bold border border-indigo-500/30">
                                        Vol. {formData.volume}
                                    </span>
                                )}
                            </h2>
                            <p className="text-xs text-gray-400 truncate max-w-xl">
                                {formData.spanish_title || formData.title || bookData.filename}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            type="button"
                            onClick={handleAiAutoFill}
                            disabled={aiSuggesting}
                            className="px-3 py-1.5 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 text-xs font-bold flex items-center gap-1.5 transition-all shadow-md active:scale-95 disabled:opacity-50"
                            title="Sugerir títulos y volumen con Inteligencia Artificial"
                        >
                            {aiSuggesting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                            <span>Autocompletar con IA</span>
                        </button>

                        <button
                            type="button"
                            onClick={onClose}
                            className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Status Message Alert */}
                {statusMsg && (
                    <div
                        className={`mx-6 mt-4 p-3 rounded-2xl flex items-center gap-2.5 text-xs font-bold ${
                            statusMsg.type === 'success'
                                ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                                : 'bg-red-500/10 text-red-300 border border-red-500/20'
                        }`}
                    >
                        {statusMsg.type === 'success' ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        ) : (
                            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                        )}
                        <span>{statusMsg.text}</span>
                    </div>
                )}

                {/* Modal Body: 2 Columns layout matching SeriesEditTab */}
                <div className="p-6 overflow-y-auto flex-1">
                    <form onSubmit={handleSave} className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                        {/* LEFT COLUMN: Main Book Metadata (7 cols) */}
                        <div className="lg:col-span-7 space-y-4">
                            <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
                                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                                    <FileSpreadsheet className="w-4 h-4 text-indigo-400" /> Metadatos Principales del Volumen
                                </h3>
                                <span className="text-[10px] text-gray-400 font-mono">ID: {bookData.id}</span>
                            </div>

                            {/* Título en Español */}
                            <div>
                                <label className="block text-[11px] font-bold text-amber-300 uppercase mb-1">
                                    Título en Español (Canónico)
                                </label>
                                <input
                                    type="text"
                                    value={formData.spanish_title || ''}
                                    onChange={(e) => setFormData({ ...formData, spanish_title: e.target.value })}
                                    placeholder="Ej: Alya a veces susurra en ruso"
                                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-amber-400 font-bold"
                                />
                            </div>

                            {/* Título en Inglés / Internacional */}
                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                    Título en Inglés / Oficial Internacional
                                </label>
                                <input
                                    type="text"
                                    value={formData.english_title || ''}
                                    onChange={(e) => setFormData({ ...formData, english_title: e.target.value })}
                                    placeholder="Ej: Alya Sometimes Hides Her Feelings in Russian"
                                    className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-medium"
                                />
                            </div>

                            {/* Título de Archivo / Original */}
                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                    Título Original / Nombre de Obra
                                </label>
                                <input
                                    type="text"
                                    value={formData.title || ''}
                                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            {/* Volume, Edition, Color Mode, Censorship */}
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                        Número de Tomo
                                    </label>
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={formData.volume !== undefined ? formData.volume : ''}
                                        onChange={(e) => setFormData({ ...formData, volume: e.target.value })}
                                        placeholder="Ej: 1, 2, 4.5"
                                        className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-mono font-bold"
                                    />
                                </div>

                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                        Edición / Versión
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.edition || ''}
                                        onChange={(e) => setFormData({ ...formData, edition: e.target.value })}
                                        placeholder="Estándar, BD..."
                                        className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                        Modo Color
                                    </label>
                                    <select
                                        value={formData.color_mode || 'bw'}
                                        onChange={(e) => setFormData({ ...formData, color_mode: e.target.value })}
                                        className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-bold"
                                    >
                                        <option value="bw">Blanco y Negro</option>
                                        <option value="color">Full Color [Color]</option>
                                    </select>
                                </div>
                            </div>

                            {/* Censorship Checkbox */}
                            <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-950/60 border border-white/5">
                                <input
                                    type="checkbox"
                                    id="is_uncensored"
                                    checked={Boolean(formData.is_uncensored)}
                                    onChange={(e) => setFormData({ ...formData, is_uncensored: e.target.checked })}
                                    className="w-4 h-4 rounded text-red-600 focus:ring-red-500 bg-slate-900 border-white/20"
                                />
                                <label htmlFor="is_uncensored" className="text-xs text-gray-300 font-medium cursor-pointer flex items-center gap-1.5">
                                    <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
                                    <span>Versión Sin Censura (S/C)</span>
                                </label>
                            </div>

                            {/* Author & Illustrator */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Autor</label>
                                    <input
                                        type="text"
                                        value={formData.author || ''}
                                        onChange={(e) => setFormData({ ...formData, author: e.target.value })}
                                        className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Ilustrador</label>
                                    <input
                                        type="text"
                                        value={formData.illustrator || ''}
                                        onChange={(e) => setFormData({ ...formData, illustrator: e.target.value })}
                                        className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    />
                                </div>
                            </div>

                            {/* Translator & Layout By */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Traductor / Fansub</label>
                                    <input
                                        type="text"
                                        value={formData.translator || ''}
                                        onChange={(e) => setFormData({ ...formData, translator: e.target.value })}
                                        className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Maquetador</label>
                                    <input
                                        type="text"
                                        value={formData.layout_by || ''}
                                        onChange={(e) => setFormData({ ...formData, layout_by: e.target.value })}
                                        className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    />
                                </div>
                            </div>

                            {/* Publisher / Grupo */}
                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                    Editorial / Publisher (dc:publisher)
                                </label>
                                <input
                                    type="text"
                                    value={formData.publisher || ''}
                                    onChange={(e) => setFormData({ ...formData, publisher: e.target.value })}
                                    className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                                />
                            </div>

                            {/* Sinopsis del Volumen */}
                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                    Sinopsis del Tomo
                                </label>
                                <textarea
                                    value={formData.description || ''}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    rows={4}
                                    className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white leading-relaxed focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            {/* Guardar Metadatos Button */}
                            <button
                                type="submit"
                                disabled={saving}
                                className="w-full py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 shadow-xl shadow-indigo-600/30 transition-all active:scale-95 disabled:opacity-50"
                            >
                                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                <span>Guardar Metadatos del Tomo</span>
                            </button>
                        </div>

                        {/* RIGHT COLUMN: Cover, Physical File & Audit (5 cols) */}
                        <div className="lg:col-span-5 space-y-5">
                            {/* Cover Preview Card */}
                            <div className="bg-slate-950/60 border border-white/10 rounded-2xl p-4 space-y-3">
                                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                                    <Eye className="w-4 h-4 text-indigo-400" /> Portada del Volumen
                                </h4>
                                <div className="flex gap-4 items-center">
                                    <div className="w-20 h-28 rounded-xl bg-slate-900 border border-white/10 overflow-hidden shrink-0 flex items-center justify-center">
                                        {formData.cover_url || bookData.cover_image || bookData.cover_thumb ? (
                                            <img
                                                src={formData.cover_url || bookData.cover_image || bookData.cover_thumb}
                                                alt="Portada"
                                                className="w-full h-full object-cover"
                                            />
                                        ) : (
                                            <BookOpen className="w-8 h-8 text-gray-600" />
                                        )}
                                    </div>
                                    <div className="space-y-2 flex-1">
                                        <label className="block text-[10px] font-bold text-gray-400 uppercase">
                                            URL de Portada
                                        </label>
                                        <input
                                            type="text"
                                            value={formData.cover_url || ''}
                                            onChange={(e) => setFormData({ ...formData, cover_url: e.target.value })}
                                            placeholder="/api/library/covers/..."
                                            className="w-full px-2.5 py-1.5 bg-slate-900 border border-white/10 rounded-lg text-xs text-white font-mono"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* Physical File & Maquetador Audit Box */}
                            <div className="bg-slate-950/60 border border-white/10 rounded-2xl p-4 space-y-3">
                                <div className="flex items-center justify-between border-b border-white/10 pb-2">
                                    <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider flex items-center gap-2">
                                        <AlertTriangle className="w-4 h-4 text-amber-400" /> Auditoría para Maquetador
                                    </h4>
                                    <button
                                        type="button"
                                        onClick={handleSyncPhysicalEpub}
                                        disabled={isSyncing}
                                        className="px-2.5 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold flex items-center gap-1.5 transition-all shadow-sm active:scale-95 disabled:opacity-50"
                                        title="Re-escanear metadatos directamente del archivo físico en disco"
                                    >
                                        <RefreshCw className={`w-3 h-3 ${isSyncing ? 'animate-spin' : ''}`} />
                                        <span>{isSyncing ? 'Re-escaneando...' : 'Re-escanear EPUB'}</span>
                                    </button>
                                </div>

                                {/* Filepath and Copy Button */}
                                <div className="space-y-1">
                                    <span className="text-[10px] font-bold text-gray-400 uppercase">Ruta en Disco:</span>
                                    <div className="flex items-center gap-2">
                                        <div
                                            className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-white/5 font-mono text-[10px] text-gray-300 truncate flex-1"
                                            title={formData.filepath || bookData.filepath || bookData.filename}
                                        >
                                            {formData.filepath || bookData.filepath || bookData.filename || 'Ruta no especificada'}
                                        </div>
                                        <button
                                            type="button"
                                            onClick={handleCopyPath}
                                            className={`px-2.5 py-1.5 rounded-lg text-[10px] font-bold flex items-center gap-1 transition-all shrink-0 ${
                                                copiedPath
                                                    ? 'bg-emerald-500 text-black'
                                                    : 'bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10'
                                            }`}
                                            title="Copiar ruta absoluta del archivo EPUB para editar en Sigil/Calibre"
                                        >
                                            {copiedPath ? (
                                                <>
                                                    <Check className="w-3 h-3 stroke-[3]" />
                                                    <span>¡Copiado!</span>
                                                </>
                                            ) : (
                                                <>
                                                    <Copy className="w-3 h-3" />
                                                    <span>Copiar</span>
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </div>

                                {/* Observations List */}
                                <div className="pt-2 border-t border-white/5 space-y-1.5">
                                    <span className="text-[10px] font-bold text-gray-400 uppercase">Estado de Consistencia:</span>
                                    {issues.length > 0 ? (
                                        <div className="space-y-1.5">
                                            {issues.map((iss, idx) => (
                                                <div
                                                    key={idx}
                                                    className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-200 text-[11px] flex items-center gap-2"
                                                >
                                                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                                                    <span>{iss}</span>
                                                </div>
                                            ))}
                                            <p className="text-[10px] text-gray-400 italic pt-1">
                                                Tip: Corrige los metadatos en el archivo con Sigil/Calibre y pulsa "Re-escanear EPUB" para sincronizar de inmediato.
                                            </p>
                                        </div>
                                    ) : (
                                        <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2 font-bold">
                                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                                            <span>Metadatos completos y consistentes con el archivo.</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Linked Series Card */}
                            {(bookData.series_name || seriesData?.name || formData.series_id) && (
                                <div className="bg-slate-950/60 border border-white/10 rounded-2xl p-4 space-y-2">
                                    <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2">
                                        <Layers className="w-4 h-4 text-indigo-400" /> Serie Vinculada
                                    </h4>
                                    <p className="text-xs font-bold text-white truncate">
                                        {seriesData?.name_spanish || seriesData?.name || bookData.series_spanish || bookData.series_name || 'Serie asociada'}
                                    </p>
                                    {formData.series_id && (
                                        <a
                                            href={`/app-v2/series/${formData.series_id}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-bold pt-1"
                                        >
                                            <span>Ver serie completa</span>
                                            <ExternalLink className="w-3 h-3" />
                                        </a>
                                    )}
                                </div>
                            )}
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};
