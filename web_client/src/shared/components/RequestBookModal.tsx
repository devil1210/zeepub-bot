import React, { useState } from 'react';
import {
    Zap,
    Send,
    Sparkles,
    X,
    Star,
    CheckCircle2,
    Loader2,
    Check
} from 'lucide-react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { api } from '../services/api';

interface RequestBookModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const RequestBookModal: React.FC<RequestBookModalProps> = ({ isOpen, onClose }) => {
    const { settings } = useTheme();
    const [title, setTitle] = useState('');
    const [author, setAuthor] = useState('');
    const [isbn, setIsbn] = useState('');
    const [priority, setPriority] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (isSubmitting) return;

        setIsSubmitting(true);
        try {
            const notes = `ISBN: ${isbn}. Priority: ${priority ? 'High' : 'Normal'}`;
            await api.requestBook(title, author, notes);

            setIsSuccess(true);
            setTimeout(() => {
                onClose();
                setIsSuccess(false);
                setTitle('');
                setAuthor('');
                setIsbn('');
                setPriority(false);
            }, 1500);
        } catch (error) {
            console.error('Error requesting book:', error);
            setIsSubmitting(false);
            // Could show error state here
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            <div
                className="glass-panel w-full max-w-2xl rounded-premium overflow-hidden border border-white/10 shadow-2xl relative animate-in zoom-in-95 duration-200 max-h-[90vh] flex flex-col"
                style={{
                    background: `rgba(var(--glass-rgb), ${settings.glassOpacity})`,
                    backdropFilter: `blur(${settings.glassBlur}px)`,
                }}
            >
                {/* Header */}
                <div className="p-6 border-b border-white/5 flex items-center justify-between shrink-0">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-premium-sm bg-primary/20 flex items-center justify-center border border-primary/20">
                            <Sparkles className="text-primary w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white leading-tight">Solicitar un Libro</h2>
                            <p className="text-xs text-gray-400">¿No encuentras lo que buscas?</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-white/5 rounded-full text-gray-400 hover:text-white transition-colors"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Scrollable Content */}
                <div className="overflow-y-auto p-6 space-y-8 flex-1 custom-scrollbar">
                    <p className="text-gray-400 text-sm leading-relaxed">
                        Envía una solicitud y nuestra comunidad ayudará a localizar el ePub por ti. Las solicitudes suelen procesarse en menos de 24h.
                    </p>

                    <form className="space-y-6" onSubmit={handleSubmit}>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="col-span-2">
                                <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-1.5 ml-1">
                                    Título del Libro <span className="text-red-500">*</span>
                                </label>
                                <input
                                    className="w-full rounded-premium-sm bg-black/40 border border-white/5 text-white focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none placeholder-gray-600 py-3 px-4 transition-all text-sm"
                                    placeholder="ej. Project Hail Mary"
                                    required
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                />
                            </div>
                            <div className="col-span-2 md:col-span-1">
                                <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-1.5 ml-1">
                                    Nombre del Autor <span className="text-red-500">*</span>
                                </label>
                                <input
                                    className="w-full rounded-premium-sm bg-black/40 border border-white/5 text-white focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none placeholder-gray-600 py-3 px-4 transition-all text-sm"
                                    placeholder="ej. Andy Weir"
                                    required
                                    type="text"
                                    value={author}
                                    onChange={(e) => setAuthor(e.target.value)}
                                />
                            </div>
                            <div className="col-span-2 md:col-span-1">
                                <label className="block text-[10px] font-black text-gray-500 uppercase tracking-widest mb-1.5 ml-1">
                                    ISBN (Opcional)
                                </label>
                                <input
                                    className="w-full rounded-premium-sm bg-black/40 border border-white/5 text-white focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none placeholder-gray-600 py-3 px-4 transition-all text-sm"
                                    placeholder="ej. 978-0593135204"
                                    type="text"
                                    value={isbn}
                                    onChange={(e) => setIsbn(e.target.value)}
                                />
                            </div>
                        </div>

                        <div
                            className={`bg-white/5 rounded-premium-sm p-4 border flex items-center justify-between group cursor-pointer transition-colors ${priority ? 'border-primary/50 bg-primary/5' : 'border-white/5 hover:border-primary/50'}`}
                            onClick={() => setPriority(!priority)}
                        >
                            <div className="flex items-start gap-3">
                                <div className={`p-2 rounded-premium-sm text-primary border transition-colors ${priority ? 'bg-primary/20 border-primary/20' : 'bg-primary/10 border-primary/10'}`}>
                                    <Zap className="w-5 h-5" />
                                </div>
                                <div>
                                    <h3 className={`text-sm font-bold transition-colors ${priority ? 'text-primary' : 'text-white group-hover:text-primary'}`}>Solicitud Prioritaria</h3>
                                    <p className="text-[10px] text-gray-500 mt-0.5">Sube esta solicitud al principio de la cola</p>
                                </div>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer pointer-events-none">
                                <input className="sr-only peer" type="checkbox" checked={priority} readOnly />
                                <div className="w-10 h-5.5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4.5 after:w-4.5 after:transition-all peer-checked:bg-primary"></div>
                            </label>
                        </div>

                        <button
                            className={`w-full text-white font-black uppercase tracking-widest text-xs py-4 px-6 rounded-premium-sm shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed ${isSuccess
                                    ? 'bg-green-500 shadow-green-500/20'
                                    : 'bg-primary hover:bg-primary-dark shadow-primary/20'
                                }`}
                            type="submit"
                            disabled={isSubmitting || isSuccess}
                        >
                            {isSubmitting ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>Enviando...</span>
                                </>
                            ) : isSuccess ? (
                                <>
                                    <Check className="w-4 h-4" />
                                    <span>¡Enviado!</span>
                                </>
                            ) : (
                                <>
                                    <span>Enviar Solicitud</span>
                                    <Send className="w-4 h-4" />
                                </>
                            )}
                        </button>
                    </form>

                    {/* Support Info */}
                    <div className="pt-4 border-t border-white/5">
                        <div className="flex items-center gap-4 text-[10px] text-gray-500 overflow-x-auto pb-2 scrollbar-none">
                            <div className="flex items-center gap-1 shrink-0">
                                <CheckCircle2 className="w-3 h-3 text-green-400" />
                                <span>Procesado en 24h</span>
                            </div>
                            <div className="flex items-center gap-1 shrink-0">
                                <Star className="w-3 h-3 text-yellow-400" />
                                <span>Calidad Garantizada</span>
                            </div>
                            <div className="flex items-center gap-1 shrink-0">
                                <Sparkles className="w-3 h-3 text-primary" />
                                <span>Actualizaciones</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
