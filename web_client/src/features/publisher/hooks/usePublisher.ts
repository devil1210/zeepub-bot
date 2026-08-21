import { useState, useEffect, useCallback } from 'react';
import { publisherApi, PublicationQueueItem, PublicationChannel, PublicationTemplate, DiscoveredChat } from '../services/publisherApi';
import { workgroupsApi, TranslatorsGroupItem, GroupContactLinks } from '../services/workgroupsApi';

export const usePublisher = () => {
    const [queue, setQueue] = useState<PublicationQueueItem[]>([]);
    const [channels, setChannels] = useState<PublicationChannel[]>([]);
    const [discoveredChats, setDiscoveredChats] = useState<DiscoveredChat[]>([]);
    const [templates, setTemplates] = useState<PublicationTemplate[]>([]);
    const [workgroups, setWorkgroups] = useState<TranslatorsGroupItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            console.log("Fetching publisher data...");
            const [qRes, cRes, tRes, wRes] = await Promise.all([
                publisherApi.getQueue(),
                publisherApi.getChannels(),
                publisherApi.getTemplates(),
                workgroupsApi.getAll().catch(() => [])
            ]);

            console.log("Publisher data received:", { qRes, cRes, tRes, wRes });

            setQueue(qRes.items || []);

            // cRes now returns { channels: [], discovered: [] }
            setChannels(cRes.channels || []);
            setDiscoveredChats(cRes.discovered || []);

            setTemplates(tRes.templates || []);
            setWorkgroups(wRes || []);
        } catch (err: any) {
            console.error("Error fetching publisher data:", err);
            setError(err.message || 'Error fetching publisher data');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const schedulePublication = async (data: any) => {
        const res = await publisherApi.schedulePublication(data);
        if (res.success) await fetchData();
        return res;
    };

    const updateQueueItem = async (data: any) => {
        const res = await publisherApi.updateQueueItem(data);
        if (res.success) await fetchData();
        return res;
    };

    const deleteQueueItem = async (id: number) => {
        if (!window.confirm('¿Estás seguro de eliminar esta publicación de la cola?')) return;
        const res = await publisherApi.deleteQueueItem(id);
        if (res.success) await fetchData();
        return res;
    };

    const saveChannel = async (channel: Partial<PublicationChannel>) => {
        const res = await publisherApi.saveChannel(channel);
        if (res.success) await fetchData();
        return res;
    };

    const toggleFavorite = async (id: number) => {
        const res = await publisherApi.toggleFavorite(id);
        if (res.success) await fetchData();
        return res;
    };

    const promoteDiscovered = async (chatId: string, name: string) => {
        const res = await publisherApi.promoteDiscovered(chatId, name);
        if (res.success) await fetchData();
        return res;
    };

    const saveTemplate = async (template: Partial<PublicationTemplate>) => {
        const res = await publisherApi.saveTemplate(template);
        if (res.success) await fetchData();
        return res;
    };

    const deleteTemplate = async (id: number) => {
        if (!window.confirm('¿Estás seguro de eliminar esta plantilla?')) return;
        const res = await publisherApi.deleteTemplate(id);
        if (res.success) await fetchData();
        return res;
    };

    const saveWorkgroup = async (group: {
        id?: number;
        name: string;
        siglas?: string;
        description?: string;
        links: GroupContactLinks;
    }) => {
        const res = await workgroupsApi.save(group);
        if (res.success) await fetchData();
        return res;
    };

    const deleteWorkgroup = async (id: number) => {
        const res = await workgroupsApi.delete(id);
        if (res.success) await fetchData();
        return res;
    };

    return {
        queue,
        channels,
        discoveredChats,
        templates,
        workgroups,
        loading,
        error,
        refresh: fetchData,
        schedulePublication,
        updateQueueItem,
        deleteQueueItem,
        saveChannel,
        deleteChannel: async (id: number) => {
            if (!window.confirm('¿Estás seguro de eliminar este canal?')) return;
            const res = await publisherApi.deleteChannel(id);
            if (res.success) await fetchData();
            return res;
        },
        toggleFavorite,
        promoteDiscovered,
        saveTemplate,
        deleteTemplate,
        saveWorkgroup,
        deleteWorkgroup,
        restoreTemplates: async (platform: string = 'telegram') => {
            if (!window.confirm('¿Estás seguro de restaurar todas las plantillas por defecto? Se perderán los cambios personalizados.')) return;
            const res = await publisherApi.restoreTemplates(platform);
            if (res.success) await fetchData();
            return res;
        }
    };
};
