import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
    ArrowLeft,
    Send,
    Save,
    RotateCcw,
    CheckCircle2,
    AlertCircle,
    Loader2,
    Building2,
    Calendar,
    BookOpen,
    Sparkles,
    LayoutTemplate,
    ExternalLink
} from 'lucide-react';
import { api } from '@shared/services/api';
import { TelegramRichMessageEditor } from '../components/TelegramRichMessageEditor';
import { TelegramMessagePreview } from '../components/TelegramMessagePreview';

export const EditorialPostEdit: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const [post, setPost] = useState<any | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [caption, setCaption] = useState('');
    const [templates, setTemplates] = useState<any[]>([]);
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const fetchPostAndTemplates = async () => {
        setLoading(true);
        try {
            // 1. Fetch queue items to find this post
            const queueRes = await api.pubGetQueue(undefined, 100);
            const items = queueRes?.items || [];
            const found = items.find((i: any) => String(i.id) === String(id) || String(i.book_hash) === String(id));

            if (found) {
                setPost(found);
                const initialCaption = found.payload?.caption || found.caption || '';
                setCaption(initialCaption);
            }

            // 2. Fetch templates for quick insertion
            const tplRes = await api.pubGetTemplates();
            setTemplates(tplRes?.templates || []);
        } catch (err: any) {
            console.error('Error cargando publicación:', err);
            setStatusMsg({ type: 'error', text: 'Error cargando datos de la publicación' });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPostAndTemplates();
    }, [id]);

    const handleApplyTemplate = (tpl: any) => {
        if (!tpl?.content || !post) return;
        setCaption(tpl.content);
        setStatusMsg({ type: 'success', text: `Plantilla "${tpl.name}" aplicada en el editor` });
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!caption.trim()) {
            setStatusMsg({ type: 'error', text: 'El mensaje no puede estar vacío.' });
            return;
        }

        setSaving(true);
        setStatusMsg(null);

        try {
            await api.pubUpdatePost({
                book_id: post.book_hash || post.id,
                book_hash: post.book_hash,
                caption: caption,
                platforms: [post.platform ? post.platform.toLowerCase() : 'telegram'],
            });

            setStatusMsg({ type: 'success', text: '¡Mensaje actualizado exitosamente en Telegram!' });
        } catch (err: any) {
            console.error('Error actualizando post:', err);
            setStatusMsg({ type: 'error', text: err.message || 'Error al actualizar el mensaje en Telegram' });
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="w-full py-32 flex flex-col items-center justify-center gap-4">
                <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
                <span className="text-xs text-gray-400 font-mono">Cargando publicación oficial...</span>
            </div>
        );
    }

    if (!post) {
        return (
            <div className="w-full max-w-2xl mx-auto py-24 text-center space-y-4">
                <AlertCircle className="w-12 h-12 text-red-400 mx-auto" />
                <h3 className="text-xl font-bold text-white">Publicación no encontrada</h3>
                <p className="text-xs text-gray-400">No se pudo localizar el post con ID #{id}.</p>
                <Link
                    to="/app-v2/posts"
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-bold transition-all"
                >
                    <ArrowLeft className="w-4 h-4" /> Volver al Historial
                </Link>
            </div>
        );
    }

    return (
        <div className="w-full max-w-[2400px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Top Navigation & Action Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate('/app-v2/posts')}
                        className="p-2.5 rounded-2xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 transition-all active:scale-95"
                        title="Volver al Historial"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <div className="flex items-center gap-2">
                            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
                                {post.series || 'Publicación'}
                            </h2>
                            <span className="px-2.5 py-0.5 rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-black">
                                Vol. {post.volume || 1}
                            </span>
                            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-black uppercase">
                                {post.platform || 'Telegram'}
                            </span>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-gray-400 mt-1">
                            <span className="flex items-center gap-1 text-gray-300">
                                <Building2 className="w-3.5 h-3.5 text-indigo-400" /> {post.channel || 'Canal Oficial'}
                            </span>
                            <span>•</span>
                            <span className="flex items-center gap-1 font-mono text-gray-400 text-[11px]">
                                <Calendar className="w-3 h-3" />
                                {post.published_at ? new Date(post.published_at).toLocaleString('es-ES') : 'Completado'}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={() => navigate('/app-v2/posts')}
                        className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold border border-white/10 transition-all"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white text-xs font-black flex items-center gap-2 shadow-lg shadow-indigo-600/30 active:scale-95 transition-all disabled:opacity-50"
                    >
                        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        <span>Guardar y Actualizar en Telegram</span>
                    </button>
                </div>
            </div>

            {statusMsg && (
                <div
                    className={`p-4 rounded-2xl flex items-center gap-3 text-xs font-medium ${
                        statusMsg.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : 'bg-red-500/10 text-red-300 border border-red-500/20'
                    }`}
                >
                    {statusMsg.type === 'success' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                        <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                    )}
                    <span>{statusMsg.text}</span>
                </div>
            )}

            {/* Quick Template Applicator Bar */}
            {templates.length > 0 && (
                <div className="p-3.5 rounded-2xl bg-slate-900/50 border border-white/10 backdrop-blur-xl flex items-center gap-3 overflow-x-auto shadow-lg">
                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider shrink-0 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Insertar Plantilla Guardada:
                    </span>
                    <div className="flex items-center gap-2">
                        {templates.map((tpl) => (
                            <button
                                key={tpl.id}
                                type="button"
                                onClick={() => handleApplyTemplate(tpl)}
                                className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-indigo-600/30 text-gray-300 hover:text-white border border-white/5 hover:border-indigo-500/30 text-xs font-medium shrink-0 transition-all active:scale-95"
                            >
                                {tpl.name}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* 50/50 2K Grid: Editor on Left, Official Live Simulator on Right */}
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
                {/* 1. Left 6 cols: Rich Copy Editor */}
                <div className="xl:col-span-6 space-y-3 bg-slate-900/40 border border-white/10 rounded-3xl p-5 sm:p-6 backdrop-blur-2xl shadow-2xl flex flex-col">
                    <div className="flex items-center justify-between pb-2 border-b border-white/5">
                        <label className="text-xs font-bold text-white uppercase flex items-center gap-2">
                            <LayoutTemplate className="w-4 h-4 text-indigo-400" /> Contenido del Mensaje
                        </label>
                        <span className="text-[11px] text-gray-400 font-mono">
                            Modifica el texto para editar el post en vivo
                        </span>
                    </div>

                    <TelegramRichMessageEditor
                        value={caption}
                        onChange={setCaption}
                        platform={(post.platform || 'telegram').toLowerCase()}
                    />
                </div>

                {/* 2. Right 6 cols: Official Telegram Live Simulator */}
                <div className="xl:col-span-6 space-y-3 bg-slate-900/40 border border-white/10 rounded-3xl p-5 sm:p-6 backdrop-blur-2xl shadow-2xl flex flex-col">
                    <div className="flex items-center justify-between pb-2 border-b border-white/5">
                        <label className="text-xs font-bold text-white uppercase flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-amber-400" /> Previsualización en Vivo (Simulador Oficial)
                        </label>
                        <span className="text-[11px] text-emerald-400 font-bold flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" /> Tiempo Real
                        </span>
                    </div>

                    <div className="flex-1 min-h-[600px]">
                        <TelegramMessagePreview
                            rawTemplate={caption}
                            platform={(post.platform || 'telegram').toLowerCase()}
                            sampleBook={{
                                serie: post.series || post.series_name,
                                series: post.series || post.series_name,
                                series_name: post.series || post.series_name,
                                series_english: post.series_english || post.series,
                                series_spanish: post.series_spanish || post.title,
                                romaji_title: post.romaji_title || post.series,
                                volumen: String(post.volume || 1),
                                volume: String(post.volume || 1),
                                autor: post.author || 'Autor',
                                author: post.author || 'Autor',
                                illustrator: post.illustrator || 'Ilustrador',
                                translator: post.translator || 'Fansub',
                                traductor: post.translator || 'Fansub',
                                editorial: post.workgroup_name || post.publisher || 'Editorial',
                                sinopsis: post.synopsis || post.description || 'Sinopsis del libro.',
                                slug: (post.series || 'Novela').replace(/[^a-zA-Z0-9]/g, '_'),
                                download_link: `https://t.me/zeepub_bot?start=dl_${post.book_hash || post.id}`,
                                cover_url: post.cover_url || post.cover_thumb || '',
                            }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};
