import React, { useState } from 'react';
import { useNavigation } from '@shared/contexts/NavigationContext';
import { usePublisher } from '../hooks/usePublisher';
import {
    Send,
    Calendar,
    Clock,
    Settings,
    Trash2,
    Plus,
    Edit3,
    CheckCircle2,
    XCircle,
    AlertCircle,
    Copy,
    Type,
    Facebook,
    Send as TelegramIcon,
    RefreshCw
} from 'lucide-react';
import { useTheme } from '@shared/contexts/ThemeContext';

export const PublisherDashboard: React.FC = () => {
    const { settings } = useTheme();
    const { queue, channels, templates, loading, deleteQueueItem, refresh } = usePublisher();
    const [activeTab, setActiveTab] = useState<'queue' | 'channels' | 'templates'>('queue');


    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'sent': return <CheckCircle2 className="w-4 h-4 text-green-400" />;
            case 'failed': return <XCircle className="w-4 h-4 text-red-400" />;
            case 'publishing': return <RefreshCw className="w-4 h-4 text-primary animate-spin" />;
            default: return <Clock className="w-4 h-4 text-gray-400" />;
        }
    };

    return (
        <div className="flex flex-col gap-6 pb-24">
            {/* Header Tabs */}
            <div className="flex gap-2 p-1 glass-panel rounded-premium w-full sticky top-0 z-20"
                style={{
                    background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                    backdropFilter: `blur(${settings.glassBlur}px)`
                }}>
                {(['queue', 'channels', 'templates'] as const).map((tab) => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === tab ? 'bg-primary text-white shadow-lg' : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        {tab === 'queue' && <Calendar className="w-3.5 h-3.5" />}
                        {tab === 'channels' && <Send className="w-3.5 h-3.5" />}
                        {tab === 'templates' && <Type className="w-3.5 h-3.5" />}
                        {tab === 'queue' ? 'Cola' : tab === 'channels' ? 'Canales' : 'Plantillas'}
                    </button>
                ))}
            </div>

            <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
                {activeTab === 'queue' && (
                    <div className="flex flex-col gap-3">
                        <div className="flex justify-between items-center px-1">
                            <h2 className="text-xs font-black uppercase tracking-[0.2em] text-primary/80">Cola de Publicación</h2>
                            <button onClick={refresh} className="p-2 glass-panel rounded-full hover:bg-white/10 transition-all">
                                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                            </button>
                        </div>

                        {queue.length === 0 ? (
                            <div className="glass-panel rounded-premium p-10 flex flex-col items-center gap-3 text-center">
                                <div className="p-4 rounded-full bg-white/5">
                                    <Clock className="w-8 h-8 text-gray-400/50" />
                                </div>
                                <p className="text-xs text-gray-500 font-medium">No hay publicaciones programadas</p>
                            </div>
                        ) : (
                            queue.map((item) => (
                                <div key={item.id} className="glass-panel rounded-premium p-4 border border-white/5 flex flex-col gap-3 group relative overflow-hidden">
                                    {/* Background decoration */}
                                    {item.status === 'failed' && <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/5 blur-3xl -z-10" />}
                                    {item.status === 'sent' && <div className="absolute top-0 right-0 w-24 h-24 bg-green-500/5 blur-3xl -z-10" />}

                                    <div className="flex justify-between items-start">
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-xl bg-white/5 ${item.platform === 'telegram' ? 'text-blue-400' : 'text-primary'}`}>
                                                {item.platform === 'telegram' ? <TelegramIcon className="w-4 h-4" /> : <Facebook className="w-4 h-4" />}
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-[11px] font-black uppercase tracking-wider">{item.channel}</span>
                                                <span className="text-[10px] text-gray-400 flex items-center gap-1">
                                                    <Calendar className="w-3 h-3" />
                                                    {new Date(item.scheduled_for).toLocaleString()}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[9px] font-black uppercase tracking-wider ${item.status === 'sent' ? 'bg-green-500/10 text-green-400' :
                                                item.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                                                    'bg-white/5 text-gray-400'
                                                }`}>
                                                {getStatusIcon(item.status)}
                                                {item.status === 'pending' ? 'Pendiente' :
                                                    item.status === 'publishing' ? 'Enviando...' :
                                                        item.status === 'sent' ? 'Enviado' : 'Fallido'}
                                            </div>
                                            <button
                                                onClick={() => deleteQueueItem(item.id)}
                                                className="p-1.5 text-gray-500 hover:text-red-400 transition-colors"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 px-3 py-2 bg-black/20 rounded-premium-sm border border-white/5">
                                        <Copy className="w-3 h-3 text-gray-500" />
                                        <span className="text-[10px] text-gray-400 font-mono truncate">{item.book_hash}</span>
                                    </div>

                                    {item.error && (
                                        <div className="px-3 py-2 bg-red-500/10 rounded-premium-sm border border-red-500/20 flex items-start gap-2">
                                            <AlertCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0 mt-0.5" />
                                            <p className="text-[10px] text-red-300 leading-relaxed font-medium">{item.error}</p>
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                )}

                {activeTab === 'channels' && (
                    <div className="flex flex-col gap-3">
                        <div className="flex justify-between items-center px-1">
                            <h2 className="text-xs font-black uppercase tracking-[0.2em] text-primary/80">Canales Vinculados</h2>
                            <button className="flex items-center gap-2 px-3 py-1.5 glass-panel rounded-premium-sm text-[9px] font-black uppercase bg-primary text-white border-primary shadow-lg shadow-primary/20">
                                <Plus className="w-3.5 h-3.5" /> Nuevo
                            </button>
                        </div>

                        {channels.map(channel => (
                            <div key={channel.id} className="glass-panel rounded-premium p-4 border border-white/5 flex items-center justify-between group">
                                <div className="flex items-center gap-4">
                                    <div className={`p-3 rounded-2xl ${channel.platform === 'telegram' ? 'bg-blue-500/10 text-blue-400' : 'bg-primary/10 text-primary'
                                        } shadow-inner`}>
                                        {channel.platform === 'telegram' ? <TelegramIcon className="w-5 h-5" /> : <Facebook className="w-5 h-5" />}
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-xs font-black uppercase tracking-wider">{channel.name}</span>
                                        <span className="text-[10px] text-gray-500 font-medium">{channel.target_id}</span>
                                    </div>
                                </div>
                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button className="p-2 text-gray-400 hover:text-white transition-colors"><Edit3 className="w-4 h-4" /></button>
                                    <button className="p-2 text-gray-400 hover:text-red-400 transition-colors"><Trash2 className="w-4 h-4" /></button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {activeTab === 'templates' && (
                    <div className="flex flex-col gap-3">
                        <div className="flex justify-between items-center px-1">
                            <h2 className="text-xs font-black uppercase tracking-[0.2em] text-primary/80">Plantillas de Texto</h2>
                            <button className="flex items-center gap-2 px-3 py-1.5 glass-panel rounded-premium-sm text-[9px] font-black uppercase bg-primary text-white border-primary shadow-lg shadow-primary/20">
                                <Plus className="w-3.5 h-3.5" /> Nueva
                            </button>
                        </div>

                        {templates.map(template => (
                            <div key={template.id} className="glass-panel rounded-premium p-4 border border-white/5 flex flex-col gap-3 group">
                                <div className="flex justify-between items-center">
                                    <div className="flex items-center gap-2">
                                        <Type className="w-4 h-4 text-primary" />
                                        <span className="text-xs font-black uppercase tracking-wider">{template.name}</span>
                                    </div>
                                    <div className="px-2 py-0.5 rounded-full bg-white/5 text-[9px] font-black uppercase tracking-wider text-gray-400">
                                        {template.platform}
                                    </div>
                                </div>
                                <div className="p-3 bg-black/20 rounded-premium-sm text-[10px] text-gray-300 leading-relaxed italic whitespace-pre-line border border-white/5">
                                    {template.content.length > 150 ? template.content.substring(0, 150) + '...' : template.content}
                                </div>
                                <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button className="p-2 text-gray-400 hover:text-white transition-colors"><Edit3 className="w-4 h-4" /></button>
                                    <button className="p-2 text-gray-400 hover:text-red-400 transition-colors"><Trash2 className="w-4 h-4" /></button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
