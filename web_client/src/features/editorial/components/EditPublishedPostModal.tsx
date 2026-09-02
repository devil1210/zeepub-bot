import React, { useState, useEffect } from 'react';
import {
    X,
    Send,
    Edit3,
    CheckCircle2,
    AlertCircle,
    Loader2,
    Sparkles,
    Eye,
    Tag,
    Copy,
    FileText,
    RefreshCw
} from 'lucide-react';
import { api } from '@shared/services/api';
import { TelegramRichMessageEditor } from './TelegramRichMessageEditor';
import { TelegramMessagePreview } from './TelegramMessagePreview';

interface EditPublishedPostModalProps {
    isOpen: boolean;
    post: any | null;
    onClose: () => void;
    onSuccess: () => void;
}

export const EditPublishedPostModal: React.FC<EditPublishedPostModalProps> = ({
    isOpen,
    post,
    onClose,
    onSuccess,
}) => {
    if (!isOpen || !post) return null;

    const [caption, setCaption] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMsg, setSuccessMsg] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<'editor' | 'preview'>('editor');
    const [templates, setTemplates] = useState<any[]>([]);

    const buildDefaultCaption = (tplContent?: string) => {
        const seriesName = post.series || post.series_name || 'Novela Ligera';
        const vol = post.volume || 1;
        const author = post.author || 'Autor';
        const synopsis = post.synopsis || post.description || 'Sinopsis no disponible.';
        const hashtags = `#${seriesName.replace(/[^a-zA-Z0-9]/g, '')} #ZeePubs`;

        const template = tplContent || '<b>🇬🇧 {serie}</b>\n📚 <b>Volumen {volumen}</b>\n\n🏷 {hashtags}\n\n<details open>\n<summary>📋 <b>Ficha Técnica</b></summary>\n👤 <b>Autor:</b> {autor}\n📦 <b>Categoría:</b> Novela Ligera\n</details>\n\n<details>\n<summary>📖 <b>Ver Sinopsis</b></summary>\n{sinopsis}\n</details>\n\n📥 {link}';

        return template
            .replace(/{serie}/g, seriesName)
            .replace(/{volumen}/g, String(vol))
            .replace(/{autor}/g, author)
            .replace(/{sinopsis}/g, synopsis)
            .replace(/{hashtags}/g, hashtags)
            .replace(/{link}/g, `https://t.me/zeepub_bot?start=dl_${post.book_hash || post.id}`);
    };

    useEffect(() => {
        if (isOpen && post) {
            let initialCaption = post.payload?.caption || post.caption || '';
            if (!initialCaption.trim()) {
                initialCaption = buildDefaultCaption();
            }
            setCaption(initialCaption);

            // Fetch templates
            api.pubGetTemplates().then((res: any) => {
                const list = res?.templates || [];
                setTemplates(list);
            }).catch(console.error);

            setError(null);
            setSuccessMsg(null);
        }
    }, [isOpen, post]);

    const handleApplyTemplate = (tpl: any) => {
        if (!tpl?.content) return;
        const generated = buildDefaultCaption(tpl.content);
        setCaption(generated);
    };

    const handleSave = async () => {
        if (!caption.trim()) {
            setError('El contenido del mensaje no puede estar vacío');
            return;
        }

        setLoading(true);
        setError(null);
        setSuccessMsg(null);

        try {
            const res = await api.pubUpdatePost({
                book_id: post.book_hash,
                book_hash: post.book_hash,
                caption: caption,
                platforms: [post.platform ? post.platform.toLowerCase() : 'telegram'],
            });

            if (res && res.success) {
                setSuccessMsg('¡Mensaje actualizado exitosamente en Telegram!');
                setTimeout(() => {
                    onSuccess();
                    onClose();
                }, 1200);
            } else {
                setError(res?.error || 'No se pudo editar el mensaje en Telegram');
            }
        } catch (err: any) {
            console.error('Error actualizando post publicado:', err);
            setError(err.message || 'Error al conectar con la API de Telegram');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 lg:p-10 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
            <div className="relative w-full max-w-6xl 2xl:max-w-7xl h-[88vh] flex flex-col bg-slate-950 border border-white/10 rounded-3xl shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="p-5 sm:p-6 border-b border-white/10 flex items-center justify-between bg-slate-900/60 backdrop-blur-xl">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                            <Edit3 className="w-5 h-5" />
                        </div>
                        <div>
                            <h3 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                                Editar Mensaje Publicado en Telegram
                            </h3>
                            <p className="text-xs text-gray-400">
                                {post.series || 'Novela'} • Vol. {post.volume || 1} • Canal:{' '}
                                <strong className="text-gray-200">{post.channel}</strong>
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        {/* Tab Toggle for mobile / small screens */}
                        <div className="flex rounded-xl bg-slate-900 border border-white/10 p-0.5 lg:hidden">
                            <button
                                onClick={() => setViewMode('editor')}
                                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                                    viewMode === 'editor' ? 'bg-indigo-600 text-white' : 'text-gray-400'
                                }`}
                            >
                                Editor
                            </button>
                            <button
                                onClick={() => setViewMode('preview')}
                                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                                    viewMode === 'preview' ? 'bg-indigo-600 text-white' : 'text-gray-400'
                                }`}
                            >
                                Simulador
                            </button>
                        </div>

                        <button
                            onClick={onClose}
                            className="p-2 text-gray-400 hover:text-white rounded-xl hover:bg-white/10 transition-colors"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Alerts */}
                {error && (
                    <div className="mx-6 mt-4 p-3.5 rounded-2xl bg-red-500/10 border border-red-500/20 text-xs text-red-300 font-medium flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span>{error}</span>
                    </div>
                )}
                {successMsg && (
                    <div className="mx-6 mt-4 p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 font-medium flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 shrink-0" />
                        <span>{successMsg}</span>
                    </div>
                )}

                {/* Template Quick Paste Toolbar */}
                {templates.length > 0 && (
                    <div className="px-6 pt-3 flex flex-wrap items-center gap-2 border-b border-white/5 pb-3">
                        <span className="text-[11px] font-bold text-gray-400 uppercase flex items-center gap-1">
                            <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Insertar Plantilla:
                        </span>
                        {templates.map((tpl) => (
                            <button
                                key={tpl.id}
                                type="button"
                                onClick={() => handleApplyTemplate(tpl)}
                                className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-[11px] font-bold border border-white/5 transition-all"
                            >
                                {tpl.name}
                            </button>
                        ))}
                    </div>
                )}

                {/* Body (Side by Side on 2K / desktop) */}
                <div className="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-white/10">
                    {/* Left: Rich Editor (7 cols) */}
                    <div
                        className={`lg:col-span-7 flex flex-col p-5 overflow-y-auto space-y-4 ${
                            viewMode === 'editor' ? 'flex' : 'hidden lg:flex'
                        }`}
                    >
                        <div className="flex-1 flex flex-col min-h-0">
                            <TelegramRichMessageEditor
                                value={caption}
                                onChange={setCaption}
                                placeholder="Escribe aquí el copy usando etiquetas HTML de Telegram y variables..."
                            />
                        </div>
                    </div>

                    {/* Right: Live Telegram Simulator (5 cols) */}
                    <div
                        className={`lg:col-span-5 flex flex-col p-5 bg-[#0e1621]/40 overflow-y-auto ${
                            viewMode === 'preview' ? 'flex' : 'hidden lg:flex'
                        }`}
                    >
                        <div className="text-[11px] font-bold uppercase tracking-wider text-gray-400 mb-3 flex items-center justify-between">
                            <span>Previsualización en Vivo (Simulador Oficial)</span>
                            <span className="text-[10px] text-cyan-400 font-normal">✨ Tiempo Real</span>
                        </div>

                        <div className="flex-1 flex items-start justify-center">
                            <TelegramMessagePreview
                                templateContent={caption}
                                previewBook={{
                                    series_name: post.series || 'Baccano!',
                                    series_english: post.series || 'Baccano!',
                                    volume: post.volume || 3,
                                    author: post.author || 'Ryohgo Narita',
                                    illustrator: 'Katsumi Enami',
                                    translator: 'Clixea',
                                    demography: 'Seinen',
                                    synopsis: post.synopsis || 'En los años 30, una serie de sucesos violentos y alquímicos se desatan a bordo del tren transcontinental Flying Pussyfoot.',
                                    cover_url: post.cover_url,
                                }}
                            />
                        </div>
                    </div>
                </div>

                {/* Footer Controls */}
                <div className="p-4 sm:p-5 border-t border-white/10 bg-slate-900/80 flex items-center justify-between">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-xl text-xs font-bold text-gray-400 hover:text-white transition-colors"
                    >
                        Cancelar
                    </button>

                    <button
                        onClick={handleSave}
                        disabled={loading}
                        className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/30 active:scale-95 transition-all disabled:opacity-50"
                    >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        <span>Guardar y Actualizar en Telegram</span>
                    </button>
                </div>
            </div>
        </div>
    );
};
