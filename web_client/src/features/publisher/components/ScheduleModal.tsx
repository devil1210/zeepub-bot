import React, { useState } from 'react';
import { X, Send, Calendar, Clock, CheckCircle } from 'lucide-react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { usePublisher } from '../hooks/usePublisher';

interface ScheduleModalProps {
    isOpen: boolean;
    onClose: () => void;
    bookHash: string;
    bookTitle: string;
}

export const ScheduleModal: React.FC<ScheduleModalProps> = ({
    isOpen,
    onClose,
    bookHash,
    bookTitle
}) => {
    const { settings } = useTheme();
    const { channels, templates, schedulePublication } = usePublisher();

    const [selectedChannel, setSelectedChannel] = useState<number | ''>('');
    const [selectedTemplate, setSelectedTemplate] = useState<number | ''>('');
    const [scheduledFor, setScheduledFor] = useState(() => {
        const now = new Date();
        now.setMinutes(now.getMinutes() + 10); // Default to 10 mins from now

        // Adjust to local timezone ISO string for datetime-local input
        const tzOffset = now.getTimezoneOffset() * 60000;
        const localISOTime = new Date(now.getTime() - tzOffset).toISOString().slice(0, 16);
        return localISOTime;
    });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    if (!isOpen) return null;

    const handleSchedule = async () => {
        if (!selectedChannel || !scheduledFor) return;

        setIsSubmitting(true);
        try {
            const res = await schedulePublication({
                book_hash: bookHash,
                channel_id: Number(selectedChannel),
                scheduled_for: new Date(scheduledFor).toISOString(),
                template_id: selectedTemplate === '' ? undefined : Number(selectedTemplate)
            });

            if (res.success) {
                setIsSuccess(true);
                setTimeout(() => {
                    setIsSuccess(false);
                    onClose();
                }, 1500);
            }
        } catch (err) {
            console.error("Error scheduling publication:", err);
            alert("Error al programar: " + (err as Error).message);
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

                        {/* Plantilla */}
                        <div className="flex flex-col gap-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-primary/80">Plantilla de Texto</label>
                            <select
                                value={selectedTemplate}
                                onChange={(e) => setSelectedTemplate(e.target.value ? Number(e.target.value) : '')}
                                className="w-full p-3 glass-panel rounded-premium-sm border border-white/10 text-xs bg-black/20 text-white focus:outline-none focus:border-primary/50 transition-colors"
                            >
                                <option value="" className="bg-gray-900">Sin plantilla (Usar predeterminado)</option>
                                {templates.map(t => (
                                    <option key={t.id} value={t.id} className="bg-gray-900">{t.name}</option>
                                ))}
                            </select>
                        </div>

                        {/* Fecha y Hora */}
                        <div className="flex flex-col gap-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-primary/80">Fecha y Hora</label>
                            <div className="relative">
                                <input
                                    type="datetime-local"
                                    value={scheduledFor}
                                    onChange={(e) => setScheduledFor(e.target.value)}
                                    className="w-full p-3 glass-panel rounded-premium-sm border border-white/10 text-xs bg-black/20 text-white focus:outline-none focus:border-primary/50 transition-colors"
                                />
                                <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
                            </div>
                        </div>

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
                                disabled={isSubmitting || !selectedChannel || !scheduledFor}
                                className="flex-[2] p-3 bg-primary text-white rounded-premium-sm text-[10px] font-black uppercase tracking-widest shadow-lg shadow-primary/20 hover:opacity-90 disabled:opacity-50 disabled:grayscale transition-all flex items-center justify-center gap-2"
                            >
                                {isSubmitting ? <Clock className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                                {isSubmitting ? 'Programando...' : 'Programar Ahora'}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
