import React, { useState, useEffect } from 'react';
import { X, Send, Calendar, Clock, CheckCircle, Hash } from 'lucide-react';
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

    useEffect(() => {
        if (isOpen) {
            setBookHash(editingItem?.book_hash || initialBookHash);
            const defaultChan = editingItem?.channel_id || (channels.find(c => c.is_favorite)?.id || (channels.length > 0 ? channels[0].id : ''));
            setSelectedChannel(defaultChan);
            setSelectedTemplates(editingItem?.template_id ? [editingItem.template_id] : []);
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
        if (!isImmediate && !scheduledFor) return;

        setIsSubmitting(true);
        try {
            if (editingItem) {
                const res = await updateQueueItem({
                    id: editingItem.id,
                    book_hash: bookHash,
                    channel_id: Number(selectedChannel),
                    scheduled_for: isImmediate ? new Date().toISOString() : new Date(scheduledFor).toISOString(),
                    template_id: selectedTemplates.length > 0 ? selectedTemplates[0] : undefined,
                    immediate: isImmediate,
                    status: 'pending' // Al editar, volvemos a ponerlo en pending por si estaba fallido
                });

                if (res.success) {
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
                    immediate: isImmediate
                });

                if (res.success) {
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
                            <Send className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-sm font-black uppercase tracking-widest">Programar Publicación</h2>
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
                        <p className="text-sm font-black uppercase tracking-widest text-green-500">¡Programado con éxito!</p>
                    </div>
                ) : (
                    <div className="p-6 flex flex-col gap-6">
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
                                                if (editingItem) {
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

                        {/* Opción Inmediata */}
                        <div className="flex items-center gap-2 p-3 glass-panel rounded-premium-sm border border-white/5 bg-white/2 cursor-pointer transition-all hover:bg-white/5" onClick={() => setIsImmediate(!isImmediate)}>
                            <div className={`w-4 h-4 rounded border flex items-center justify-center transition-all ${isImmediate ? 'bg-primary border-primary' : 'border-white/20'}`}>
                                {isImmediate && <CheckCircle className="w-3 h-3 text-white" />}
                            </div>
                            <span className="text-[10px] font-black uppercase tracking-widest text-white/80">Publicar inmediatamente</span>
                        </div>

                        {/* Fecha y Hora */}
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

                        {/* Actions */}
                        <div className="flex gap-3 pt-2">
                            <button
                                onClick={onClose}
                                className="flex-1 p-3 glass-panel rounded-premium-sm text-[10px] font-black uppercase tracking-widest border border-white/5 hover:bg-white/5 transition-all"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleSchedule}
                                disabled={isSubmitting || !selectedChannel || (!isImmediate && !scheduledFor)}
                                className={`flex-[2] p-3 text-white rounded-premium-sm text-[10px] font-black uppercase tracking-widest shadow-lg transition-all flex items-center justify-center gap-2 ${isImmediate
                                    ? 'bg-green-600 shadow-green-600/20 hover:bg-green-500'
                                    : 'bg-primary shadow-primary/20 hover:opacity-90'
                                    } disabled:opacity-50 disabled:grayscale`}
                            >
                                {isSubmitting ? <Clock className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                                {isSubmitting ? (isImmediate ? 'Publicando...' : 'Programando...') : (isImmediate ? 'Publicar Ahora' : 'Programar Ahora')}
                            </button>
                        </div>

                    </div>
                )}
            </div>
        </div>
    );
};
