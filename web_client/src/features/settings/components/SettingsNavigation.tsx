import React from 'react';
import { ChevronRight, ShieldCheck, BookOpen, Download, Upload, Bug } from 'lucide-react';

interface SettingsNavigationProps {
    isAdmin: boolean;
    status: any;
    canUploadEpub: boolean;
    onNavigate: (tab: string) => void;
    onOpenRequestModal: () => void;
    onOpenReportModal: () => void;
}

export const SettingsNavigation: React.FC<SettingsNavigationProps> = ({
    isAdmin,
    status,
    canUploadEpub,
    onNavigate,
    onOpenRequestModal,
    onOpenReportModal
}) => {
    const navItems = [
        { id: 'admin', icon: ShieldCheck, label: 'Admin Terminal', desc: 'Gestionar Sistema', visible: isAdmin, color: 'text-red-400', bg: 'bg-red-500/10' },
        { id: 'requests', icon: BookOpen, label: 'Biblioteca', desc: 'Gestionar Pedidos', visible: status?.user?.can_request_books !== false, color: 'text-blue-400', bg: 'bg-blue-500/10', action: onOpenRequestModal },
        { id: 'downloads', icon: Download, label: 'Descargas', desc: 'Recursos Locales', visible: status?.user?.has_library_access !== false, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
        { id: 'upload', icon: Upload, label: 'Subir Archivo', desc: 'Aportar Contenido', visible: canUploadEpub, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
        { id: 'report', icon: Bug, label: 'Asistencia', desc: 'Reportar Incidencia', visible: true, color: 'text-amber-400', bg: 'bg-amber-500/10', action: onOpenReportModal }
    ].filter(i => i.visible);

    return (
        <div className="glass-panel rounded-premium-lg overflow-hidden shadow-2xl border-white/5">
            <div className="p-8 border-b border-white/5 flex items-center justify-between">
                <h3 className="text-[11px] font-black text-gray-500 uppercase tracking-[0.4em]">Panel de Control</h3>
                <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
            </div>
            <div className="p-3 space-y-2">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => item.action ? item.action() : onNavigate(item.id)}
                        className="w-full flex items-center justify-between p-5 rounded-premium text-gray-400 hover:bg-white/[0.04] transition-all duration-500 group"
                    >
                        <div className="flex items-center gap-5">
                            <div className={`p-3.5 rounded-premium-sm ${item.bg} ${item.color} border border-white/10 shadow-lg group-hover:scale-110 group-hover:rotate-3 transition-all duration-500`}>
                                <item.icon className="w-5 h-5" strokeWidth={2.5} />
                            </div>
                            <div className="text-left">
                                <p className="text-[13px] font-black text-white uppercase tracking-tight group-hover:text-primary transition-colors">{item.label}</p>
                                <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest opacity-60 mt-0.5">{item.desc}</p>
                            </div>
                        </div>
                        <ChevronRight className="w-5 h-5 text-gray-700 group-hover:text-primary group-hover:translate-x-1 transition-all duration-500" />
                    </button>
                ))}
            </div>
        </div>
    );
};
