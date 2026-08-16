// @ts-nocheck
import React, { useState, useEffect } from 'react';
import { X, Send, Calendar, Clock, CheckCircle, Hash, Edit3, RefreshCw, Sparkles, Copy, Check, AlertTriangle, FolderCheck, FolderPlus } from 'lucide-react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { usePublisher } from '../hooks/usePublisher';
import { publisherApi, PublicationQueueItem } from '../services/publisherApi';

interface ScheduleModalProps {
    isOpen: boolean;
    onClose: () => void;
    bookHash: string;
    bookTitle: string;
    editingItem?: PublicationQueueItem | null;
}

export const ScheduleModal: React.FC<ScheduleModalProps> = ({
    isOpen,
    onClose,
    bookHash: initialBookHash,
    bookTitle,
    editingItem
}) => {
    const { settings } = useTheme();
    const { channels, templates, schedulePublication, updateQueueItem } = usePublisher();

    const [bookHash, setBookHash] = useState(initialBookHash);
    const [selectedChannel, setSelectedChannel] = useState<number | ''>(editingItem?.channel_id || '');
    const [selectedTemplates, setSelectedTemplates] = useState<number[]>(
        editingItem?.template_id ? [editingItem.template_id] : []
    );
    const [scheduledFor, setScheduledFor] = useState(() => {
        if (editingItem) {
            const date = new Date(editingItem.scheduled_for);
            const tzOffset = date.getTimezoneOffset() * 60000;
            return new Date(date.getTime() - tzOffset).toISOString().slice(0, 16);
        }
        const now = new Date();
        now.setMinutes(now.getMinutes() + 10);
        const tzOffset = now.getTimezoneOffset() * 60000;
        return new Date(now.getTime() - tzOffset).toISOString().slice(0, 16);
    });

    const isSentItem = Boolean(editingItem && editingItem.status === 'sent');
    const [actionType, setActionType] = useState<'update_existing' | 'create_new'>('update_existing');

    const [selectedFbAlbumId, setSelectedFbAlbumId] = useState<string>('auto');

    useEffect(() => {
        if (isOpen) {
            setBookHash(editingItem?.book_hash || initialBookHash);
            const defaultChan = editingItem?.channel_id || (channels.find(c => c.is_favorite)?.id || (channels.length > 0 ? channels[0].id : ''));
            setSelectedChannel(defaultChan);
            setSelectedTemplates(editingItem?.template_id ? [editingItem.template_id] : []);
            setActionType(editingItem?.status === 'sent' ? 'update_existing' : 'create_new');
            setSelectedFbAlbumId(editingItem?.payload?.fb_album_id || 'auto');
            if (editingItem) {
                const date = new Date(editingItem.scheduled_for);
                const tzOffset = date.getTimezoneOffset() * 60000;
                setScheduledFor(new Date(date.getTime() - tzOffset).toISOString().slice(0, 16));
            } else {
                const now = new Date();
                now.setMinutes(now.getMinutes() + 10);
                const tzOffset = now.getTimezoneOffset() * 60000;
                setScheduledFor(new Date(now.getTime() - tzOffset).toISOString().slice(0, 16));
            }
            setIsImmediate(false);
            setIsSuccess(false);
        }
    }, [isOpen, editingItem, initialBookHash, channels]);

    const [isImmediate, setIsImmediate] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [successMsg, setSuccessMsg] = useState('¡Programado con éxito!');
    const [customCaption, setCustomCaption] = useState('');
    const [albumCheck, setAlbumCheck] = useState<{
        loading: boolean;
        exists?: boolean;
        album_name?: string;
        album_id?: string;
        recommended_name?: string;
        candidates?: string[];
        available_albums?: Array<{ id: string; name: string }>;
        error?: string;
    } | null>(null);
    const [copiedAlbumName, setCopiedAlbumName] = useState(false);

    const selectedChanObj = channels.find(c => c.id === Number(selectedChannel));
    const isFacebookChannel = selectedChanObj?.platform === 'facebook';

    useEffect(() => {
        if (!isOpen || !bookHash || !isFacebookChannel) {
            setAlbumCheck(null);
            return;
        }

        let isMounted = true;
        setAlbumCheck({ loading: true });

        publisherApi.checkFacebookAlbum(bookHash, Number(selectedChannel))
            .then((res: any) => {
                if (!isMounted) return;
                setAlbumCheck({
                    loading: false,
                    exists: res.exists,
                    album_name: res.album_name,
                    album_id: res.album_id,
                    recommended_name: res.recommended_name,
                    candidates: res.candidates,
                    available_albums: res.available_albums || [],
                    error: res.error,
                });
            })
            .catch((err: any) => {
                if (!isMounted) return;
                setAlbumCheck({
                    loading: false,
                    exists: false,
                    available_albums: [],
                    error: err.message,
                });
            });

        return () => {
            isMounted = false;
        };
    }, [isOpen, bookHash, selectedChannel, isFacebookChannel]);

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopiedAlbumName(true);
        setTimeout(() => setCopiedAlbumName(false), 2000);
    };

    const HOURS = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'));
    const MINUTES = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'));

    const datePart = scheduledFor ? scheduledFor.slice(0, 10) : '';
    const hourPart = scheduledFor && scheduledFor.includes('T') ? scheduledFor.slice(11, 13) : '10';
    const minutePart = scheduledFor && scheduledFor.includes('T') ? scheduledFor.slice(14, 16) : '00';

    const updateDateTime = (newDate: string, newHour: string, newMinute: string) => {
        const d = newDate || new Date().toISOString().slice(0, 10);
        const h = (newHour || '10').padStart(2, '0');
        const m = (newMinute || '00').padStart(2, '0');
        setScheduledFor(`${d}T${h}:${m}`);
    };

    const applyPreset = (minutesToAdd: number, targetHour?: number) => {
        const now = new Date();
        if (targetHour !== undefined) {
            if (minutesToAdd > 0) now.setDate(now.getDate() + 1);
            now.setHours(targetHour, 0, 0, 0);
        } else {
            now.setMinutes(now.getMinutes() + minutesToAdd);
        }
        const tzOffset = now.getTimezoneOffset() * 60000;
        setScheduledFor(new Date(now.getTime() - tzOffset).toISOString().slice(0, 16));
    };

    const getFormattedPreview = () => {
        try {
            if (!scheduledFor) return '';
            const d = new Date(scheduledFor);
            if (isNaN(d.getTime())) return '';
            return d.toLocaleString('es-ES', {
                weekday: 'short',
                day: 'numeric',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return '';
        }
    };

    if (!isOpen) return null;

    const handleSchedule = async () => {
        if (!selectedChannel) return;
        if (actionType !== 'update_existing' && !isImmediate && !scheduledFor) return;

        setIsSubmitting(true);
        try {
            const fbAlbumIdParam = isFacebookChannel && selectedFbAlbumId !== 'auto' ? selectedFbAlbumId : undefined;

            if (isSentItem && actionType === 'update_existing') {
                const chan = channels.find(c => c.id === Number(selectedChannel));
                const platform = chan ? chan.platform : 'facebook';
                const res = await publisherApi.updatePublishedPost({
                    book_id: bookHash,
                    caption: customCaption.trim() ? customCaption.trim() : undefined,
                    template_id: selectedTemplates.length > 0 ? selectedTemplates[0] : undefined,
                    platforms: [platform]
                });

                if (res.success) {
                    setSuccessMsg('¡Publicación actualizada con éxito en ' + platform.toUpperCase() + '!');
                    setIsSuccess(true);
                    setTimeout(() => {
                        setIsSuccess(false);
                        onClose();
                    }, 1500);
                } else {
                    alert("No se pudo actualizar: " + (res.error || "Error desconocido"));
                }
            } else if (editingItem && !isSentItem) {
                const res = await updateQueueItem({
                    id: editingItem.id,
                    book_hash: bookHash,
                    channel_id: Number(selectedChannel),
                    scheduled_for: isImmediate ? new Date().toISOString() : new Date(scheduledFor).toISOString(),
                    template_id: selectedTemplates.length > 0 ? selectedTemplates[0] : undefined,
                    immediate: isImmediate,
                    fb_album_id: fbAlbumIdParam,
                    status: 'pending' // Al editar, volvemos a ponerlo en pending por si estaba fallido
                });

                if (res.success) {
                    setSuccessMsg('¡Programación actualizada con éxito!');
                    setIsSuccess(true);
                    setTimeout(() => {
                        setIsSuccess(false);
                        onClose();
                    }, 1500);
                }
            } else {
                const res = await schedulePublication({
                    book_hash: bookHash,
                    channel_id: Number(selectedChannel),
                    scheduled_for: isImmediate ? new Date().toISOString() : new Date(scheduledFor).toISOString(),
                    template_ids: selectedTemplates.length > 0 ? selectedTemplates : undefined,
                    immediate: isImmediate,
                    fb_album_id: fbAlbumIdParam,
                });

                if (res.success) {
                    setSuccessMsg(isImmediate ? '¡Publicado con éxito!' : '¡Programado con éxito!');
                    setIsSuccess(true);
                    setTimeout(() => {
                        setIsSuccess(false);
                        onClose();
                    }, 1500);
                }
            }
        } catch (err) {
            console.error("Error processing publication:", err);
            alert("Error al procesar: " + (err as Error).message);
        } finally {
            setIsSubmitting(false);
        }
    };



    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center px-4 sm:px-0 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
            <div
                className="w-full max-w-lg glass-panel rounded-premium overflow-hidden border border-white/10 shadow-2xl animate-in zoom-in-95 duration-300"
                style={{
                    background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                    backdropFilter: `blur(${settings.glassBlur}px)`
                }}
            >
                {/* Header */}
                <div className="p-6 border-b border-white/5 flex justify-between items-center bg-gradient-to-r from-primary/10 to-transparent">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-primary/20 rounded-xl text-primary">
                            {isSentItem && actionType === 'update_existing' ? <Edit3 className="w-5 h-5" /> : <Send className="w-5 h-5" />}
                        </div>
                        <div>
                            <h2 className="text-sm font-black uppercase tracking-widest">
                                {isSentItem && actionType === 'update_existing'
                                    ? 'Editar Publicación Enviada'
                                    : editingItem
                                        ? 'Editar Programación'
                                        : 'Programar Publicación'}
                            </h2>
                            <p className="text-[10px] text-gray-400 font-bold uppercase truncate max-w-[200px]">{bookTitle}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                        <X className="w-5 h-5 text-gray-400" />
                    </button>
                </div>

                {isSuccess ? (
                    <div className="p-12 flex flex-col items-center justify-center gap-4 animate-in zoom-in-90 duration-300">
                        <div className="p-4 bg-green-500/20 rounded-full text-green-500">
                            <CheckCircle className="w-12 h-12" />
                        </div>
                        <p className="text-sm font-black uppercase tracking-widest text-green-500 text-center">{successMsg}</p>
                    </div>
                ) : (
                    <div className="p-6 flex flex-col gap-5">
                        {/* Selector de Acción cuando el item ya fue enviado */}
                        {isSentItem && (
                            <div className="flex rounded-xl p-1 bg-black/40 border border-white/10 gap-1">
                                <button
                                    type="button"
                                    onClick={() => setActionType('update_existing')}
                                    className={`flex-1 py-2.5 px-3 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                                        actionType === 'update_existing'
                                            ? 'bg-primary text-white shadow-lg'
                                            : 'text-gray-400 hover:text-white'
                                    }`}
                                >
                                    <Edit3 className="w-3.5 h-3.5" />
                                    Editar Post Existente
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setActionType('create_new')}
                                    className={`flex-1 py-2.5 px-3 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                                        actionType === 'create_new'
                                            ? 'bg-primary text-white shadow-lg'
                                            : 'text-gray-400 hover:text-white'
                                    }`}
                                >
                                    <Send className="w-3.5 h-3.5" />
                                    Publicar de Nuevo
                                </button>
                            </div>
                        )}

                        {isSentItem && actionType === 'update_existing' && (
                            <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-start gap-2.5 text-blue-300 text-[11px] leading-relaxed">
                                <Sparkles className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                                <span>
                                    Esta acción actualizará el texto de la publicación en Facebook directamente con la plantilla seleccionada o los datos actualizados del libro <strong>sin duplicar fotos</strong>.
                                </span>
                            </div>
                        )}

                        {/* Book Hash (Editable) */}
                        <div className="flex flex-col gap-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-primary/80 flex items-center gap-2">
                                <Hash className="w-3 h-3" /> Hash del Libro
                            </label>
                            <input
                                type="text"
                                value={bookHash}
                                onChange={(e) => setBookHash(e.target.value)}
                                placeholder="Hash del libro..."
                                className="w-full p-3 glass-panel rounded-premium-sm border border-white/10 text-xs bg-black/20 text-white focus:outline-none focus:border-primary/50 transition-colors"
                            />
                        </div>

                        {/* Canal */}
                        <div className="flex flex-col gap-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-primary/80">Canal de Destino</label>
                            <div className="grid grid-cols-1 gap-2">
                                {channels.length === 0 ? (
                                    <p className="text-[10px] text-gray-500 italic">No hay canales activos definidos.</p>
                                ) : (
                                    <select
                                        value={selectedChannel}
                                        onChange={(e) => setSelectedChannel(e.target.value ? Number(e.target.value) : '')}
                                        className="w-full p-3 glass-panel rounded-premium-sm border border-white/10 text-xs bg-black/20 text-white focus:outline-none focus:border-primary/50 transition-colors"
                                    >
                                        <option value="" className="bg-gray-900">Seleccionar canal...</option>
                                        {channels.map(c => (
                                            <option key={c.id} value={c.id} className="bg-gray-900">
                                                {c.platform.toUpperCase()} - {c.name}
                                            </option>
                                        ))}
                                    </select>
                                )}
                            </div>
                        </div>

                        {/* Detector y Selector de Álbum en Facebook */}
                        {isFacebookChannel && (
                            <div className="flex flex-col gap-2.5 p-3 rounded-xl bg-white/[0.03] border border-white/10 animate-in fade-in duration-300">
                                {albumCheck?.loading ? (
                                    <div className="p-2.5 rounded-lg bg-white/5 border border-white/10 flex items-center gap-2 text-xs text-gray-400">
                                        <RefreshCw className="w-3.5 h-3.5 animate-spin text-primary shrink-0" />
                                        <span>Consultando álbumes de la página de Facebook...</span>
                                    </div>
                                ) : albumCheck?.exists ? (
                                    <div className="p-3 rounded-xl bg-green-500/10 border border-green-500/25 flex items-center justify-between gap-2 text-green-300">
                                        <div className="flex items-center gap-2 min-w-0">
                                            <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />
                                            <div className="min-w-0">
                                                <p className="text-[10px] font-black uppercase tracking-wider text-green-400">Álbum Detectado para la Serie</p>
                                                <p className="text-xs text-white font-bold truncate">"{albumCheck.album_name}"</p>
                                            </div>
                                        </div>
                                        <span className="text-[9px] px-2 py-0.5 rounded-full bg-green-500/20 text-green-300 border border-green-500/30 shrink-0 font-bold">
                                            Auto-detectado
                                        </span>
                                    </div>
                                ) : albumCheck && !albumCheck.loading && !albumCheck.exists ? (
                                    <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 flex flex-col gap-2 text-amber-200">
                                        <div className="flex items-start gap-2">
                                            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                                            <div className="flex flex-col gap-0.5 w-full">
                                                <p className="text-[10px] font-black uppercase tracking-wider text-amber-400">
                                                    Álbum no encontrado para esta serie
                                                </p>
                                                <p className="text-[11px] text-amber-200/90 leading-relaxed">
                                                    Para crear el álbum en Facebook, usa este <strong>nombre exacto</strong>:
                                                </p>
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between gap-2 p-2 bg-black/40 rounded-lg border border-amber-500/20">
                                            <span className="text-xs font-black text-white px-1 select-all truncate">
                                                {albumCheck.recommended_name || bookTitle}
                                            </span>
                                            <button
                                                type="button"
                                                onClick={() => copyToClipboard(albumCheck.recommended_name || bookTitle)}
                                                className="px-2.5 py-1 text-[10px] font-black uppercase tracking-wider bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 rounded-md border border-amber-500/30 flex items-center gap-1 transition-all cursor-pointer shrink-0"
                                            >
                                                {copiedAlbumName ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                                                {copiedAlbumName ? '¡Copiado!' : 'Copiar'}
                                            </button>
                                        </div>
                                    </div>
                                ) : null}

                                {/* Desplegable para seleccionar álbum de la lista */}
                                <div className="flex flex-col gap-1.5 mt-0.5">
                                    <label className="text-[10px] font-black uppercase tracking-widest text-primary/80 flex items-center justify-between">
                                        <span>📂 Asignar a Álbum de Facebook</span>
                                        {selectedFbAlbumId !== 'auto' && (
                                            <button
                                                type="button"
                                                onClick={() => setSelectedFbAlbumId('auto')}
                                                className="text-[9px] text-primary hover:underline cursor-pointer"
                                            >
                                                Restablecer a automático
                                            </button>
                                        )}
                                    </label>
                                    <select
                                        value={selectedFbAlbumId}
                                        onChange={(e) => setSelectedFbAlbumId(e.target.value)}
                                        className="w-full p-2.5 glass-panel rounded-premium-sm border border-white/10 text-xs bg-black/30 text-white focus:outline-none focus:border-primary/50 transition-colors"
                                    >
                                        <option value="auto" className="bg-gray-900 text-white">
                                            ✨ Detección automática {albumCheck?.exists ? `(Usar "${albumCheck.album_name}")` : '(Buscar por nombre de serie)'}
                                        </option>
                                        <option value="wall" className="bg-gray-900 text-amber-300 font-semibold">
                                            🚫 Muro Principal (No publicar en ningún álbum)
                                        </option>
                                        {albumCheck?.available_albums && albumCheck.available_albums.length > 0 && (
                                            <optgroup label="── Álbumes creados en tu Página de Facebook ──" className="bg-gray-900 text-primary font-bold">
                                                {albumCheck.available_albums.map((alb: any) => (
                                                    <option key={alb.id} value={alb.id} className="bg-gray-900 text-white font-normal">
                                                        📁 {alb.name}
                                                    </option>
                                                ))}
                                            </optgroup>
                                        )}
                                    </select>
                                    {selectedFbAlbumId !== 'auto' && selectedFbAlbumId !== 'wall' && (
                                        <div className="flex items-center gap-1.5 text-[10px] text-green-300/90 font-medium px-1">
                                            <CheckCircle className="w-3 h-3 text-green-400 shrink-0" />
                                            <span>Asignado expresamente al álbum: <strong>{albumCheck?.available_albums?.find((a: any) => a.id === selectedFbAlbumId)?.name || selectedFbAlbumId}</strong></span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Plantilla (Multi-select) */}
                        <div className="flex flex-col gap-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-primary/80 flex items-center justify-between">
                                <span>Plantilla(s) de Texto</span>
                                {!editingItem && <span className="text-[8px] text-gray-500">Secuencial</span>}
                            </label>
                            <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto w-full p-2 glass-panel rounded-premium-sm border border-white/10 bg-black/20 custom-scrollbar">
                                <div
                                    className={`flex items-center gap-2 p-2.5 rounded-lg cursor-pointer transition-all ${selectedTemplates.length === 0 ? 'bg-primary/20 text-primary border border-primary/30' : 'text-white/60 hover:bg-white/5 border border-transparent'}`}
                                    onClick={() => setSelectedTemplates([])}
                                >
                                    <div className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center transition-all ${selectedTemplates.length === 0 ? 'bg-primary border-primary' : 'border-white/20'}`}>
                                        {selectedTemplates.length === 0 && <div className="w-1.5 h-1.5 bg-black rounded-full" />}
                                    </div>
                                    <span className="text-xs font-semibold">Sin plantilla (Predeterminado)</span>
                                </div>
                                {templates.map(t => {
                                    const isSelected = selectedTemplates.includes(t.id);
                                    return (
                                        <div
                                            key={t.id}
                                            className={`flex items-center gap-2 p-2.5 rounded-lg cursor-pointer transition-all ${isSelected ? 'bg-primary/20 text-primary border border-primary/30' : 'text-white/60 hover:bg-white/5 border border-transparent'}`}
                                            onClick={() => {
                                                if (editingItem || actionType === 'update_existing') {
                                                    setSelectedTemplates([t.id]);
                                                } else {
                                                    if (isSelected) {
                                                        setSelectedTemplates(selectedTemplates.filter(id => id !== t.id));
                                                    } else {
                                                        setSelectedTemplates([...selectedTemplates, t.id]);
                                                    }
                                                }
                                            }}
                                        >
                                            <div className={`w-3.5 h-3.5 rounded border transition-all ${isSelected ? 'bg-primary border-primary flex items-center justify-center' : 'border-white/20'}`}>
                                                {isSelected && <CheckCircle className="w-2.5 h-2.5 text-black" />}
                                            </div>
                                            <span className="text-xs">{t.name} {isSelected && !editingItem && <span className="ml-1 text-[10px] px-1.5 py-0.5 bg-primary/30 rounded-full text-primary-light">#{selectedTemplates.indexOf(t.id) + 1}</span>}</span>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>

                        {/* Texto Personalizado Opcional para Edición */}
                        {isSentItem && actionType === 'update_existing' && (
                            <div className="flex flex-col gap-2">
                                <label className="text-[10px] font-black uppercase tracking-widest text-primary/80 flex items-center justify-between">
                                    <span>Texto Personalizado (Opcional)</span>
                                    <span className="text-[8px] text-gray-400">Si lo dejas vacío, usa la plantilla</span>
                                </label>
                                <textarea
                                    rows={4}
                                    value={customCaption}
                                    onChange={(e) => setCustomCaption(e.target.value)}
                                    placeholder="Escribe un texto específico si deseas sobrescribir la plantilla..."
                                    className="w-full p-3 glass-panel rounded-premium-sm border border-white/10 text-xs bg-black/20 text-white focus:outline-none focus:border-primary/50 transition-colors resize-y custom-scrollbar"
                                />
                            </div>
                        )}

                        {/* Opciones de Publicación Programada / Inmediata (Solo cuando no es actualización directa en vivo) */}
                        {(!isSentItem || actionType === 'create_new') && (
                            <>
                                <div className="flex items-center gap-2 p-3 glass-panel rounded-premium-sm border border-white/5 bg-white/2 cursor-pointer transition-all hover:bg-white/5" onClick={() => setIsImmediate(!isImmediate)}>
                                    <div className={`w-4 h-4 rounded border flex items-center justify-center transition-all ${isImmediate ? 'bg-primary border-primary' : 'border-white/20'}`}>
                                        {isImmediate && <CheckCircle className="w-3 h-3 text-white" />}
                                    </div>
                                    <span className="text-[10px] font-black uppercase tracking-widest text-white/80">Publicar inmediatamente</span>
                                </div>

                                {!isImmediate && (
                                    <div className="flex flex-col gap-3 animate-in slide-in-from-top-2 duration-300">
                                        <div className="flex items-center justify-between">
                                            <label className="text-[10px] font-black uppercase tracking-widest text-primary/80">
                                                Fecha y Hora de Publicación
                                            </label>
                                            <span className="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">
                                                {getFormattedPreview()}
                                            </span>
                                        </div>

                                        {/* Presets Rápidos */}
                                        <div className="flex flex-wrap gap-1.5">
                                            <button
                                                type="button"
                                                onClick={() => applyPreset(10)}
                                                className="px-2.5 py-1 text-[10px] font-bold rounded-lg glass-panel bg-white/5 hover:bg-primary/20 hover:text-primary text-white/80 transition-all border border-white/5"
                                            >
                                                +10m
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => applyPreset(30)}
                                                className="px-2.5 py-1 text-[10px] font-bold rounded-lg glass-panel bg-white/5 hover:bg-primary/20 hover:text-primary text-white/80 transition-all border border-white/5"
                                            >
                                                +30m
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => applyPreset(60)}
                                                className="px-2.5 py-1 text-[10px] font-bold rounded-lg glass-panel bg-white/5 hover:bg-primary/20 hover:text-primary text-white/80 transition-all border border-white/5"
                                            >
                                                +1h
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => applyPreset(180)}
                                                className="px-2.5 py-1 text-[10px] font-bold rounded-lg glass-panel bg-white/5 hover:bg-primary/20 hover:text-primary text-white/80 transition-all border border-white/5"
                                            >
                                                +3h
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => applyPreset(1, 9)}
                                                className="px-2.5 py-1 text-[10px] font-bold rounded-lg glass-panel bg-white/5 hover:bg-primary/20 hover:text-primary text-white/80 transition-all border border-white/5"
                                            >
                                                Mañana 9:00 AM
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => applyPreset(1, 18)}
                                                className="px-2.5 py-1 text-[10px] font-bold rounded-lg glass-panel bg-white/5 hover:bg-primary/20 hover:text-primary text-white/80 transition-all border border-white/5"
                                            >
                                                Mañana 6:00 PM
                                            </button>
                                        </div>

                                        {/* Grid de Fecha, Hora y Minutos */}
                                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                                            {/* Campo Fecha */}
                                            <div className="sm:col-span-1 flex flex-col gap-1">
                                                <span className="text-[9px] uppercase font-bold text-gray-400 flex items-center gap-1">
                                                    <Calendar className="w-2.5 h-2.5" /> Fecha
                                                </span>
                                                <input
                                                    type="date"
                                                    value={datePart}
                                                    onChange={(e) => updateDateTime(e.target.value, hourPart, minutePart)}
                                                    className="w-full p-2.5 glass-panel rounded-premium-sm border border-white/10 text-xs bg-black/20 text-white focus:outline-none focus:border-primary/50 transition-colors [color-scheme:dark]"
                                                />
                                            </div>

                                            {/* Selector Hora */}
                                            <div className="flex flex-col gap-1">
                                                <span className="text-[9px] uppercase font-bold text-gray-400 flex items-center gap-1">
                                                    <Clock className="w-2.5 h-2.5" /> Hora
                                                </span>
                                                <select
                                                    value={hourPart}
                                                    onChange={(e) => updateDateTime(datePart, e.target.value, minutePart)}
                                                    className="w-full p-2.5 glass-panel rounded-premium-sm border border-white/10 text-xs bg-black/20 text-white focus:outline-none focus:border-primary/50 transition-colors cursor-pointer"
                                                >
                                                    {HOURS.map((h) => {
                                                        const hNum = parseInt(h, 10);
                                                        const ampm = hNum >= 12 ? 'PM' : 'AM';
                                                        const displayHour = hNum % 12 === 0 ? 12 : hNum % 12;
                                                        return (
                                                            <option key={h} value={h} className="bg-gray-900 text-white">
                                                                {h}:00 ({displayHour} {ampm})
                                                            </option>
                                                        );
                                                    })}
                                                </select>
                                            </div>

                                            {/* Selector Minutos */}
                                            <div className="flex flex-col gap-1">
                                                <span className="text-[9px] uppercase font-bold text-gray-400 flex items-center gap-1">
                                                    <Clock className="w-2.5 h-2.5 text-gray-500" /> Minutos
                                                </span>
                                                <select
                                                    value={minutePart}
                                                    onChange={(e) => updateDateTime(datePart, hourPart, e.target.value)}
                                                    className="w-full p-2.5 glass-panel rounded-premium-sm border border-white/10 text-xs bg-black/20 text-white focus:outline-none focus:border-primary/50 transition-colors cursor-pointer"
                                                >
                                                    {MINUTES.map((m) => (
                                                        <option key={m} value={m} className="bg-gray-900 text-white">
                                                            :{m}
                                                        </option>
                                                    ))}
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}

                        {/* Actions */}
                        <div className="flex gap-3 pt-2">
                            <button
                                onClick={onClose}
                                className="flex-1 p-3 glass-panel rounded-premium-sm text-[10px] font-black uppercase tracking-widest border border-white/5 hover:bg-white/5 transition-all cursor-pointer"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleSchedule}
                                disabled={isSubmitting || !selectedChannel || (actionType !== 'update_existing' && !isImmediate && !scheduledFor)}
                                className={`flex-[2] p-3 text-white rounded-premium-sm text-[10px] font-black uppercase tracking-widest shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer ${
                                    isSentItem && actionType === 'update_existing'
                                        ? 'bg-blue-600 shadow-blue-600/20 hover:bg-blue-500'
                                        : isImmediate
                                            ? 'bg-green-600 shadow-green-600/20 hover:bg-green-500'
                                            : 'bg-primary shadow-primary/20 hover:opacity-90'
                                } disabled:opacity-50 disabled:grayscale`}
                            >
                                {isSubmitting ? (
                                    <Clock className="w-3.5 h-3.5 animate-spin" />
                                ) : isSentItem && actionType === 'update_existing' ? (
                                    <Edit3 className="w-3.5 h-3.5" />
                                ) : (
                                    <Send className="w-3.5 h-3.5" />
                                )}
                                {isSubmitting
                                    ? (isSentItem && actionType === 'update_existing' ? 'Actualizando Post...' : isImmediate ? 'Publicando...' : 'Programando...')
                                    : (isSentItem && actionType === 'update_existing' ? 'Actualizar Post en Facebook' : isImmediate ? 'Publicar Ahora' : 'Programar Ahora')}
                            </button>
                        </div>

                    </div>
                )}
            </div>
        </div>
    );
};
