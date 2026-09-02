import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
    ArrowLeft,
    Download,
    Send,
    Star,
    Flag,
    FileText,
    Calendar,
    ChevronDown,
    ChevronUp,
    Radio,
    BookOpen,
    Loader2,
    CheckCircle2,
    AlertCircle,
    User,
    Sparkles,
    Building2,
    ExternalLink,
    Layers,
    Clock,
    FileSpreadsheet,
    Hash
} from 'lucide-react';
import { api } from '@shared/services/api';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { ReportIssueModal } from '@shared/components/ReportIssueModal';
import { RatingModal } from '@features/book/components/RatingModal';
import { SchedulePostModal } from '../components/SchedulePostModal';
import { getCoverUrl } from '@shared/utils/imageUtils';

export const EditorialBookDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { webApp, isAdmin, isStaff } = useTelegram();

    const [book, setBook] = useState<any | null>(null);
    const [series, setSeries] = useState<any | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Modals state
    const [isReportOpen, setIsReportOpen] = useState(false);
    const [isRatingOpen, setIsRatingOpen] = useState(false);
    const [isScheduleOpen, setIsScheduleOpen] = useState(false);
    const [isSpecsOpen, setIsSpecsOpen] = useState(false);
    const [fullscreenCover, setFullscreenCover] = useState(false);

    // Action states
    const [downloadingTelegram, setDownloadingTelegram] = useState(false);
    const [sendingTemplate, setSendingTemplate] = useState(false);
    const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

    const fetchBookData = async () => {
        if (!id) return;
        setLoading(true);
        setError(null);
        try {
            const res = await api.getBookDetail(id);
            const bookData = res?.book || (res?.id ? res : null);
            if (bookData) {
                setBook(bookData);
                if (bookData.series_info) {
                    setSeries(bookData.series_info);
                } else if (bookData.series_id) {
                    try {
                        const sRes = await api.getSeriesDetail(bookData.series_id);
                        if (sRes?.series) setSeries(sRes.series);
                    } catch (e) {
                        console.warn('No se pudo cargar la serie asociada:', e);
                    }
                }
            } else {
                setError('No se pudo localizar este libro EPUB.');
            }
        } catch (err: any) {
            console.error('Error cargando libro:', err);
            setError(err.message || 'Error al cargar la información del libro.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBookData();
    }, [id]);

    const handleDirectDownload = () => {
        if (!book) return;
        const downloadUrl = `/api/library/download/${book.id || book.book_hash}`;
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `${book.title || 'libro'}.epub`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setFeedbackMsg({ type: 'success', text: 'Iniciando descarga en el navegador...' });
        setTimeout(() => setFeedbackMsg(null), 4000);
    };

    const handleTelegramDownload = async () => {
        if (!book) return;
        setDownloadingTelegram(true);
        try {
            webApp?.HapticFeedback?.impactOccurred('medium');
            await api.requestDownload(book.id || book.book_hash, 'private');
            webApp?.HapticFeedback?.notificationOccurred('success');
            setFeedbackMsg({ type: 'success', text: '¡Libro enviado con éxito a tu chat privado de Telegram!' });
        } catch (err: any) {
            webApp?.HapticFeedback?.notificationOccurred('error');
            setFeedbackMsg({ type: 'error', text: err.message || 'No se pudo enviar el libro a Telegram.' });
        } finally {
            setDownloadingTelegram(false);
            setTimeout(() => setFeedbackMsg(null), 5000);
        }
    };

    const handleSendTemplate = async () => {
        if (!book) return;
        setSendingTemplate(true);
        try {
            webApp?.HapticFeedback?.impactOccurred('light');
            await api.sendTemplateToTelegram(book.id || book.book_hash);
            webApp?.HapticFeedback?.notificationOccurred('success');
            setFeedbackMsg({ type: 'success', text: 'Plantilla y portada enviadas a tu Telegram.' });
        } catch (err: any) {
            setFeedbackMsg({ type: 'error', text: err.message || 'Error al enviar la plantilla.' });
        } finally {
            setSendingTemplate(false);
            setTimeout(() => setFeedbackMsg(null), 5000);
        }
    };

    const formatDate = (dateStr?: string | null) => {
        if (!dateStr) return 'Reciente';
        try {
            const cleaned = String(dateStr).replace(/\+00:00Z$/, 'Z').replace(/\+00:00$/, 'Z');
            const d = new Date(cleaned);
            if (!isNaN(d.getTime())) {
                return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
            }
            return dateStr;
        } catch {
            return dateStr;
        }
    };

    if (loading) {
        return (
            <div className="w-full py-32 flex flex-col items-center justify-center gap-4">
                <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
                <span className="text-xs text-gray-400 font-mono">Cargando información del EPUB...</span>
            </div>
        );
    }

    if (error || !book) {
        return (
            <div className="w-full max-w-2xl mx-auto py-24 text-center space-y-4">
                <AlertCircle className="w-12 h-12 text-red-400 mx-auto" />
                <h3 className="text-xl font-bold text-white">Error de Carga</h3>
                <p className="text-xs text-gray-400">{error || 'Libro no encontrado'}</p>
                <button
                    onClick={() => navigate(-1)}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-bold transition-all"
                >
                    <ArrowLeft className="w-4 h-4" /> Volver Atrás
                </button>
            </div>
        );
    }

    // Cover extraction
    const coverUrl =
        book.cover_high ||
        book.cover_medium ||
        book.cover_original ||
        book.cover_url ||
        (typeof book.coverUrl === 'string' ? book.coverUrl : book.coverUrl?.cover_high || book.coverUrl?.cover_medium) ||
        (book.book_hash ? `/api/library/covers/${book.book_hash}.jpg` : `/api/library/covers/${book.id}.jpg`);

    const seriesTitle = series?.series_english || series?.name || book.series_english || book.series_name || book.title;
    const seriesId = series?.series_hash || series?.id || book.series_id;
    const genres = series?.tags || book.genres || book.tags || [];
    const publications = book.publications || [];

    return (
        <div className="w-full max-w-[2000px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Breadcrumbs Navigation */}
            <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-2 text-xs text-gray-400 flex-wrap">
                    <button
                        onClick={() => navigate('/app-v2/library')}
                        className="hover:text-white transition-colors flex items-center gap-1 font-medium"
                    >
                        <Layers className="w-3.5 h-3.5 text-indigo-400" /> Catálogo Editorial
                    </button>
                    <span>›</span>
                    {seriesId ? (
                        <button
                            onClick={() => navigate(`/app-v2/series/${seriesId}`)}
                            className="hover:text-white transition-colors font-medium truncate max-w-[200px]"
                        >
                            {seriesTitle}
                        </button>
                    ) : (
                        <span className="truncate max-w-[200px]">{seriesTitle}</span>
                    )}
                    <span>›</span>
                    <span className="text-white font-bold">
                        {book.volume ? `Volumen ${book.volume}` : book.title}
                    </span>
                </div>

                <button
                    onClick={() => navigate(-1)}
                    className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 transition-all flex items-center gap-1.5 text-xs font-bold active:scale-95"
                >
                    <ArrowLeft className="w-4 h-4" /> <span>Volver</span>
                </button>
            </div>

            {/* Feedback Alert */}
            {feedbackMsg && (
                <div
                    className={`p-4 rounded-2xl flex items-center gap-3 text-xs font-bold shadow-xl animate-in fade-in slide-in-from-top-2 duration-200 ${
                        feedbackMsg.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : 'bg-red-500/10 text-red-300 border border-red-500/20'
                    }`}
                >
                    {feedbackMsg.type === 'success' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                        <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                    )}
                    <span>{feedbackMsg.text}</span>
                </div>
            )}

            {/* Main Dual-Column Grid Layout matching Reference UI */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                {/* 1. LEFT COLUMN: Cover + Actions + Metrics (4 cols on lg/xl) */}
                <div className="lg:col-span-4 xl:col-span-4 space-y-5">
                    {/* Cover Box with Glow */}
                    <div className="relative group cursor-pointer" onClick={() => setFullscreenCover(true)}>
                        <div className="absolute -inset-2 bg-indigo-500/20 rounded-[2.5rem] blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
                        <div className="relative aspect-[2/3] rounded-[2rem] overflow-hidden shadow-2xl border border-white/10 bg-slate-950/80 group-hover:border-indigo-500/40 group-hover:-translate-y-1 transition-all duration-500">
                            {coverUrl ? (
                                <img
                                    src={coverUrl}
                                    alt={book.title}
                                    className="w-full h-full object-cover"
                                />
                            ) : (
                                <div className="w-full h-full flex flex-col items-center justify-center text-gray-600 gap-2">
                                    <BookOpen className="w-12 h-12" />
                                    <span className="text-xs">Sin Portada</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Action Buttons Box */}
                    <div className="space-y-2.5">
                        {/* Programar & Plantilla buttons */}
                        <div className="grid grid-cols-2 gap-2.5">
                            <button
                                type="button"
                                onClick={() => setIsScheduleOpen(true)}
                                className="py-3 px-3 rounded-2xl bg-indigo-600/15 hover:bg-indigo-600/25 border border-indigo-500/30 text-indigo-300 hover:text-white text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 transition-all active:scale-95 shadow-lg"
                            >
                                <Send className="w-3.5 h-3.5 text-indigo-400" />
                                <span>Programar</span>
                            </button>

                            <button
                                type="button"
                                onClick={handleSendTemplate}
                                disabled={sendingTemplate}
                                className="py-3 px-3 rounded-2xl bg-cyan-600/15 hover:bg-cyan-600/25 border border-cyan-500/30 text-cyan-300 hover:text-white text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 transition-all active:scale-95 shadow-lg disabled:opacity-50"
                            >
                                {sendingTemplate ? (
                                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                ) : (
                                    <FileText className="w-3.5 h-3.5 text-cyan-400" />
                                )}
                                <span>Plantilla</span>
                            </button>
                        </div>

                        {/* Direct Browser Download Button */}
                        <button
                            type="button"
                            onClick={handleDirectDownload}
                            className="w-full py-3.5 px-4 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2.5 shadow-xl shadow-blue-600/30 hover:shadow-blue-500/50 transition-all active:scale-95"
                        >
                            <Download className="w-4 h-4" />
                            <span>Descargar en Navegador</span>
                        </button>

                        {/* Telegram Download Button */}
                        <button
                            type="button"
                            onClick={handleTelegramDownload}
                            disabled={downloadingTelegram}
                            className="w-full py-3 px-4 rounded-2xl bg-slate-900/90 hover:bg-slate-800 border border-white/10 hover:border-white/20 text-white text-xs font-bold flex items-center justify-center gap-2.5 transition-all active:scale-95 disabled:opacity-50 shadow-lg"
                        >
                            {downloadingTelegram ? (
                                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                            ) : (
                                <Send className="w-4 h-4 text-cyan-400" />
                            )}
                            <span>Enviar a mi Telegram</span>
                        </button>

                        {/* Rating and Report Buttons */}
                        <div className="grid grid-cols-2 gap-2.5">
                            <button
                                type="button"
                                onClick={() => setIsRatingOpen(true)}
                                className="py-2.5 px-3 rounded-2xl bg-white/[0.03] hover:bg-white/[0.08] border border-white/10 text-gray-300 hover:text-white text-xs font-bold flex items-center justify-center gap-1.5 transition-all active:scale-95"
                            >
                                <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400/20" />
                                <span>Valorar</span>
                            </button>

                            <button
                                type="button"
                                onClick={() => setIsReportOpen(true)}
                                className="py-2.5 px-3 rounded-2xl bg-white/[0.03] hover:bg-red-500/10 border border-white/10 hover:border-red-500/30 text-gray-300 hover:text-red-300 text-xs font-bold flex items-center justify-center gap-1.5 transition-all active:scale-95"
                            >
                                <Flag className="w-3.5 h-3.5 text-red-400" />
                                <span>Reportar</span>
                            </button>
                        </div>
                    </div>

                    {/* Book Metrics Card */}
                    <div className="p-4 rounded-3xl bg-slate-900/50 border border-white/10 backdrop-blur-xl shadow-xl space-y-3">
                        <div className="flex items-center justify-between text-xs py-1 border-b border-white/5">
                            <span className="text-gray-400">Valoración</span>
                            <span className="font-bold text-white flex items-center gap-1">
                                <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                                <span>{book.rating ? `${Number(book.rating).toFixed(1)} / 5.0` : '—'}</span>
                            </span>
                        </div>

                        <div className="flex items-center justify-between text-xs py-1 border-b border-white/5">
                            <span className="text-gray-400">Descargas Totales</span>
                            <span className="font-bold text-white flex items-center gap-1">
                                <Download className="w-3.5 h-3.5 text-cyan-400" />
                                <span>{book.download_count || book.downloads || 0}</span>
                            </span>
                        </div>

                        <div className="flex items-center justify-between text-xs py-1">
                            <span className="text-gray-400">Última Actualización</span>
                            <span className="font-mono text-gray-300 text-[11px]">
                                {formatDate(book.updated_at || book.created_at)}
                            </span>
                        </div>
                    </div>
                </div>

                {/* 2. RIGHT COLUMN: Meta + Synopsis + Specs + Publications (8 cols on lg/xl) */}
                <div className="lg:col-span-8 xl:col-span-8 space-y-6">
                    {/* Workgroup / Fansub Badge */}
                    {book.workgroup || book.editorial || book.grupo_traductor ? (
                        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-600/10 border border-indigo-500/30 text-indigo-300 text-xs font-black tracking-wider">
                            <Building2 className="w-3.5 h-3.5 text-indigo-400" />
                            <span>{book.workgroup || book.editorial || book.grupo_traductor}</span>
                        </div>
                    ) : null}

                    {/* Big Title Header */}
                    <div className="space-y-2">
                        <h1 className="text-3xl sm:text-4xl 2xl:text-5xl font-black text-white tracking-tight leading-tight">
                            {seriesTitle}
                        </h1>

                        {/* Metadata row */}
                        <div className="flex items-center gap-4 text-xs text-gray-400 flex-wrap pt-1 font-medium">
                            <span className="flex items-center gap-1.5 text-gray-300">
                                <User className="w-3.5 h-3.5 text-indigo-400" />
                                <span>{book.author || series?.author || 'Autor desconocido'}</span>
                            </span>
                            {book.volume && (
                                <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-white/5 text-gray-300 font-mono font-bold">
                                    <Hash className="w-3 h-3 text-indigo-400" /> {book.volume}
                                </span>
                            )}
                            {book.translator && (
                                <span className="flex items-center gap-1.5 text-gray-300">
                                    <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                                    <span>{book.translator}</span>
                                </span>
                            )}
                            <span className="flex items-center gap-1.5 text-gray-400">
                                <Clock className="w-3.5 h-3.5 text-gray-500" />
                                <span>Actualizado: {formatDate(book.updated_at || book.created_at)}</span>
                            </span>
                        </div>
                    </div>

                    {/* Genre Chips */}
                    {genres && genres.length > 0 && (
                        <div className="flex items-center gap-2 flex-wrap">
                            {genres.map((g: string, idx: number) => (
                                <span
                                    key={idx}
                                    className="px-3 py-1 rounded-xl bg-slate-900/80 border border-white/10 text-[10px] font-black uppercase tracking-wider text-gray-300 hover:text-white hover:border-indigo-500/40 transition-colors cursor-default"
                                >
                                    {g}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Synopsis Card */}
                    <div className="p-6 sm:p-7 rounded-3xl bg-slate-900/50 border border-white/10 backdrop-blur-xl shadow-xl space-y-3">
                        <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-indigo-400">
                            <FileText className="w-4 h-4" />
                            <span>Sinopsis</span>
                        </div>
                        <div className="text-xs sm:text-sm text-gray-300 leading-relaxed space-y-3 whitespace-pre-line font-normal">
                            {book.synopsis || book.description || series?.description || 'Sin sinopsis registrada para este volumen.'}
                        </div>
                    </div>

                    {/* Collapsible Ficha Técnica Card */}
                    <div className="rounded-3xl bg-slate-900/50 border border-white/10 backdrop-blur-xl shadow-xl overflow-hidden">
                        <button
                            type="button"
                            onClick={() => setIsSpecsOpen(!isSpecsOpen)}
                            className="w-full p-5 sm:p-6 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
                        >
                            <div className="flex items-center gap-2.5 text-xs font-black uppercase tracking-wider text-white">
                                <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
                                <span>Ficha Técnica</span>
                            </div>
                            <div className="p-1 rounded-lg bg-white/5 text-gray-400">
                                {isSpecsOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </div>
                        </button>

                        {isSpecsOpen && (
                            <div className="p-5 sm:p-6 pt-0 border-t border-white/5 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs animate-in fade-in duration-200">
                                <div className="space-y-2">
                                    <div className="flex justify-between py-1 border-b border-white/5">
                                        <span className="text-gray-400">📄 Formato:</span>
                                        <span className="font-bold text-white">EPUB 3.0</span>
                                    </div>
                                    <div className="flex justify-between py-1 border-b border-white/5">
                                        <span className="text-gray-400">📑 Páginas estimadas:</span>
                                        <span className="font-bold text-white">~{book.page_count || book.pages || 250} págs</span>
                                    </div>
                                    <div className="flex justify-between py-1 border-b border-white/5">
                                        <span className="text-gray-400">📝 Palabras:</span>
                                        <span className="font-bold text-white">{book.word_count || book.words || '—'} palabras</span>
                                    </div>
                                    <div className="flex justify-between py-1">
                                        <span className="text-gray-400">⏱️ Tiempo de lectura:</span>
                                        <span className="font-bold text-white">{book.reading_time || '5h 30m aprox.'}</span>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <div className="flex justify-between py-1 border-b border-white/5">
                                        <span className="text-gray-400">👤 Autor:</span>
                                        <span className="font-bold text-white">{book.author || series?.author || '—'}</span>
                                    </div>
                                    <div className="flex justify-between py-1 border-b border-white/5">
                                        <span className="text-gray-400">🎨 Ilustrador:</span>
                                        <span className="font-bold text-white">{book.illustrator || series?.illustrator || '—'}</span>
                                    </div>
                                    <div className="flex justify-between py-1 border-b border-white/5">
                                        <span className="text-gray-400">📦 Demografía:</span>
                                        <span className="font-bold text-white">{series?.demographics?.[0] || series?.demography || 'General'}</span>
                                    </div>
                                    <div className="flex justify-between py-1">
                                        <span className="text-gray-400">💾 Tamaño de archivo:</span>
                                        <span className="font-bold text-white">{book.size_mb ? `${book.size_mb} MB` : (book.file_size ? `${(book.file_size / 1024 / 1024).toFixed(2)} MB` : '—')}</span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Book Publications History Card */}
                    <div className="p-6 sm:p-7 rounded-3xl bg-slate-900/50 border border-white/10 backdrop-blur-xl shadow-xl space-y-4">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2.5 rounded-2xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shadow-lg">
                                    <Radio className="w-5 h-5" />
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <h3 className="text-xs sm:text-sm font-black uppercase tracking-wider text-white">
                                            Historial de Publicaciones
                                        </h3>
                                        <span className="px-2 py-0.5 rounded-full bg-white/5 text-gray-400 font-mono text-[10px] font-bold">
                                            {publications.length}
                                        </span>
                                    </div>
                                    <p className="text-[11px] text-gray-400 mt-0.5">
                                        {publications.length > 0
                                            ? `${publications.length} emisiones realizadas en canales y redes.`
                                            : 'Sin registros de emisión en Facebook / Telegram para este volumen.'}
                                    </p>
                                </div>
                            </div>

                            <button
                                type="button"
                                onClick={() => setIsScheduleOpen(true)}
                                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-black flex items-center gap-2 shadow-lg shadow-blue-600/30 transition-all active:scale-95 shrink-0 self-start sm:self-center"
                            >
                                <Send className="w-3.5 h-3.5" />
                                <span>Publicar en Redes</span>
                            </button>
                        </div>

                        {publications.length > 0 && (
                            <div className="space-y-2 pt-2">
                                {publications.map((p: any, idx: number) => (
                                    <div
                                        key={idx}
                                        className="p-3.5 rounded-2xl bg-slate-950/70 border border-white/5 flex items-center justify-between gap-3 text-xs"
                                    >
                                        <div className="flex items-center gap-3">
                                            <span
                                                className={`px-2 py-0.5 rounded-md text-[10px] font-black uppercase ${
                                                    p.platform === 'facebook'
                                                        ? 'bg-blue-500/20 text-blue-300'
                                                        : 'bg-cyan-500/20 text-cyan-300'
                                                }`}
                                            >
                                                {p.platform || 'Telegram'}
                                            </span>
                                            <span className="text-gray-300 font-medium">
                                                {p.channel_name || p.channel || 'Canal Oficial'}
                                            </span>
                                            <span className="text-[10px] text-gray-500 font-mono">
                                                {formatDate(p.published_at)}
                                            </span>
                                        </div>

                                        {p.post_url && (
                                            <a
                                                href={p.post_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-[11px] font-bold flex items-center gap-1 transition-all"
                                            >
                                                <span>Ver Post</span>
                                                <ExternalLink className="w-3 h-3" />
                                            </a>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Fullscreen Cover Modal */}
            {fullscreenCover && (
                <div
                    className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 cursor-pointer"
                    onClick={() => setFullscreenCover(false)}
                >
                    <img
                        src={coverUrl}
                        alt={book.title}
                        className="max-h-[90vh] max-w-[90vw] object-contain rounded-2xl shadow-2xl border border-white/10 animate-in zoom-in-95 duration-200"
                    />
                </div>
            )}

            {/* Schedule / Publish Modal */}
            {isScheduleOpen && (
                <SchedulePostModal
                    isOpen={isScheduleOpen}
                    onClose={() => setIsScheduleOpen(false)}
                    initialBook={book}
                />
            )}

            {/* Rating Modal */}
            {isRatingOpen && (
                <RatingModal
                    isOpen={isRatingOpen}
                    onClose={() => setIsRatingOpen(false)}
                    bookId={book.id || book.book_hash}
                    currentRating={book.rating || 0}
                    onRatingSubmitted={(newRating) => {
                        setBook({ ...book, rating: newRating });
                        setFeedbackMsg({ type: 'success', text: `¡Gracias por tu valoración de ${newRating} estrellas!` });
                        setTimeout(() => setFeedbackMsg(null), 4000);
                    }}
                />
            )}

            {/* Report Issue Modal */}
            {isReportOpen && (
                <ReportIssueModal
                    isOpen={isReportOpen}
                    onClose={() => setIsReportOpen(false)}
                    bookId={book.id || book.book_hash}
                    bookTitle={`${seriesTitle} - Vol. ${book.volume || 1}`}
                />
            )}
        </div>
    );
};
