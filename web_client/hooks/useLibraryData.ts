import useSWR from 'swr';
import { api } from '../src/services/api';
import { preloadImages } from '../src/utils/imagePreloader';

const KEY = 'library/all';

export const useLibraryData = () => {
    const { data, error, mutate } = useSWR(KEY, async () => {
        try {
            // Assuming getDownloadHistory returns the user's library
            // If there's a specific getLibrary API it should be used, but Library.tsx used getDownloadHistory
            const res = await api.getDownloadHistory();
            const history = res?.downloads || [];
            const books = history.map((item: any) => ({
                id: item.book_id ? `local_${item.book_id}` : (item.book_hash || item.id),
                title: item.title,
                author: item.author || 'Autor desconocido',
                vol: item.volume || '?',
                time: item.timeAgo || 'Hace poco',
                cover: item.cover || item.coverUrl || item.cover_medium || item.cover_low || `/api/library/covers/default.jpg`,
                isNew: false,
                updated: false
            }));

            // Preload first few images
            if (books.length > 0) {
                preloadImages(books.slice(0, 20).map((b: any) => b.cover));
            }

            return books;
        } catch (e) {
            console.error("Library fetch error", e);
            throw e;
        }
    }, {
        dedupingInterval: 60000,
        revalidateOnFocus: true
    });

    return {
        books: data || [],
        loading: !data && !error,
        error,
        mutate
    };
};
