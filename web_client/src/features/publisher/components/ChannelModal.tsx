import React, { useState, useEffect } from 'react';
import { X, Send, Facebook, Loader2, Check, Save, Hash, Settings } from 'lucide-react';
import { PublicationChannel } from '../services/publisherApi';

interface ChannelModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (channel: Partial<PublicationChannel>) => Promise<any>;
    editingChannel?: PublicationChannel | null;
}

export const ChannelModal: React.FC<ChannelModalProps> = ({ isOpen, onClose, onSave, editingChannel }) => {
    const [name, setName] = useState('');
    const [platform, setPlatform] = useState('telegram');
    const [targetId, setTargetId] = useState('');
    const [threadId, setThreadId] = useState('');
    const [isActive, setIsActive] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    useEffect(() => {
        if (editingChannel) {
            setName(editingChannel.name);
            setPlatform(editingChannel.platform);
            setTargetId(editingChannel.target_id);
            setThreadId(editingChannel.config?.message_thread_id || '');
            setIsActive(editingChannel.is_active);
        } else {
            setName('');
            setPlatform('telegram');
            setTargetId('');
            setThreadId('');
            setIsActive(true);
        }
    }, [editingChannel, isOpen]);

    if (!isOpen) return null;

    const handleSubmit = async () => {
        if (!name || !targetId || isSubmitting) return;

        setIsSubmitting(true);
        try {
            const channelData: Partial<PublicationChannel> = {
                id: editingChannel?.id,
                name,
                platform,
                target_id: targetId,
                is_active: isActive,
                config: {
                    ...editingChannel?.config,
                    message_thread_id: threadId && !isNaN(parseInt(threadId)) ? parseInt(threadId) : null
                }
            };

            await onSave(channelData);

            setIsSuccess(true);
            setTimeout(() => {
                onClose();
                setIsSuccess(false);
            }, 1000);
        } catch (error) {
            console.error('Error saving channel:', error);
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[60] overflow-y-auto" role="dialog" aria-modal="true">
            <div className="fixed inset-0 bg-black/70 backdrop-blur-md transition-opacity" onClick={onClose}></div>
            <div className="flex min-h-full items-center justify-center p-4 text-center sm:p-6">
                <div className="relative transform overflow-hidden rounded-premium bg-[#1a1a1e] text-left shadow-2xl transition-all w-full max-w-lg border border-white/10 animate-in fade-in zoom-in-95 duration-200">
                    {/* Header */}
                    <div className="relative px-6 py-5 border-b border-white/5 flex justify-between items-center bg-gradient-to-b from-white/5 to-transparent">
                        <div className="flex items-center gap-3">
                            <div className="flex items-center justify-center w-10 h-10 rounded-premium-sm bg-primary/20 text-primary">
                                <Settings className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="text-lg font-black uppercase tracking-widest text-white leading-none">
                                    {editingChannel ? 'Editar Canal' : 'Nuevo Canal'}
                                </h3>
                                <p className="text-[10px] font-bold text-gray-500 mt-1 uppercase tracking-tight">Configura el destino de tus publicaciones</p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-white transition-colors p-2 rounded-full hover:bg-white/10"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Body */}
                    <div className="px-6 py-6 space-y-5">
                        <div className="space-y-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Nombre del Canal</label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Ej: Canal de Avisos"
                                className="w-full bg-black/20 border border-white/10 rounded-premium-sm px-4 py-2.5 text-sm text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Plataforma</label>
                                <div className="flex gap-2">
                                    {(['telegram', 'facebook'] as const).map((p) => (
                                        <button
                                            key={p}
                                            type="button"
                                            onClick={() => setPlatform(p)}
                                            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all border ${platform === p
                                                ? 'bg-primary/20 border-primary text-primary shadow-lg shadow-primary/10'
                                                : 'bg-black/20 border-white/5 text-gray-400 hover:text-gray-200'
                                                }`}
                                        >
                                            {p === 'telegram' ? <Send className="w-3.5 h-3.5" /> : <Facebook className="w-3.5 h-3.5" />}
                                            {p}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">Estado</label>
                                <button
                                    onClick={() => setIsActive(!isActive)}
                                    className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all border ${isActive
                                        ? 'bg-green-500/10 border-green-500/30 text-green-400'
                                        : 'bg-red-500/10 border-red-500/30 text-red-400'
                                        }`}
                                >
                                    {isActive ? 'Activo' : 'Inactivo'}
                                </button>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1">
                                {platform === 'telegram' ? 'Chat ID / @Username' : 'ID de Grupo de Facebook'}
                            </label>
                            <input
                                type="text"
                                value={targetId}
                                onChange={(e) => setTargetId(e.target.value)}
                                placeholder={platform === 'telegram' ? "-100..." : "87290..."}
                                className="w-full bg-black/20 border border-white/10 rounded-premium-sm px-4 py-2.5 text-sm text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                            />
                        </div>

                        {platform === 'telegram' && (
                            <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
                                <label className="text-[10px] font-black uppercase tracking-widest text-gray-500 ml-1 flex items-center gap-1.5">
                                    <Hash className="w-3 h-3 text-primary" /> Topic / Thread ID (Opcional)
                                </label>
                                <input
                                    type="text"
                                    value={threadId}
                                    onChange={(e) => setThreadId(e.target.value)}
                                    placeholder="Ej: 87290"
                                    className="w-full bg-black/20 border border-white/10 rounded-premium-sm px-4 py-2.5 text-sm text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                                />
                                <p className="text-[9px] text-gray-600 ml-1">Para publicar en un tópico específico de un supergrupo.</p>
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="bg-black/20 px-6 py-4 flex flex-row-reverse gap-3 border-t border-white/5">
                        <button
                            className={`inline-flex items-center gap-2 rounded-premium-sm px-8 py-2.5 text-xs font-black uppercase tracking-widest text-white shadow-lg transition-all transform active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed ${isSuccess
                                ? 'bg-green-500 shadow-green-500/20'
                                : 'bg-primary shadow-primary/20 hover:brightness-110'
                                }`}
                            onClick={handleSubmit}
                            disabled={isSubmitting || isSuccess || !name || !targetId}
                        >
                            {isSubmitting ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Guardando...
                                </>
                            ) : isSuccess ? (
                                <>
                                    <Check className="w-4 h-4" />
                                    ¡Listo!
                                </>
                            ) : (
                                <>
                                    <Save className="w-4 h-4" />
                                    {editingChannel ? 'Actualizar' : 'Vincular Canal'}
                                </>
                            )}
                        </button>
                        <button
                            onClick={onClose}
                            disabled={isSubmitting}
                            className="px-6 py-2.5 text-xs font-black uppercase tracking-widest text-gray-400 hover:text-white transition-colors"
                        >
                            Cancelar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
