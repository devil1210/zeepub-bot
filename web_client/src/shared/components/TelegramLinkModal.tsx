import React, { useState, useEffect, useRef } from 'react';
import { Send, CheckCircle2, AlertCircle, Loader2, Sparkles, X, QrCode, Smartphone, RefreshCw } from 'lucide-react';
import { api } from '@shared/services/api';
import { useTelegram } from '@shared/contexts/TelegramContext';

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
    const { botInfo } = useTelegram();
    const [activeTab, setActiveTab] = useState<'qr' | 'alias'>('qr');
    const [qrToken, setQrToken] = useState<string | null>(null);
    const [botLink, setBotLink] = useState<string | null>(null);
    const [qrLoading, setQrLoading] = useState(false);

    // Alias form states
    const [telegramInput, setTelegramInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const pollingIntervalRef = useRef<any>(null);

    // Generate QR Auth Session when modal opens
    useEffect(() => {
        if (!isOpen) {
            if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
            return;
        }

        fetchQrSession();

        return () => {
            if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
        };
    }, [isOpen]);

    const fetchQrSession = async () => {
        try {
            setQrLoading(true);
            const res = await api.generateQrAuth();
            if (res.success && res.token) {
                setQrToken(res.token);
                setBotLink(res.bot_link);
                startPolling(res.token);
            }
        } catch (e) {
            console.error("Failed to generate QR auth session:", e);
        } finally {
            setQrLoading(false);
        }
    };

    const startPolling = (token: string) => {
        if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);

        pollingIntervalRef.current = setInterval(async () => {
            try {
                const res = await api.checkQrAuth(token);
                if (res.status === 'authenticated') {
                    if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
                    setSuccessMessage('¡Vinculación confirmada desde Telegram!');
                    setTimeout(() => {
                        onSuccess();
                        onClose();
                    }, 1200);
                } else if (res.status === 'expired') {
                    if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
                }
            } catch (e) {
                // Ignore transient polling errors
            }
        }, 2000);
    };

    if (!isOpen) return null;

    const handleSubmitAlias = async (e: React.FormEvent) => {
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
            const detailMsg = err.response?.data?.detail || err.message;
            setError(detailMsg || 'Error de conexión al vincular la cuenta.');
        } finally {
            setLoading(false);
        }
    };

    const botUsername = botInfo?.username ? botInfo.username.replace(/^@/, '') : 'zeepub_bot';

    const defaultFallbackLink = email
        ? `https://t.me/${botUsername}?start=link_${btoa(email).replace(/=/g, '')}`
        : `https://t.me/${botUsername}`;

    const activeBotLink = botLink || defaultFallbackLink;

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
                    {/* Header */}
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

                    {/* Tabs */}
                    <div className="grid grid-cols-2 p-1 bg-slate-950/60 border border-white/5 rounded-xl text-xs font-semibold">
                        <button
                            type="button"
                            onClick={() => setActiveTab('qr')}
                            className={`flex items-center justify-center gap-2 py-2 rounded-lg transition-all ${
                                activeTab === 'qr'
                                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25'
                                    : 'text-slate-400 hover:text-white'
                            }`}
                        >
                            <QrCode className="w-4 h-4" />
                            <span>1-Clic / Código QR</span>
                        </button>
                        <button
                            type="button"
                            onClick={() => setActiveTab('alias')}
                            className={`flex items-center justify-center gap-2 py-2 rounded-lg transition-all ${
                                activeTab === 'alias'
                                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25'
                                    : 'text-slate-400 hover:text-white'
                            }`}
                        >
                            <Smartphone className="w-4 h-4" />
                            <span>Por @Alias o ID</span>
                        </button>
                    </div>

                    {error && (
                        <div className="flex items-center space-x-2 p-3 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl animate-shake">
                            <AlertCircle className="w-4 h-4 shrink-0" />
                            <span>{error}</span>
                        </div>
                    )}

                    {successMessage && (
                        <div className="flex items-center space-x-2 p-3 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-xl animate-fade-in">
                            <CheckCircle2 className="w-4 h-4 shrink-0" />
                            <span className="font-semibold">{successMessage}</span>
                        </div>
                    )}

                    {/* Tab 1: QR & Direct Link */}
                    {activeTab === 'qr' && (
                        <div className="space-y-4 pt-1 text-center">
                            {/* QR Code Container */}
                            <div className="relative mx-auto w-48 h-48 p-3 bg-slate-950/80 border border-blue-500/30 rounded-2xl shadow-xl flex items-center justify-center group overflow-hidden">
                                {qrLoading ? (
                                    <div className="flex flex-col items-center space-y-2 text-slate-400 text-xs">
                                        <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
                                        <span>Generando QR...</span>
                                    </div>
                                ) : activeBotLink ? (
                                    <>
                                        <img
                                            src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(activeBotLink)}&bgcolor=020617&color=38bdf8`}
                                            alt="QR Auth Telegram"
                                            className="w-full h-full rounded-lg object-contain"
                                        />
                                        {/* Scanner Line Effect */}
                                        <div className="absolute inset-x-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_12px_#38bdf8] animate-bounce pointer-events-none opacity-75" />
                                    </>
                                ) : (
                                    <button
                                        onClick={fetchQrSession}
                                        className="flex flex-col items-center gap-1 text-xs text-slate-400 hover:text-white"
                                    >
                                        <RefreshCw className="w-5 h-5" />
                                        <span>Reintentar QR</span>
                                    </button>
                                )}
                            </div>

                            {/* Status Indicator */}
                            <div className="flex items-center justify-center space-x-2 text-[11px] text-slate-300">
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
                                </span>
                                <span>Escanea con tu cámara o usa el botón directo</span>
                            </div>

                            {/* Direct Telegram & OAuth Buttons */}
                            <div className="pt-1 space-y-2">
                                <a
                                    href={activeBotLink}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="w-full flex items-center justify-center space-x-2 px-5 py-3 text-xs font-bold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 rounded-xl shadow-lg shadow-blue-500/25 active:scale-95 transition-all"
                                >
                                    <Send className="w-4 h-4" />
                                    <span>Abrir Bot en Telegram 🚀</span>
                                </a>
                                <a
                                    href="/api/oauth/telegram/login"
                                    className="w-full flex items-center justify-center space-x-2 px-5 py-2.5 text-xs font-semibold text-sky-400 bg-sky-500/10 border border-sky-500/20 hover:bg-sky-500/20 rounded-xl active:scale-95 transition-all"
                                >
                                    <span>🔑 Usar Telegram OAuth 2.0 / OpenID</span>
                                </a>
                                <p className="text-[11px] text-slate-400 mt-2">
                                    Sin ingresar número de teléfono. Presiona <strong className="text-slate-200">INICIAR</strong> en Telegram para confirmar.
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Tab 2: Alias / ID Form */}
                    {activeTab === 'alias' && (
                        <form onSubmit={handleSubmitAlias} className="space-y-4 pt-1">
                            <p className="text-xs text-slate-300 leading-relaxed">
                                Ingresa tu username de Telegram para sincronizar directamente.
                            </p>
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
                    )}
                </div>
            </div>
        </div>
    );
};
