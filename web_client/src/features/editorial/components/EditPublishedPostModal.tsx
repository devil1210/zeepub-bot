import React, { useState } from 'react';
import {
    X,
    Send,
    Edit3,
    CheckCircle2,
    AlertCircle,
    Loader2,
    Sparkles,
    Eye,
    Tag
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

    const [caption, setCaption] = useState(post.payload?.caption || post.caption || '');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMsg, setSuccessMsg] = useState<string | null>(null);
    const [viewMode, setViewMode] = useState<'editor' | 'preview'>('editor');

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
                                Vista Previa
                            </button>
                        </div>

                        <button
                            onClick={onClose}
                            className="p-2.5 rounded-2xl text-gray-400 hover:text-white hover:bg-white/10 transition-all"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Body Content */}
                <div className="flex-1 overflow-y-auto p-5 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
                    {/* Left: Editor (7 cols) */}
                    <div className={`space-y-3 lg:col-span-7 ${viewMode === 'preview' ? 'hidden lg:block' : 'block'}`}>
                        <div className="flex items-center justify-between">
                            <label className="text-xs font-bold uppercase tracking-wider text-gray-400">
                                Contenido / Caption de Telegram
                            </label>
                            <span className="text-[11px] text-gray-500">Formato HTML de Telegram</span>
                        </div>

                        <TelegramRichMessageEditor
                            value={caption}
                            onChange={setCaption}
                            platform="telegram"
                        />
                    </div>

                    {/* Right: Live Telegram Simulator (5 cols) */}
                    <div className={`space-y-3 lg:col-span-5 ${viewMode === 'editor' ? 'hidden lg:block' : 'block'}`}>
                        <div className="flex items-center justify-between">
                            <label className="text-xs font-bold uppercase tracking-wider text-gray-400">
                                Previsualización en Vivo (Simulador Oficial)
                            </label>
                            <span className="text-[11px] text-indigo-400 font-semibold flex items-center gap-1">
                                <Sparkles className="w-3.5 h-3.5" /> Tiempo Real
                            </span>
                        </div>

                        <div className="h-[480px] 2xl:h-[540px]">
                            <TelegramMessagePreview
                                rawTemplate={caption}
                                platform="telegram"
                                sampleBook={{
                                    serie: post.series || 'Novela',
                                    volumen: post.volume || 1,
                                    titulo: `Volumen ${post.volume || 1}`,
                                }}
                                isCaptionMode={true}
                            />
                        </div>
                    </div>
                </div>

                {/* Alerts */}
                {error && (
                    <div className="mx-6 mb-3 p-3.5 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                        <span>{error}</span>
                    </div>
                )}

                {successMsg && (
                    <div className="mx-6 mb-3 p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                        <span>{successMsg}</span>
                    </div>
                )}

                {/* Footer */}
                <div className="p-5 sm:p-6 border-t border-white/10 bg-slate-900/60 backdrop-blur-xl flex items-center justify-end gap-3">
                    <button
                        type="button"
                        onClick={onClose}
                        disabled={loading}
                        className="px-5 py-2.5 rounded-xl text-xs font-bold text-gray-400 hover:text-white hover:bg-white/5 transition-all"
                    >
                        Cancelar
                    </button>
                    <button
                        type="button"
                        onClick={handleSave}
                        disabled={loading}
                        className="px-7 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2.5 transition-all shadow-xl shadow-indigo-600/30 disabled:opacity-50"
                    >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        <span>Guardar y Actualizar en Telegram</span>
                    </button>
                </div>
            </div>
        </div>
    );
};
