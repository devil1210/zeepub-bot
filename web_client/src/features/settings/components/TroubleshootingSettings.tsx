import React from 'react';
import { Wrench } from 'lucide-react';

interface TroubleshootingSettingsProps {
    onClearCache: () => void;
}

export const TroubleshootingSettings: React.FC<TroubleshootingSettingsProps> = ({ onClearCache }) => {
    return (
        <div className="glass-panel p-6 rounded-premium-sm border border-white/5">
            <h3 className="text-lg font-black text-white flex items-center gap-2 mb-4 uppercase tracking-tight">
                <Wrench className="text-red-400 w-5 h-5" />
                Solución de Problemas
            </h3>
            <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-4 bg-red-900/10 border border-red-900/30 rounded-premium-sm">
                <div>
                    <p className="text-sm font-bold text-red-200">Almacenamiento de Caché Local</p>
                    <p className="text-xs text-red-400 mt-1">Si notas comportamientos extraños, limpia la caché.</p>
                </div>
                <button
                    onClick={onClearCache}
                    className="px-4 py-2 bg-red-900/30 hover:bg-red-900/50 text-red-200 text-[10px] font-black uppercase tracking-widest rounded-lg border border-red-800 transition-colors"
                    title="Limpiar Caché"
                >
                    Limpiar Caché
                </button>
            </div>
        </div>
    );
};
