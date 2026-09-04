import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Wrench,
    Grid,
    GitMerge,
    Tags,
    Sparkles,
    Activity,
    ArrowRight,
    Sliders,
    Building2
} from 'lucide-react';

export const EditorialLegacyTools: React.FC = () => {
    const navigate = useNavigate();

    const tools = [
        {
            title: 'Directorio & Fusión de Fansubs',
            desc: 'Auditoría de EPUBs asociados por grupo, detección de metadatos discordantes y herramienta de fusión.',
            icon: Building2,
            color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
            action: () => navigate('/app-v2/fansubs'),
        },
        {
            title: 'DataGrid Editor (Modo Excel)',
            desc: 'Editor masivo de metadatos de series y volúmenes con guardado por lotes.',
            icon: Grid,
            color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
            action: () => navigate('/admin/series-manager'),
        },
        {
            title: 'Gestor de Duplicados & Merges',
            desc: 'Detección automática de libros duplicados por hash SHA-256 / MD5 y herramientas de purga.',
            icon: GitMerge,
            color: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
            action: () => navigate('/admin'),
        },
        {
            title: 'Auditoría de Géneros y Demografías',
            desc: 'Revisión y homologación de etiquetas de demografía y categorías literarias.',
            icon: Tags,
            color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
            action: () => navigate('/admin'),
        },
        {
            title: 'Hub de Inteligencia Artificial (Gemini)',
            desc: 'Propuestas de normalización de títulos, extracción de volúmenes y corrección ortográfica asistida.',
            icon: Sparkles,
            color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
            action: () => navigate('/ai'),
        },
        {
            title: 'Observatorio & Monitor de Tareas',
            desc: 'Diagnóstico en tiempo real del bot de Telegram, tareas en segundo plano y rendimiento de base de datos.',
            icon: Activity,
            color: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
            action: () => navigate('/app-v2/settings'),
        },
    ];

    return (
        <div className="w-full max-w-[2100px] mx-auto space-y-6 animate-in fade-in duration-300">
            <div>
                <h2 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
                    <Wrench className="w-6 h-6 text-indigo-400" /> Herramientas de Mantenimiento & Legacy
                </h2>
                <p className="text-xs text-gray-400 mt-1">
                    Acceso directo a todos los módulos avanzados de administración técnica y utilidades del sistema.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {tools.map((tool) => {
                    const Icon = tool.icon;
                    return (
                        <div
                            key={tool.title}
                            onClick={tool.action}
                            className="p-6 rounded-2xl bg-slate-900/50 border border-white/10 hover:border-white/20 transition-all cursor-pointer group flex flex-col justify-between backdrop-blur-xl"
                        >
                            <div className="space-y-3">
                                <div className={`p-3 w-fit rounded-xl border ${tool.color}`}>
                                    <Icon className="w-6 h-6" />
                                </div>
                                <h3 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors">
                                    {tool.title}
                                </h3>
                                <p className="text-xs text-gray-400 leading-relaxed">
                                    {tool.desc}
                                </p>
                            </div>

                            <div className="mt-5 pt-3 border-t border-white/5 flex items-center gap-1.5 text-xs font-bold text-indigo-400 group-hover:text-indigo-300 transition-colors">
                                Abrir herramienta <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
