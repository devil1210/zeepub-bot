import { useState, useEffect, useCallback } from 'react';
import { publisherApi, PublicationQueueItem, PublicationChannel, PublicationTemplate } from '../services/publisherApi';

export const usePublisher = () => {
    const [queue, setQueue] = useState<PublicationQueueItem[]>([]);
    const [channels, setChannels] = useState<PublicationChannel[]>([]);
    const [templates, setTemplates] = useState<PublicationTemplate[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        try {
            const [qRes, cRes, tRes] = await Promise.all([
                publisherApi.getQueue(),
                publisherApi.getChannels(),
                publisherApi.getTemplates()
            ]);
            setQueue(qRes.items || []);
            setChannels(cRes.channels || []);
            setTemplates(tRes.templates || []);
        } catch (err: any) {
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

    const saveTemplate = async (template: Partial<PublicationTemplate>) => {
        const res = await publisherApi.saveTemplate(template);
        if (res.success) await fetchData();
        return res;
    };

    return {
        queue,
        channels,
        templates,
        loading,
        error,
        refresh: fetchData,
        schedulePublication,
        deleteQueueItem,
        saveChannel,
        saveTemplate
    };
};
