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
    Twitter,
    Send as TelegramIcon,
    RefreshCw,
    Star,
    Building2,
    Globe,
    MessageSquare,
    Heart,
    Coffee,
    BookOpen,
    Loader2
} from 'lucide-react';
import { api } from '@shared/services/api';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { useTheme } from '@shared/contexts/ThemeContext';
import { ScheduleModal } from '../components/ScheduleModal';
import { ChannelModal } from '../components/ChannelModal';
import { WorkgroupModal } from '../components/WorkgroupModal';
import { PublicationTemplate, PublicationQueueItem, PublicationChannel } from '../services/publisherApi';
import { TranslatorsGroupItem } from '../services/workgroupsApi';

export const PublisherDashboard: React.FC = () => {
    const { settings } = useTheme();
    const {
        queue,
        channels,
        discoveredChats,
        templates,
        workgroups,
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
        saveWorkgroup,
        deleteWorkgroup,
        restoreTemplates
    } = usePublisher();
    const [activeTab, setActiveTab] = useState<'queue' | 'channels' | 'templates' | 'workgroups'>('queue');
    const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
    const [editingQueueItem, setEditingQueueItem] = useState<PublicationQueueItem | null>(null);
    const [selectedBookHash, setSelectedBookHash] = useState('');
    const [selectedBookTitle, setSelectedBookTitle] = useState('');
    const [isChannelModalOpen, setIsChannelModalOpen] = useState(false);
    const [editingChannel, setEditingChannel] = useState<PublicationChannel | null>(null);
    const [isWorkgroupModalOpen, setIsWorkgroupModalOpen] = useState(false);
    const [editingWorkgroup, setEditingWorkgroup] = useState<TranslatorsGroupItem | null>(null);
    const [syncingFb, setSyncingFb] = useState(false);
    const { isAdmin, isStaff, webApp } = useTelegram();
    const canSync = isAdmin || isStaff;
    const navigate = useNavigate();

    const handleSyncFacebook = async () => {
        setSyncingFb(true);
        webApp?.HapticFeedback?.impactOccurred('medium');
        try {
            const res = await api.syncFacebookPublications(50, false);
            if (res.success) {
                const added = res.new_publications_synced ?? 0;
                const checked = res.posts_checked ?? 0;
                webApp?.HapticFeedback?.notificationOccurred('success');
                const msg = `✅ Sincronización completada: ${added} nuevas publicaciones vinculadas de ${checked} posts revisados.`;
                if (webApp?.showAlert) {
                    webApp.showAlert(msg);
                } else {
                    alert(msg);
                }
                refresh();
            } else {
                webApp?.HapticFeedback?.notificationOccurred('error');
                const errMsg = res.error || res.message || 'Error desconocido';
                if (webApp?.showAlert) webApp.showAlert(`⚠️ Error al sincronizar: ${errMsg}`);
                else alert(`⚠️ Error al sincronizar: ${errMsg}`);
            }
        } catch (error: any) {
            console.error('Error sincronizando Facebook:', error);
            webApp?.HapticFeedback?.notificationOccurred('error');
            const errMsg = error.message || 'Error de conexión';
            if (webApp?.showAlert) webApp.showAlert(`❌ Error al conectar con el servidor: ${errMsg}`);
            else alert(`❌ Error al conectar con el servidor: ${errMsg}`);
        } finally {
            setSyncingFb(false);
        }
    };

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
            <div className="flex gap-2 p-1 glass-panel rounded-premium w-full sticky top-0 z-20"
                style={{
                    background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                    backdropFilter: `blur(${settings.glassBlur}px)`
                }}>
                {(['queue', 'channels', 'templates', 'workgroups'] as const).map((tab) => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`min-h-[44px] flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === tab ? 'bg-primary text-white shadow-lg' : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        {tab === 'queue' && <Calendar className="w-3.5 h-3.5" />}
                        {tab === 'channels' && <Send className="w-3.5 h-3.5" />}
                        {tab === 'templates' && <Type className="w-3.5 h-3.5" />}
                        {tab === 'workgroups' && <Building2 className="w-3.5 h-3.5" />}
                        {tab === 'queue' ? 'Cola' : tab === 'channels' ? 'Canales' : tab === 'templates' ? 'Plantillas' : 'Fansubs'}
                    </button>
                ))}
            </div>

            <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
                {activeTab === 'queue' && (
                    <div className="flex flex-col gap-3">
                        <div className="flex justify-between items-center px-1">
                            <h2 className="text-xs font-black uppercase tracking-[0.2em] text-primary/80">Cola de Publicación</h2>
                            <button onClick={refresh} className="p-3 min-w-[44px] min-h-[44px] flex items-center justify-center glass-panel rounded-full hover:bg-white/10 transition-all">
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
                                            <div className={`p-2 rounded-xl bg-white/5 ${item.platform === 'telegram' ? 'text-blue-400' : item.platform === 'facebook' ? 'text-primary' : 'text-sky-400'}`}>
                                                {item.platform === 'telegram' ? <TelegramIcon className="w-4 h-4" /> : item.platform === 'facebook' ? <Facebook className="w-4 h-4" /> : <Twitter className="w-4 h-4" />}
                                            </div>
                                            <div className="flex flex-col gap-0.5">
                                                <div className="flex items-center gap-1.5">
                                                    <span className="text-[11px] font-black uppercase tracking-[0.05em] text-white">
                                                        {item.series_spanish || item.series || 'Sin Título'}
                                                    </span>
                                                    {item.volume !== undefined && item.volume !== null && (
                                                        <span className="text-[9px] font-black bg-primary/10 px-1.5 py-0.5 rounded text-primary border border-primary/20">
                                                            VOL. {item.volume}
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                                                        {typeof item.channel === 'object' && item.channel !== null 
                                                            ? (item.channel as any).name 
                                                            : String(item.channel || 'Unknown')}
                                                    </span>
                                                    <span className="text-[10px] text-gray-500 flex items-center gap-1">
                                                        <Calendar className="w-2.5 h-2.5" />
                                                        {new Date(item.scheduled_for).toLocaleString()}
                                                    </span>
                                                </div>
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
                                                onClick={() => handleEditQueueItem(item)}
                                                className="p-3 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-white transition-colors cursor-pointer"
                                                title={item.status === 'sent' ? 'Editar / Actualizar Publicación Enviada' : 'Editar'}
                                            >
                                                <Edit3 className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => deleteQueueItem(item.id)}
                                                className="p-3 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-500 hover:text-red-400 transition-colors"
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
                    <div className="flex flex-col gap-6">
                        {/* Facebook Feed Sync Banner */}
                        {canSync && (
                            <div className="glass-panel border border-blue-500/20 bg-blue-500/5 rounded-premium p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xl">
                                <div className="flex items-center gap-3.5">
                                    <div className="p-3 rounded-2xl bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-inner">
                                        <Facebook className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="text-xs font-black uppercase tracking-wider text-white flex items-center gap-2">
                                            Sincronización de Publicaciones Facebook
                                        </h3>
                                        <p className="text-[11px] text-gray-400 mt-0.5">
                                            Escanea posts manuales recientes del administrador en Facebook y los vincula automáticamente al catálogo.
                                        </p>
                                    </div>
                                </div>

                                <button
                                    onClick={handleSyncFacebook}
                                    disabled={syncingFb}
                                    className="group relative flex items-center justify-center gap-2.5 px-4 py-2.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 text-blue-300 hover:text-white transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-blue-500/20 active:scale-[0.98] text-xs font-bold shrink-0 self-end sm:self-center"
                                    title="Escanear posts recientes de Facebook y vincularlos a los EPUBs"
                                >
                                    {syncingFb ? (
                                        <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                                    ) : (
                                        <RefreshCw className="w-4 h-4 text-blue-400 group-hover:rotate-180 transition-transform duration-500" />
                                    )}
                                    <span>
                                        {syncingFb ? 'Sincronizando FB...' : 'Sincronizar Publicaciones FB'}
                                    </span>
                                </button>
                            </div>
                        )}

                        {/* Authorized Channels */}
                        <div className="flex flex-col gap-3">
                            <div className="flex justify-between items-center px-1">
                                <h2 className="text-xs font-black uppercase tracking-[0.2em] text-primary/80">Canales Vinculados</h2>
                                <button
                                    onClick={handleCreateChannel}
                                    className="min-h-[44px] flex items-center gap-2 px-4 py-2 glass-panel rounded-premium-sm text-[9px] font-black uppercase bg-primary text-white border-primary shadow-lg shadow-primary/20"
                                >
                                    <Plus className="w-3.5 h-3.5" /> Nuevo
                                </button>
                            </div>

                            {channels.length === 0 ? (
                                <div className="p-8 text-center glass-panel rounded-premium opacity-50">
                                    <p className="text-xs text-gray-400">No hay canales configurados</p>
                                </div>
                            ) : (
                                channels.map(channel => (
                                    <div key={channel.id} className={`glass-panel rounded-premium p-4 border flex items-center justify-between group transition-all ${channel.is_favorite ? 'border-yellow-500/20 bg-yellow-500/5' : 'border-white/5'}`}>
                                        <div className="flex items-center gap-4">
                                            <div className={`p-3 rounded-2xl ${channel.platform === 'telegram' ? 'bg-blue-500/10 text-blue-400' : channel.platform === 'facebook' ? 'bg-primary/10 text-primary' : 'bg-sky-500/10 text-sky-400'
                                                } shadow-inner relative`}>
                                                {channel.platform === 'telegram' ? <TelegramIcon className="w-5 h-5" /> : channel.platform === 'facebook' ? <Facebook className="w-5 h-5" /> : <Twitter className="w-5 h-5" />}
                                                {channel.is_favorite && (
                                                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full border-2 border-[#1a1b1e] shadow-sm transform rotate-12" />
                                                )}
                                            </div>
                                            <div className="flex flex-col">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs font-black uppercase tracking-wider">{channel.name}</span>
                                                    {channel.is_favorite && <span className="text-[9px] text-yellow-500/80 font-bold bg-yellow-500/10 px-1.5 py-0.5 rounded-full">FAVORITO</span>}
                                                </div>
                                                <span className="text-[10px] text-gray-500 font-medium">{channel.target_id}</span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            <button
                                                onClick={() => toggleFavorite(channel.id)}
                                                className={`p-3 min-w-[44px] min-h-[44px] flex items-center justify-center transition-colors ${channel.is_favorite ? 'text-yellow-400 hover:text-yellow-300' : 'text-gray-600 hover:text-yellow-400'}`}
                                                title={channel.is_favorite ? "Quitar de favoritos" : "Marcar como favorito"}
                                            >
                                                <Star className={`w-4 h-4 ${channel.is_favorite ? 'fill-yellow-400' : ''}`} />
                                            </button>
                                            <button
                                                onClick={() => handleEditChannel(channel)}
                                                className="p-3 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-white transition-colors"
                                            >
                                                <Edit3 className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => deleteChannel(channel.id)}
                                                className="p-3 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-red-400 transition-colors"
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
                            <div className="flex flex-col gap-3 pt-4 border-t border-white/5 animate-in fade-in slide-in-from-bottom-4 duration-700">
                                <div className="flex justify-between items-center px-1">
                                    <div className="flex items-center gap-2">
                                        <h2 className="text-xs font-black uppercase tracking-[0.2em] text-cyan-400/80">Chats Descubiertos</h2>
                                        <span className="px-1.5 py-0.5 rounded-full bg-cyan-500/10 text-[9px] font-bold text-cyan-400 border border-cyan-500/20">
                                            {discoveredChats.length}
                                        </span>
                                    </div>
                                    <span className="text-[9px] text-gray-500 uppercase font-medium">Auto-detect</span>
                                </div>

                                <div className="grid grid-cols-1 gap-2">
                                    {discoveredChats.map(chat => (
                                        <div key={chat.chat_id} className="glass-panel rounded-premium p-3 border border-white/5 flex items-center justify-between group hover:border-cyan-500/30 transition-colors">
                                            <div className="flex items-center gap-3">
                                                <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
                                                    <TelegramIcon className="w-4 h-4" />
                                                </div>
                                                <div className="flex flex-col">
                                                    <span className="text-[11px] font-bold text-gray-200">{chat.title}</span>
                                                    <div className="flex items-center gap-2 text-[9px] text-gray-500">
                                                        <span>{chat.type}</span>
                                                        <span>•</span>
                                                        <span>{chat.member_count} miembros</span>
                                                    </div>
                                                </div>
                                            </div>

                                            {chat.is_promoted ? (
                                                <span className="text-[9px] text-green-400 font-bold px-2 py-1 bg-green-500/10 rounded-full flex items-center gap-1">
                                                    <CheckCircle2 className="w-3 h-3" /> AÑADIDO
                                                </span>
                                            ) : (
                                                <button
                                                    onClick={() => promoteDiscovered(chat.chat_id, chat.title)}
                                                    className="opacity-60 group-hover:opacity-100 flex items-center justify-center gap-1.5 min-w-[44px] min-h-[44px] px-3 rounded-full bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 text-[9px] font-black uppercase tracking-wider transition-all"
                                                >
                                                    Agregar <Plus className="w-3 h-3" />
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
                    <div className="flex flex-col gap-3">
                        <div className="flex justify-between items-center px-1">
                            <div className="flex gap-2">
                                <button
                                    onClick={() => restoreTemplates('telegram')}
                                    className="min-h-[44px] flex items-center gap-2 px-3 py-1.5 glass-panel rounded-premium-sm text-[9px] font-black uppercase text-gray-400 hover:text-white border-white/5 hover:bg-white/5 transition-all"
                                    title="Restaurar todas las plantillas de Telegram a sus valores por defecto"
                                >
                                    <RefreshCw className="w-3 h-3" /> Restaurar
                                </button>
                                <button
                                    onClick={handleCreateTemplate}
                                    className="min-h-[44px] flex items-center gap-2 px-3 py-1.5 glass-panel rounded-premium-sm text-[9px] font-black uppercase bg-primary text-white border-primary shadow-lg shadow-primary/20"
                                >
                                    <Plus className="w-3.5 h-3.5" /> Nueva
                                </button>
                            </div>
                        </div>

                        {templates.map(template => (
                            <div key={template.id} className={`glass-panel rounded-premium p-4 border transition-all flex flex-col gap-3 group ${
                                template.is_default 
                                    ? 'border-primary/50 bg-primary/5 shadow-lg shadow-primary/5' 
                                    : 'border-white/5'
                            }`}>
                                <div className="flex justify-between items-center">
                                    <div className="flex items-center gap-2">
                                        <Type className={`w-4 h-4 ${template.is_default ? 'text-primary' : 'text-gray-400'}`} />
                                        <span className="text-xs font-black uppercase tracking-wider text-white">{template.name}</span>
                                        {template.is_default && (
                                            <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-[9px] font-black uppercase tracking-wider text-emerald-400">
                                                Activa / Principal
                                            </span>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {template.extra_config?.type && template.extra_config.type !== 'general' && (
                                            <div className="px-2 py-0.5 rounded-full bg-primary/20 border border-primary/30 text-[9px] font-black uppercase tracking-wider text-primary">
                                                {template.extra_config.type === 'cover' ? 'Envío: Portada' :
                                                 template.extra_config.type === 'synopsis' ? 'Envío: Sinopsis' :
                                                 template.extra_config.type === 'info' ? 'Envío: Info' :
                                                 template.extra_config.type === 'unified' ? 'Envío: Unificado' :
                                                 template.extra_config.type}
                                            </div>
                                        )}
                                        <div className="px-2 py-0.5 rounded-full bg-white/5 text-[9px] font-black uppercase tracking-wider text-gray-400">
                                            {template.platform}
                                        </div>

                                        {/* Switch para marcar como Plantilla Predeterminada / Activa */}
                                        <button
                                            onClick={async (e) => {
                                                e.stopPropagation();
                                                try {
                                                    await saveTemplate({
                                                        id: template.id,
                                                        name: template.name,
                                                        content: template.content,
                                                        platform: template.platform,
                                                        extra_config: template.extra_config,
                                                        is_default: !template.is_default,
                                                    } as any);
                                                    webApp?.HapticFeedback?.impactOccurred('medium');
                                                } catch (err) {
                                                    console.error("Error setting default template", err);
                                                }
                                            }}
                                            className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                                                template.is_default ? 'bg-primary' : 'bg-white/10 hover:bg-white/20'
                                            }`}
                                            title={template.is_default ? 'Plantilla activa por defecto (Toca para desactivar)' : 'Toca para activar como plantilla por defecto'}
                                        >
                                            <span
                                                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                                                    template.is_default ? 'translate-x-4' : 'translate-x-0'
                                                }`}
                                            />
                                        </button>
                                    </div>
                                </div>
                                <div
                                    className="p-3 bg-black/20 rounded-premium-sm text-[10px] text-gray-300 leading-relaxed italic whitespace-pre-line border border-white/5 line-clamp-3 prose prose-invert max-w-none"
                                    dangerouslySetInnerHTML={{ __html: template.content }}
                                />
                                <div className="flex justify-end gap-1 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={() => handleEditTemplate(template)}
                                        className="p-3 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-white transition-colors"
                                        title="Editar Plantilla"
                                    >
                                        <Edit3 className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => deleteTemplate(template.id)}
                                        className="p-3 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-red-400 transition-colors"
                                        title="Eliminar Plantilla"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {activeTab === 'workgroups' && (
                    <div className="flex flex-col gap-3">
                        <div className="flex justify-between items-center px-1">
                            <div>
                                <h2 className="text-xs font-black uppercase tracking-[0.2em] text-primary/80">Grupos Traductores / Fansubs</h2>
                                <p className="text-[11px] text-gray-400">Gestiona los enlaces oficiales a sus redes que se inyectan en tus publicaciones</p>
                            </div>
                            <button
                                onClick={() => {
                                    setEditingWorkgroup(null);
                                    setIsWorkgroupModalOpen(true);
                                }}
                                className="px-4 py-2 bg-primary hover:brightness-110 text-white rounded-premium text-xs font-bold shadow-lg shadow-primary/20 flex items-center gap-1.5 active:scale-95 transition-all"
                            >
                                <Plus className="w-4 h-4" />
                                <span>Nuevo Grupo</span>
                            </button>
                        </div>

                        {workgroups.length === 0 ? (
                            <div className="glass-panel rounded-premium p-10 flex flex-col items-center gap-3 text-center">
                                <div className="p-4 rounded-full bg-white/5 text-primary">
                                    <Building2 className="w-8 h-8" />
                                </div>
                                <div>
                                    <h3 className="text-sm font-bold text-white mb-1">No hay grupos traductores registrados</h3>
                                    <p className="text-xs text-gray-400 max-w-xs mx-auto">
                                        Registra tus fansubs favoritos para vincular sus redes sociales (Web, Facebook, Discord, Patreon) en tus posts automáticos.
                                    </p>
                                </div>
                                <button
                                    onClick={() => {
                                        setEditingWorkgroup(null);
                                        setIsWorkgroupModalOpen(true);
                                    }}
                                    className="mt-2 px-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 rounded-premium text-xs font-semibold flex items-center gap-2 transition-all"
                                >
                                    <Plus className="w-4 h-4" />
                                    <span>Crear Primer Grupo</span>
                                </button>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {workgroups.map((group) => (
                                    <div
                                        key={group.id}
                                        onClick={() => navigate(`/app-v2/fansubs/${group.id}`)}
                                        className="glass-panel rounded-premium p-4 flex flex-col justify-between gap-3 border border-white/5 hover:border-primary/50 hover:bg-white/[0.04] transition-all group cursor-pointer"
                                    >
                                        <div className="flex flex-col gap-2">
                                            <div className="flex justify-between items-start">
                                                <div className="flex items-center gap-2.5">
                                                    <div className="p-2 rounded-xl bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-all">
                                                        <Building2 className="w-4 h-4" />
                                                    </div>
                                                    <div>
                                                        <div className="flex items-center gap-2">
                                                            <h3 className="text-xs font-bold text-white group-hover:text-primary transition-colors">{group.name}</h3>
                                                            {group.siglas && (
                                                                <span className="px-2 py-0.5 rounded-full bg-white/10 text-[9px] font-bold text-gray-300">
                                                                    {group.siglas}
                                                                </span>
                                                            )}
                                                        </div>
                                                        {group.description && (
                                                            <p className="text-[11px] text-gray-400 line-clamp-1 mt-0.5">
                                                                {group.description}
                                                            </p>
                                                        )}
                                                    </div>
                                                </div>

                                                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                                                    <button
                                                        onClick={() => navigate(`/app-v2/fansubs/${group.id}`)}
                                                        className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all"
                                                        title="Ver y Editar Fansub"
                                                    >
                                                        <Edit3 className="w-3.5 h-3.5" />
                                                    </button>
                                                    <button
                                                        onClick={() => deleteWorkgroup(group.id)}
                                                        className="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
                                                        title="Eliminar Grupo"
                                                    >
                                                        <Trash2 className="w-3.5 h-3.5" />
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Links Badges */}
                                            <div className="flex flex-wrap gap-1.5 pt-1">
                                                {group.links?.web && (
                                                    <a
                                                        href={group.links.web}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="px-2 py-1 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 text-[10px] font-semibold flex items-center gap-1 transition-all"
                                                    >
                                                        <Globe className="w-3 h-3" /> Web
                                                    </a>
                                                )}
                                                {group.links?.fb && (
                                                    <a
                                                        href={group.links.fb}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="px-2 py-1 rounded-lg bg-blue-600/10 hover:bg-blue-600/20 text-blue-300 text-[10px] font-semibold flex items-center gap-1 transition-all"
                                                    >
                                                        <Facebook className="w-3 h-3" /> Facebook
                                                    </a>
                                                )}
                                                {group.links?.discord && (
                                                    <a
                                                        href={group.links.discord}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="px-2 py-1 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 text-[10px] font-semibold flex items-center gap-1 transition-all"
                                                    >
                                                        <MessageSquare className="w-3 h-3" /> Discord
                                                    </a>
                                                )}
                                                {group.links?.patreon && (
                                                    <a
                                                        href={group.links.patreon}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="px-2 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-300 text-[10px] font-semibold flex items-center gap-1 transition-all"
                                                    >
                                                        <Heart className="w-3 h-3" /> Patreon
                                                    </a>
                                                )}
                                                {group.links?.twitter && (
                                                    <a
                                                        href={group.links.twitter}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="px-2 py-1 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 text-[10px] font-semibold flex items-center gap-1 transition-all"
                                                    >
                                                        <Twitter className="w-3 h-3" /> Twitter
                                                    </a>
                                                )}
                                                {group.links?.donations && (
                                                    <a
                                                        href={group.links.donations}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="px-2 py-1 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-[10px] font-semibold flex items-center gap-1 transition-all"
                                                    >
                                                        <Coffee className="w-3 h-3" /> Donar
                                                    </a>
                                                )}
                                                {!Object.values(group.links || {}).some(Boolean) && (
                                                    <span className="text-[10px] text-gray-500 italic">Sin enlaces registrados</span>
                                                )}
                                            </div>
                                        </div>

                                        <div className="flex justify-between items-center pt-2 border-t border-white/5 text-[10px] text-gray-400">
                                            <span className="flex items-center gap-1">
                                                <BookOpen className="w-3 h-3 text-primary" /> {group.books_count} libros asociados
                                            </span>
                                            <span>ID: {group.id}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
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

            <WorkgroupModal
                isOpen={isWorkgroupModalOpen}
                onClose={() => setIsWorkgroupModalOpen(false)}
                onSave={saveWorkgroup}
                onDelete={deleteWorkgroup}
                group={editingWorkgroup}
            />
        </div>
    );
};
