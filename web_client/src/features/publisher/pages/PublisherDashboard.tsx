import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
    RefreshCw,
    Star
} from 'lucide-react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { ScheduleModal } from '../components/ScheduleModal';
import { ChannelModal } from '../components/ChannelModal';
import { PublicationTemplate, PublicationQueueItem, PublicationChannel } from '../services/publisherApi';

export const PublisherDashboard: React.FC = () => {
    const { settings } = useTheme();
    const {
        queue,
        channels,
        discoveredChats,
        templates,
        loading,
        error,
        refresh,
        deleteQueueItem,
        toggleFavorite,
        promoteDiscovered,
        saveChannel,
        deleteChannel,
        saveTemplate,
        deleteTemplate,
        restoreTemplates
    } = usePublisher();
    const [activeTab, setActiveTab] = useState<'queue' | 'channels' | 'templates'>('queue');
    const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
    const [editingQueueItem, setEditingQueueItem] = useState<PublicationQueueItem | null>(null);
    const [selectedBookHash, setSelectedBookHash] = useState('');
    const [selectedBookTitle, setSelectedBookTitle] = useState('');
    const [isChannelModalOpen, setIsChannelModalOpen] = useState(false);
    const [editingChannel, setEditingChannel] = useState<PublicationChannel | null>(null);
    const navigate = useNavigate();

    const handleCreateTemplate = () => {
        React.startTransition(() => {
            navigate('/admin/templates/new');
        });
    };

    const handleEditTemplate = (template: PublicationTemplate) => {
        React.startTransition(() => {
            navigate(`/admin/templates/${template.id}`);
        });
    };

    const handleEditQueueItem = (item: PublicationQueueItem) => {
        setEditingQueueItem(item);
        setSelectedBookHash(item.book_hash);
        setSelectedBookTitle(`${item.series_spanish || item.series || 'Editando Publicación'}`);
        setIsScheduleModalOpen(true);
    };

    const handleCreateChannel = () => {
        setEditingChannel(null);
        setIsChannelModalOpen(true);
    };

    const handleEditChannel = (channel: PublicationChannel) => {
        setEditingChannel(channel);
        setIsChannelModalOpen(true);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[50vh]">
                <div className="loader ring-2 ring-primary ring-offset-2 rounded-full w-8 h-8 animate-spin"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4">
                <div className="glass-panel border-red-500/30 p-6 flex flex-col items-center gap-4 text-center">
                    <div className="p-3 rounded-full bg-red-500/10 text-red-500">
                        <span className="material-icons-round text-3xl">error_outline</span>
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-white mb-1">Error al cargar el Publicador</h3>
                        <p className="text-gray-400 max-w-xs mx-auto">{error}</p>
                    </div>
                    <button
                        onClick={refresh}
                        className="px-6 py-2 bg-primary rounded-premium text-white font-medium hover:brightness-110 active:scale-95 transition-all"
                    >
                        Reintentar
                    </button>
                </div>
            </div>
        );
    }

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
            <div className="flex gap-2 p-1.5 glass-panel rounded-premium w-full sticky top-0 z-20 border border-[var(--panel-border)] shadow-premium"
                style={{
                    background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                    backdropFilter: `blur(${settings.glassBlur}px) saturate(${settings.glassSaturation}%)`,
                    WebkitBackdropFilter: `blur(${settings.glassBlur}px) saturate(${settings.glassSaturation}%)`
                }}>
                {(['queue', 'channels', 'templates'] as const).map((tab) => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`min-h-[44px] flex-1 flex items-center justify-center gap-2 py-3 rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all duration-500 ${activeTab === tab
                            ? 'bg-primary text-white shadow-[0_10px_20px_-5px_rgba(var(--color-primary-rgb),0.3)] scale-[1.02]'
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
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
                            <h2 className="text-xs font-black uppercase tracking-[0.2em] text-primary/80 drop-shadow-sm">Cola de Publicación</h2>
                            <button onClick={refresh} className="p-3 min-w-[44px] min-h-[44px] flex items-center justify-center glass-panel rounded-full border border-[var(--panel-border)] hover:bg-white/10 hover:scale-110 active:scale-95 transition-all duration-500 group/refresh">
                                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-700'}`} />
                            </button>
                        </div>

                        {queue.length === 0 ? (
                            <div className="glass-panel rounded-premium p-12 flex flex-col items-center gap-4 text-center border border-[var(--panel-border)] backdrop-blur-2xl">
                                <div className="p-5 rounded-full bg-white/5 border border-white/5 shadow-inner">
                                    <Clock className="w-10 h-10 text-gray-400/30" />
                                </div>
                                <p className="text-xs text-gray-500 font-bold uppercase tracking-widest opacity-60">No hay publicaciones programadas</p>
                            </div>
                        ) : (
                            queue.map((item) => (
                                <div key={item.id} className="glass-panel rounded-premium p-5 border border-[var(--panel-border)] flex flex-col gap-4 group relative overflow-hidden backdrop-blur-2xl hover:bg-white/[0.02] transition-colors duration-500 shadow-premium">
                                    {/* Background decoration */}
                                    {item.status === 'failed' && <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/5 blur-3xl -z-10" />}
                                    {item.status === 'sent' && <div className="absolute top-0 right-0 w-24 h-24 bg-green-500/5 blur-3xl -z-10" />}

                                    <div className="flex justify-between items-start">
                                        <div className="flex items-center gap-4">
                                            <div className={`p-3 rounded-2xl bg-white/5 border border-white/10 shadow-inner group-hover:scale-110 transition-transform duration-500 ${item.platform === 'telegram' ? 'text-[#0088cc]' : 'text-primary'}`}>
                                                {item.platform === 'telegram' ? <TelegramIcon className="w-5 h-5" /> : <Facebook className="w-5 h-5" />}
                                            </div>
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs font-black uppercase tracking-widest text-white drop-shadow-sm">
                                                        {item.series_spanish || item.series || 'Sin Título'}
                                                    </span>
                                                    {item.volume !== undefined && item.volume !== null && (
                                                        <span className="text-[9px] font-black bg-primary/20 px-2 py-0.5 rounded-full text-primary border border-primary/30 shadow-[0_0_10px_rgba(var(--color-primary-rgb),0.2)]">
                                                            VOL. {item.volume}
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.15em]">{item.channel}</span>
                                                    <span className="text-[9px] text-gray-500 font-bold flex items-center gap-1.5 uppercase tracking-wider">
                                                        <Calendar className="w-3 h-3 text-primary/60" />
                                                        {new Date(item.scheduled_for).toLocaleString()}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-[9px] font-black uppercase tracking-[0.1em] shadow-sm border ${item.status === 'sent' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                                                item.status === 'failed' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                                    'bg-white/5 text-gray-400 border-white/10'
                                                }`}>
                                                <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${item.status === 'sent' ? 'bg-green-400' : item.status === 'failed' ? 'bg-red-400' : 'bg-gray-400'}`} />
                                                {item.status === 'pending' ? 'Pendiente' :
                                                    item.status === 'publishing' ? 'Enviando...' :
                                                        item.status === 'sent' ? 'Enviado' : 'Fallido'}
                                            </div>
                                            <div className="flex items-center bg-white/5 rounded-full border border-white/10 p-1">
                                                <button
                                                    onClick={() => handleEditQueueItem(item)}
                                                    className="p-2 min-w-[36px] min-h-[36px] flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 rounded-full transition-all duration-300"
                                                    title="Editar"
                                                >
                                                    <Edit3 className="w-3.5 h-3.5" />
                                                </button>
                                                <button
                                                    onClick={() => deleteQueueItem(item.id)}
                                                    className="p-2 min-w-[36px] min-h-[36px] flex items-center justify-center text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-full transition-all duration-300"
                                                >
                                                    <Trash2 className="w-3.5 h-3.5" />
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-3 px-4 py-2.5 bg-black/40 rounded-premium-sm border border-white/5 group-hover:border-primary/20 transition-colors duration-500 shadow-inner">
                                        <div className="p-1.5 rounded bg-white/5">
                                            <Copy className="w-3 h-3 text-primary/60" />
                                        </div>
                                        <span className="text-[10px] text-gray-400 font-mono tracking-wider truncate uppercase opacity-80">{item.book_hash}</span>
                                    </div>

                                    {item.error && (
                                        <div className="px-4 py-3 bg-red-500/5 rounded-premium-sm border border-red-500/10 flex items-start gap-3 animate-in fade-in slide-in-from-top-1 duration-500">
                                            <div className="p-1.5 rounded-full bg-red-500/10">
                                                <AlertCircle className="w-3 h-3 text-red-400" />
                                            </div>
                                            <p className="text-[10px] text-red-300/80 leading-relaxed font-bold uppercase tracking-wide">{item.error}</p>
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                )}

                {activeTab === 'channels' && (
                    <div className="flex flex-col gap-4">
                        {/* Authorized Channels */}
                        <div className="flex flex-col gap-4">
                            <div className="flex justify-between items-center px-1">
                                <h2 className="text-xs font-black uppercase tracking-[0.2em] text-primary/80 drop-shadow-sm">Canales Vinculados</h2>
                                <button
                                    onClick={handleCreateChannel}
                                    className="min-h-[44px] flex items-center gap-2 px-6 py-2.5 glass-panel rounded-premium-sm text-[10px] font-black uppercase tracking-widest bg-primary text-white border-primary shadow-premium hover:scale-105 active:scale-95 transition-all duration-500"
                                >
                                    <Plus className="w-4 h-4" /> Nuevo Canal
                                </button>
                            </div>

                            {channels.length === 0 ? (
                                <div className="glass-panel rounded-premium p-12 flex flex-col items-center gap-4 text-center border border-[var(--panel-border)] backdrop-blur-2xl">
                                    <div className="p-5 rounded-full bg-white/5 border border-white/5 shadow-inner">
                                        <TelegramIcon className="w-10 h-10 text-gray-400/30" />
                                    </div>
                                    <p className="text-xs text-gray-500 font-bold uppercase tracking-widest opacity-60">No hay canales configurados</p>
                                </div>
                            ) : (
                                channels.map(channel => (
                                    <div key={channel.id} className={`glass-panel rounded-premium p-5 border flex items-center justify-between group transition-all duration-500 backdrop-blur-2xl shadow-premium hover:bg-white/[0.02] ${channel.is_favorite
                                        ? 'border-yellow-500/20 bg-yellow-500/[0.03]'
                                        : 'border-[var(--panel-border)]'}`}>
                                        <div className="flex items-center gap-5">
                                            <div className={`p-4 rounded-2xl shadow-inner relative group-hover:scale-110 transition-transform duration-500 ${channel.platform === 'telegram' ? 'bg-blue-500/10 text-[#0088cc]' : 'bg-primary/10 text-primary'
                                                }`}>
                                                {channel.platform === 'telegram' ? <TelegramIcon className="w-6 h-6" /> : <Facebook className="w-6 h-6" />}
                                                {channel.is_favorite && (
                                                    <div className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-yellow-400 rounded-full border-2 border-[#1a1b1e] shadow-md transform rotate-12 flex items-center justify-center">
                                                        <Star className="w-2 h-2 text-black fill-black" />
                                                    </div>
                                                )}
                                            </div>
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-3">
                                                    <span className="text-xs font-black uppercase tracking-widest text-white drop-shadow-sm">{channel.name}</span>
                                                    {channel.is_favorite && (
                                                        <span className="text-[8px] text-yellow-500 font-black bg-yellow-500/10 px-2 py-0.5 rounded-full border border-yellow-500/20 tracking-tighter shadow-[0_0_10px_rgba(234,179,8,0.1)]">FAVORITO</span>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-2 opacity-60">
                                                    <code className="text-[10px] text-primary/80 font-mono tracking-tight">{channel.target_id}</code>
                                                    <span className="text-[8px] font-black uppercase text-gray-500 tracking-widest mt-0.5">• ID DIRECTO</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center bg-white/5 rounded-full border border-white/10 p-1">
                                            <button
                                                onClick={() => toggleFavorite(channel.id)}
                                                className={`p-2.5 min-w-[40px] min-h-[40px] flex items-center justify-center rounded-full transition-all duration-300 ${channel.is_favorite
                                                    ? 'text-yellow-400 hover:bg-yellow-400/10'
                                                    : 'text-gray-500 hover:text-yellow-400 hover:bg-yellow-400/5'}`}
                                                title={channel.is_favorite ? "Quitar de favoritos" : "Marcar como favorito"}
                                            >
                                                <Star className={`w-4 h-4 ${channel.is_favorite ? 'fill-yellow-400' : ''}`} />
                                            </button>
                                            <button
                                                onClick={() => handleEditChannel(channel)}
                                                className="p-2.5 min-w-[40px] min-h-[40px] flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 rounded-full transition-all duration-300"
                                            >
                                                <Edit3 className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => deleteChannel(channel.id)}
                                                className="p-2.5 min-w-[40px] min-h-[40px] flex items-center justify-center text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-full transition-all duration-300"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        {/* Discovered Chats */}
                        {discoveredChats && discoveredChats.length > 0 && (
                            <div className="flex flex-col gap-4 pt-6 border-t border-white/5 animate-in fade-in slide-in-from-bottom-4 duration-700">
                                <div className="flex justify-between items-center px-1">
                                    <div className="flex items-center gap-3">
                                        <h2 className="text-xs font-black uppercase tracking-[0.2em] text-cyan-400 drop-shadow-[0_0_8px_rgba(34,211,238,0.3)]">Chats Descubiertos</h2>
                                        <span className="px-2 py-0.5 rounded-full bg-cyan-500/10 text-[9px] font-black text-cyan-400 border border-cyan-500/20 shadow-inner">
                                            {discoveredChats.length}
                                        </span>
                                    </div>
                                    <span className="text-[9px] text-gray-500 uppercase font-black tracking-widest opacity-60">ESCÁNER AUTOMÁTICO</span>
                                </div>

                                <div className="grid grid-cols-1 gap-3">
                                    {discoveredChats.map(chat => (
                                        <div key={chat.chat_id} className="glass-panel rounded-premium p-4 border border-[var(--panel-border)] flex items-center justify-between group hover:bg-cyan-500/[0.02] hover:border-cyan-500/30 transition-all duration-500 backdrop-blur-2xl shadow-premium">
                                            <div className="flex items-center gap-4">
                                                <div className="p-3 rounded-2xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-inner group-hover:scale-110 transition-transform duration-500">
                                                    <TelegramIcon className="w-5 h-5" />
                                                </div>
                                                <div className="flex flex-col gap-1">
                                                    <span className="text-xs font-black text-white tracking-wide uppercase drop-shadow-sm">{chat.title}</span>
                                                    <div className="flex items-center gap-3 text-[9px] font-bold text-gray-500 uppercase tracking-widest">
                                                        <span className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10">{chat.type}</span>
                                                        <span className="flex items-center gap-1.5">
                                                            <div className="w-1 h-1 rounded-full bg-cyan-400" />
                                                            {chat.member_count} miembros
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            {chat.is_promoted ? (
                                                <div className="px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-full flex items-center gap-2 group/status shadow-inner">
                                                    <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
                                                    <span className="text-[9px] text-green-400 font-black uppercase tracking-widest">VINCULADO</span>
                                                </div>
                                            ) : (
                                                <button
                                                    onClick={() => promoteDiscovered(chat.chat_id, chat.title)}
                                                    className="flex items-center justify-center gap-2.5 min-h-[44px] px-5 rounded-full bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 text-cyan-400 text-[10px] font-black uppercase tracking-widest shadow-sm hover:scale-105 active:scale-95 transition-all duration-300"
                                                >
                                                    Agregar <Plus className="w-3.5 h-3.5" />
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'templates' && (
                    <div className="flex flex-col gap-4">
                        <div className="flex justify-between items-center px-1">
                            <h2 className="text-xs font-black uppercase tracking-[0.2em] text-primary/80 drop-shadow-sm">Plantillas Disponibles</h2>
                            <div className="flex gap-3">
                                <button
                                    onClick={() => restoreTemplates('telegram')}
                                    className="min-h-[44px] flex items-center gap-2 px-5 py-2 glass-panel rounded-premium-sm text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-white border-[var(--panel-border)] hover:bg-white/5 transition-all duration-300"
                                    title="Restaurar todas las plantillas de Telegram a sus valores por defecto"
                                >
                                    <RefreshCw className="w-3.5 h-3.5" /> Restaurar
                                </button>
                                <button
                                    onClick={handleCreateTemplate}
                                    className="min-h-[44px] flex items-center gap-2 px-6 py-2.5 glass-panel rounded-premium-sm text-[10px] font-black uppercase tracking-widest bg-primary text-white border-primary shadow-premium hover:scale-105 active:scale-95 transition-all duration-500"
                                >
                                    <Plus className="w-4 h-4" /> Nueva
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 gap-4">
                        {templates.map(template => (
                            <div key={template.id} className="glass-panel rounded-premium p-5 border border-[var(--panel-border)] flex flex-col gap-4 group backdrop-blur-2xl shadow-premium hover:bg-white/[0.02] transition-all duration-500">
                                <div className="flex justify-between items-center">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 shadow-inner group-hover:scale-110 transition-transform duration-500">
                                            <Type className="w-5 h-5 text-primary" />
                                        </div>
                                        <span className="text-xs font-black uppercase tracking-widest text-white drop-shadow-sm">{template.name}</span>
                                    </div>
                                    <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[9px] font-black uppercase tracking-[0.2em] text-gray-400 shadow-inner">
                                        {template.platform}
                                    </span>
                                </div>

                                <div className="relative group/content">
                                    <div className="absolute inset-0 bg-primary/5 blur-xl group-hover/content:bg-primary/10 transition-colors duration-500 -z-10" />
                                    <div
                                        className="p-4 bg-black/40 rounded-premium-sm text-[11px] text-gray-300 leading-relaxed italic whitespace-pre-line border border-white/5 line-clamp-4 prose prose-invert max-w-none group-hover:border-primary/20 transition-colors duration-500 shadow-inner"
                                        dangerouslySetInnerHTML={{ __html: template.content }}
                                    />
                                </div>

                                <div className="flex justify-end pt-2">
                                    <div className="flex items-center bg-white/5 rounded-full border border-white/10 p-1">
                                        <button
                                            onClick={() => handleEditTemplate(template)}
                                            className="p-2.5 min-w-[40px] min-h-[40px] flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 rounded-full transition-all duration-300"
                                            title="Editar"
                                        >
                                            <Edit3 className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => deleteTemplate(template.id)}
                                            className="p-2.5 min-w-[40px] min-h-[40px] flex items-center justify-center text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-full transition-all duration-300"
                                            title="Eliminar"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                        </div>
                    </div>
                )}
            </div>

            <ScheduleModal
                isOpen={isScheduleModalOpen}
                onClose={() => setIsScheduleModalOpen(false)}
                bookHash={selectedBookHash}
                bookTitle={selectedBookTitle}
                editingItem={editingQueueItem}
            />

            <ChannelModal
                isOpen={isChannelModalOpen}
                onClose={() => setIsChannelModalOpen(false)}
                onSave={saveChannel}
                editingChannel={editingChannel}
            />
        </div>
    );
};
