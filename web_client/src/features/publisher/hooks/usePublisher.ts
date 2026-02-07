import { useState, useEffect, useCallback } from 'react';
import { publisherApi, PublicationQueueItem, PublicationChannel, PublicationTemplate, DiscoveredChat } from '../services/publisherApi';

export const usePublisher = () => {
    const [queue, setQueue] = useState<PublicationQueueItem[]>([]);
    const [channels, setChannels] = useState<PublicationChannel[]>([]);
    const [discoveredChats, setDiscoveredChats] = useState<DiscoveredChat[]>([]);
    const [templates, setTemplates] = useState<PublicationTemplate[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            console.log("Fetching publisher data...");
            const [qRes, cRes, tRes] = await Promise.all([
                publisherApi.getQueue(),
                publisherApi.getChannels(),
                publisherApi.getTemplates()
            ]);

            console.log("Publisher data received:", { qRes, cRes, tRes });

            setQueue(qRes.items || []);

            // cRes now returns { channels: [], discovered: [] }
            setChannels(cRes.channels || []);
            setDiscoveredChats(cRes.discovered || []);

            setTemplates(tRes.templates || []);
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
        const res = await publisherApi.schedule(data);
        if (res.success) await fetchData();
        return res;
    };

    const deleteQueueItem = async (id: number) => {
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

    return {
        queue,
        channels,
        discoveredChats,
        templates,
        loading,
        error,
        refresh: fetchData,
        schedulePublication,
        deleteQueueItem,
        saveChannel,
        toggleFavorite,
        promoteDiscovered,
        saveTemplate
    };
};
