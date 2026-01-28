import React, { useState, useEffect, useMemo } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import {
   ArrowUp,
   Star,
   Calendar,
   Clock,
   Download
} from 'lucide-react';
import { preloadImages } from '../src/utils/imagePreloader';
import { api } from '../src/services/api';

// Modular Components
import { LibraryHeader } from '../components/library/LibraryHeader';
import { LibraryCard } from '../components/library/LibraryCard';
import { EmptyLibrary } from '../components/library/EmptyLibrary';
import { LibrarySortBar } from '../components/library/LibrarySortBar';

interface LibraryProps {
   onNavigate?: (tab: string) => void;
   onSelectBook?: (title: string, author: string, cover: string) => void;
}

export const Library: React.FC<LibraryProps> = ({ onNavigate, onSelectBook }) => {
   const { settings } = useTheme();
   const [isSortMenuOpen, setIsSortMenuOpen] = useState(false);
   const [activeSort, setActiveSort] = useState('a-z');
   const [libraryBooks, setLibraryBooks] = useState<any[]>([]);
   const [loading, setLoading] = useState(true);

   const sortOptions = [
      { id: 'a-z', label: 'A-Z', icon: ArrowUp },
      { id: 'z-a', label: 'Z-A', icon: ArrowUp },
      { id: 'downloads', label: 'DESCARGAS', icon: Download },
      { id: 'rating', label: 'VALORACIÓN', icon: Star },
      { id: 'added', label: 'AÑADIDO', icon: Calendar },
      { id: 'updated', label: 'ACTUALIZADO', icon: Clock },
   ];

   useEffect(() => {
      const fetchLibrary = async () => {
         try {
            const res = await api.getDownloadHistory();
            const history = res?.downloads || [];
            const books = history.map((item: any) => ({
               id: item.id,
               title: item.title,
               author: item.book?.author || item.volume?.author || 'Autor desconocido',
               vol: item.volume?.volumeNumber || item.volume?.vol || '?',
               time: item.timeAgo || 'Hace poco',
               cover: item.book?.coverUrl || item.volume?.coverUrl || item.volume?.cover || '/api/library/covers/default.jpg',
               isNew: false,
               updated: false
            }));
            setLibraryBooks(books);
            if (books.length > 0) {
               preloadImages(books.map((b: any) => b.cover));
            }
         } catch (error) {
            console.error("Error fetching library:", error);
         } finally {
            setLoading(false);
         }
      };
      fetchLibrary();
   }, []);

   const sortedBooks = useMemo(() => {
      const sorted = [...libraryBooks];
      if (activeSort === 'a-z') return sorted.sort((a, b) => (a.title || '').localeCompare(b.title || '', undefined, { numeric: true, sensitivity: 'base' }));
      if (activeSort === 'z-a') return sorted.sort((a, b) => (b.title || '').localeCompare(a.title || '', undefined, { numeric: true, sensitivity: 'base' }));
      return sorted;
   }, [libraryBooks, activeSort]);

   return (
      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-4 animate-in fade-in duration-500 pb-28">
         <LibraryHeader />

         {/* Filter Chips (Quick Filters) */}
         <div className="flex flex-wrap gap-2 mb-12">
            <button className="h-10 px-6 rounded-full bg-primary text-white text-[11px] font-black uppercase tracking-[0.2em] shadow-[0_10px_20px_-5px_rgba(var(--color-primary-rgb),0.5)] active:scale-95 transition-all">
               Todas
            </button>
            <button className="h-10 px-6 rounded-full bg-white/[0.03] border border-white/5 hover:bg-white/10 text-gray-400 hover:text-white text-[11px] font-black uppercase tracking-[0.2em] transition-all flex items-center gap-3">
               Actualizadas
               <span className="flex h-5 w-5 items-center justify-center rounded-lg bg-primary text-[9px] font-black text-white shadow-lg">1</span>
            </button>
            <button className="h-10 px-6 rounded-full bg-white/[0.03] border border-white/5 hover:bg-white/10 text-gray-400 hover:text-white text-[11px] font-black uppercase tracking-[0.2em] transition-all">
               Completadas
            </button>
         </div>

         {!loading && libraryBooks.length > 0 ? (
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 mb-12">
               {sortedBooks.map((book) => (
                  <LibraryCard
                     key={book.id}
                     book={book}
                     onClick={() => onSelectBook && onSelectBook(book.title, book.author, book.cover)}
                  />
               ))}
            </div>
         ) : !loading ? (
            <EmptyLibrary onGoToCatalog={() => onNavigate && onNavigate('search')} />
         ) : (
            <div className="flex justify-center py-20">
               <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
            </div>
         )}

         <LibrarySortBar
            onNavigate={(tab) => onNavigate && onNavigate(tab)}
            isSortMenuOpen={isSortMenuOpen}
            setIsSortMenuOpen={setIsSortMenuOpen}
            activeSort={activeSort}
            setActiveSort={setActiveSort}
            sortOptions={sortOptions}
            settings={settings}
         />
      </div>
   );
};
