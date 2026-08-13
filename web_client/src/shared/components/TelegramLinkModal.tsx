import React, { useState } from 'react';
import { Send, CheckCircle2, AlertCircle, Loader2, Sparkles, X } from 'lucide-react';
import { api } from '@shared/services/api';

interface TelegramLinkModalProps {
    isOpen: boolean;
    email?: string;
    onClose: () => void;
    onSuccess: () => void;
}

export const TelegramLinkModal: React.FC<TelegramLinkModalProps> = ({
    isOpen,
    email,
    onClose,
    onSuccess
}) => {
    const [telegramInput, setTelegramInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!telegramInput.trim()) {
            setError('Ingresa tu @usuario o ID numérico de Telegram.');
            return;
        }

        try {
            setLoading(true);
            setError(null);
            const res = await api.linkTelegram(telegramInput.trim());

            if (res.success || res.telegram_id) {
                setSuccessMessage('¡Cuenta de Telegram vinculada con éxito!');
                setTimeout(() => {
                    onSuccess();
                    onClose();
                }, 1000);
            } else {
                setError(res.error || res.message || 'No se pudo vincular la cuenta. Verifica tus datos.');
            }
        } catch (err: any) {
            setError(err.message || 'Error de conexión al vincular la cuenta.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
            <div className="relative w-full max-w-md p-6 overflow-hidden border border-white/10 rounded-2xl bg-slate-900/95 shadow-2xl backdrop-blur-xl">
                {/* Header close button */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-lg hover:bg-white/5 transition-colors"
                >
                    <X className="w-5 h-5" />
                </button>

                {/* Decorative glow */}
                <div className="absolute -top-20 -right-20 w-40 h-40 bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />
                <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />

                <div className="relative z-10 space-y-4">
                    {/* Icon Header */}
                    <div className="flex items-center space-x-3">
                        <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400">
                            <Send className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                Vincular Telegram <Sparkles className="w-4 h-4 text-amber-400" />
                            </h3>
                            {email && (
                                <p className="text-xs text-slate-400">
                                    Conectado como <span className="text-blue-400 font-medium">{email}</span>
                                </p>
                            )}
                        </div>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">
                        Conecta tu sesión activa de Telegram para sincronizar tus descargas diarias, foto de perfil y rango.
                    </p>

                    {error && (
                        <div className="flex items-center space-x-2 p-3 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl animate-shake">
                            <AlertCircle className="w-4 h-4 shrink-0" />
                            <span>{error}</span>
                        </div>
                    )}

                    {successMessage && (
                        <div className="flex items-center space-x-2 p-3 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                            <CheckCircle2 className="w-4 h-4 shrink-0" />
                            <span>{successMessage}</span>
                        </div>
                    )}

                    {/* Direct Telegram Session Button */}
                    {(() => {
                        const startParam = email ? `?start=link_${btoa(email).replace(/=/g, '')}` : '';
                        const botLink = `https://t.me/spcore_bot${startParam}`;
                        return (
                            <div className="flex flex-col items-center justify-center p-4 bg-gradient-to-br from-blue-600/15 to-purple-600/15 border border-blue-500/20 rounded-xl space-y-3 text-center">
                                <p className="text-xs font-semibold text-slate-200">
                                    Método Directo: Usa tu Sesión de Telegram ✈️
                                </p>
                                <a
                                    href={botLink}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center justify-center space-x-2 px-5 py-2.5 text-xs font-bold text-white bg-blue-500 hover:bg-blue-400 rounded-xl shadow-lg shadow-blue-500/25 active:scale-95 transition-all"
                                >
                                    <Send className="w-4 h-4" />
                                    <span>Abrir Bot en Telegram</span>
                                </a>
                                <p className="text-[11px] text-slate-400">
                                    Abre el bot directamente en tu app de Telegram sin ingresar número de teléfono.
                                </p>
                            </div>
                        );
                    })()}

                    <div className="relative flex items-center justify-center my-2">
                        <div className="border-t border-white/10 w-full" />
                        <span className="bg-slate-900 px-3 text-[10px] text-slate-500 font-bold uppercase tracking-wider">o vincular por alias</span>
                        <div className="border-t border-white/10 w-full" />
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4 pt-1">
                        <div>
                            <label className="block mb-1.5 text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                Tu Alias de Telegram (@usuario) o ID
                            </label>
                            <input
                                type="text"
                                value={telegramInput}
                                onChange={(e) => setTelegramInput(e.target.value)}
                                placeholder="Ej. @mi_usuario o 123456789"
                                className="w-full px-4 py-2.5 text-sm text-white placeholder-slate-500 bg-slate-800/80 border border-white/10 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                            />
                        </div>

                        <div className="flex items-center justify-end space-x-3 pt-2">
                            <button
                                type="button"
                                onClick={onClose}
                                className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
                            >
                                Omitir
                            </button>
                            <button
                                type="submit"
                                disabled={loading}
                                className="flex items-center justify-center space-x-2 px-4 py-2 text-xs font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl hover:from-blue-500 hover:to-indigo-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 shadow-lg shadow-blue-500/20 disabled:opacity-50 transition-all"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                        <span>Vinculando...</span>
                                    </>
                                ) : (
                                    <span>Vincular Cuenta</span>
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};
