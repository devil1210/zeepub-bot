import React, { useState } from 'react';
import { BookOpen, ShieldAlert, ExternalLink, Mail } from 'lucide-react';
import { supabase } from '@shared/services/supabase';

interface LoginGateProps {
    onSuccess?: () => void;
}

export const LoginGate: React.FC<LoginGateProps> = () => {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [sent, setSent] = useState(false);

    const handleMagicLink = async () => {
        if (!email) return;
        setLoading(true);
        try {
            const { error } = await supabase.auth.signInWithOtp({
                email,
                options: {
                    emailRedirectTo: window.location.origin
                }
            });
            if (error) throw error;
            setSent(true);
        } catch (error: any) {
            alert(error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] bg-[#0a0c10] flex items-center justify-center p-6 overflow-hidden">
            {/* Background Effects */}
            <div className="absolute top-[-20%] right-[-10%] w-[800px] h-[800px] bg-primary/20 rounded-full blur-[180px] animate-pulse-slow"></div>
            <div className="absolute bottom-[-15%] left-[-20%] w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[150px] animate-float"></div>

            <div className="relative w-full max-w-md glass-panel p-10 rounded-[32px] border border-white/10 shadow-2xl animate-in zoom-in-95 fade-in duration-700">
                <div className="flex flex-col items-center text-center space-y-6">
                    {/* Icon Header */}
                    <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center shadow-2xl shadow-primary/40 mb-2">
                        <BookOpen className="text-white w-10 h-10" />
                    </div>

                    <div className="space-y-2">
                        <h1 className="text-3xl font-black tracking-tight text-white">Acceso Restringido</h1>
                        <p className="text-gray-400 text-sm font-medium leading-relaxed">
                            Has intentado acceder a la terminal de <span className="text-primary font-bold">ZeePub</span> fuera de Telegram.
                        </p>
                    </div>

                    {!sent ? (
                        <div className="w-full space-y-4 pt-4">
                            <div className="p-4 rounded-premium-sm bg-red-500/10 border border-red-500/20 flex items-start gap-3 text-left">
                                <ShieldAlert className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                                <div className="text-[12px] text-red-200/80 leading-snug">
                                    Para proteger tu biblioteca, el acceso web requiere autenticación vinculada a tu ID de Telegram.
                                </div>
                            </div>

                            <div className="relative group">
                                <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                                    <Mail className="w-5 h-5 text-gray-500 group-focus-within:text-primary transition-colors" />
                                </div>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="Tu correo de usuario"
                                    className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 text-white placeholder:text-gray-600 focus:outline-none focus:border-primary/50 focus:bg-white/[0.08] transition-all"
                                />
                            </div>

                            <button
                                onClick={handleMagicLink}
                                disabled={loading || !email}
                                className="w-full bg-primary hover:bg-primary-dark text-white font-black py-4 rounded-2xl shadow-xl shadow-primary/20 transition-all active:scale-95 flex items-center justify-center gap-2"
                            >
                                {loading ? 'Enviando...' : 'Obtener Acceso'}
                                {!loading && <ExternalLink className="w-5 h-5" />}
                            </button>

                            <div className="pt-4">
                                <a
                                    href="https://t.me/zeepub_bot"
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-[11px] font-black uppercase tracking-widest text-gray-500 hover:text-white transition-colors flex items-center justify-center gap-2"
                                >
                                    Ir al Bot de Telegram
                                </a>
                            </div>
                        </div>
                    ) : (
                        <div className="w-full py-8 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="w-16 h-16 rounded-full bg-green-500/20 text-green-500 flex items-center justify-center mx-auto mb-4 border border-green-500/30">
                                <Mail className="w-8 h-8" />
                            </div>
                            <div className="space-y-2">
                                <h2 className="text-xl font-bold text-white">Revisa tu correo</h2>
                                <p className="text-gray-400 text-sm leading-relaxed">
                                    Hemos enviado un **Link de Acceso** a <span className="text-white font-bold">{email}</span>. Click en el link para entrar.
                                </p>
                            </div>
                            <button
                                onClick={() => setSent(false)}
                                className="text-sm font-bold text-primary hover:underline"
                            >
                                Intentar con otro correo
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <div className="fixed bottom-8 text-gray-600 text-[10px] font-black uppercase tracking-[0.4em] opacity-40">
                ZeePub Security Protocol v3.5
            </div>
        </div>
    );
};
