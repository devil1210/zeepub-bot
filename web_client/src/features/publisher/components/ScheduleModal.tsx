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
            setSelectedChannel(editingItem?.channel_id || '');
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
    }, [isOpen, editingItem, initialBookHash]);

    const [isImmediate, setIsImmediate] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

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
                        <div className="flex items-center justify-center w-10 h-10 rounded-premium-sm bg-primary/20 text-primary border border-primary/20">
                            <Send className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-sm font-black uppercase tracking-widest text-white">Programar Publicación</h2>
                            <p className="text-[10px] text-gray-500 font-bold uppercase truncate max-w-[200px] mt-1">{bookTitle}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors group">
                        <X className="w-5 h-5 text-gray-400 group-hover:text-white" />
                    </button>
                </div>

                {isSuccess ? (
                    <div className="p-12 flex flex-col items-center justify-center gap-4 animate-in zoom-in-90 duration-300">
                        <div className="p-4 bg-green-500/20 rounded-full text-green-500 shadow-lg shadow-green-500/10 border border-green-500/20">
                            <CheckCircle className="w-12 h-12" />
                        </div>
                        <p className="text-xs font-black uppercase tracking-widest text-green-500">¡Programado con éxito!</p>
                    </div>
                ) : (
                    <div className="p-6 flex flex-col gap-6">
                        {/* Book Hash (Editable) */}
                        <div className="flex flex-col gap-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-primary/80 flex items-center gap-2 ml-1">
                                <Hash className="w-3 h-3" /> Hash del Libro
                            </label>
                            <input
                                type="text"
                                value={bookHash}
                                onChange={(e) => setBookHash(e.target.value)}
                                placeholder="Hash del libro..."
                                className="w-full p-3 bg-black/20 border border-white/10 rounded-premium-sm text-xs text-white focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all placeholder:text-gray-600"
                            />
                        </div>

                        {/* Canal */}
                        <div className="flex flex-col gap-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-primary/80 ml-1">Canal de Destino</label>
                            <div className="grid grid-cols-1 gap-2">
                                {channels.length === 0 ? (
                                    <p className="text-[10px] text-gray-500 italic ml-1">No hay canales activos definidos.</p>
                                ) : (
                                    <select
                                        value={selectedChannel}
                                        onChange={(e) => setSelectedChannel(e.target.value ? Number(e.target.value) : '')}
                                        className="w-full p-3 bg-black/20 border border-white/10 rounded-premium-sm text-xs text-white focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all cursor-pointer"
                                    >
                                        <option value="" className="bg-[#1a1a1e]">Seleccionar canal...</option>
                                        {channels.map(c => (
                                            <option key={c.id} value={c.id} className="bg-[#1a1a1e]">
                                                {c.platform.toUpperCase()} - {c.name}
                                            </option>
                                        ))}
                                    </select>
                                )}
                            </div>
                        </div>

                        {/* Plantilla (Multi-select) */}
                        <div className="flex flex-col gap-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-primary/80 flex items-center justify-between ml-1">
                                <span>Plantilla(s) de Texto</span>
                                {!editingItem && <span className="text-[8px] text-gray-500 font-bold uppercase tracking-tighter">Secuencial</span>}
                            </label>
                            <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto w-full p-2 bg-black/20 border border-white/10 rounded-premium-sm custom-scrollbar">
                                <div
                                    className={`flex items-center gap-2 p-2.5 rounded-lg cursor-pointer transition-all ${selectedTemplates.length === 0 ? 'bg-primary/20 text-primary border border-primary/30' : 'text-white/40 hover:bg-white/5 border border-transparent'}`}
                                    onClick={() => setSelectedTemplates([])}
                                >
                                    <div className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center transition-all ${selectedTemplates.length === 0 ? 'bg-primary border-primary' : 'border-white/20'}`}>
                                        {selectedTemplates.length === 0 && <div className="w-1.5 h-1.5 bg-black rounded-full" />}
                                    </div>
                                    <span className="text-xs font-semibold">Sin plantilla</span>
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
                                            <span className="text-xs">{t.name} {isSelected && !editingItem && <span className="ml-1 text-[9px] px-1.5 py-0.5 bg-primary/30 rounded-full text-primary-light font-bold">#{selectedTemplates.indexOf(t.id) + 1}</span>}</span>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>

                        {/* Opción Inmediata */}
                        <div className="flex items-center gap-2 p-3 bg-white/5 border border-white/10 rounded-premium-sm cursor-pointer transition-all hover:bg-white/10 active:scale-[0.98]" onClick={() => setIsImmediate(!isImmediate)}>
                            <div className={`w-4 h-4 rounded border flex items-center justify-center transition-all ${isImmediate ? 'bg-primary border-primary shadow-lg shadow-primary/20' : 'border-white/20'}`}>
                                {isImmediate && <CheckCircle className="w-3 h-3 text-white" />}
                            </div>
                            <span className="text-[10px] font-black uppercase tracking-widest text-white/90">Publicar inmediatamente</span>
                        </div>

                        {/* Fecha y Hora */}
                        {!isImmediate && (
                            <div className="flex flex-col gap-2 animate-in slide-in-from-top-2 duration-300">
                                <label className="text-[10px] font-black uppercase tracking-widest text-primary/80 ml-1">Fecha y Hora</label>
                                <div className="relative">
                                    <input
                                        type="datetime-local"
                                        value={scheduledFor}
                                        onChange={(e) => setScheduledFor(e.target.value)}
                                        className="w-full p-3 bg-black/20 border border-white/10 rounded-premium-sm text-xs text-white focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all cursor-pointer"
                                    />
                                    <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
                                </div>
                            </div>
                        )}

                        {/* Actions */}
                        <div className="flex gap-3 pt-2">
                            <button
                                onClick={onClose}
                                className="flex-1 p-3 bg-black/20 border border-white/5 rounded-premium-sm text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-white hover:bg-white/5 transition-all"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleSchedule}
                                disabled={isSubmitting || !selectedChannel || (!isImmediate && !scheduledFor)}
                                className={`flex-[2] p-3 text-white rounded-premium-sm text-[10px] font-black uppercase tracking-widest shadow-lg transition-all flex items-center justify-center gap-2 transform active:scale-95 ${isImmediate
                                    ? 'bg-green-600 shadow-green-600/20 hover:bg-green-500'
                                    : 'bg-primary shadow-primary/20 hover:brightness-110'
                                    } disabled:opacity-50 disabled:grayscale disabled:scale-100`}
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
