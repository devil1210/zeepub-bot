import React, { useState, useMemo } from 'react';
import { useTheme } from '@shared/contexts/ThemeContext';
import {
   ArrowUp,
   Star,
   Calendar,
   Clock,
   Download
} from 'lucide-react';
import { VList } from 'virtua';
import { useLibraryData } from '../hooks/useLibraryData';
import { useResponsiveColumns } from '@shared/hooks/useResponsiveColumns';

// Modular Components
import { LibraryHeader } from '../components/LibraryHeader';
import { LibraryCard } from '../components/LibraryCard';
import { EmptyLibrary } from '../components/EmptyLibrary';
import { LibrarySortBar } from '../components/LibrarySortBar';

interface LibraryProps {
   onNavigate?: (tab: string) => void;
   onSelectBook?: (bookId: string) => void;
}

const chunkArray = <T,>(array: T[], size: number): T[][] => {
   const chunked: T[][] = [];
   for (let i = 0; i < array.length; i += size) {
      chunked.push(array.slice(i, i + size));
   }
   return chunked;
};

export const Library: React.FC<LibraryProps> = ({ onNavigate, onSelectBook }) => {
   const { settings } = useTheme();
   const [isSortMenuOpen, setIsSortMenuOpen] = useState(false);
   const [activeSort, setActiveSort] = useState('a-z');

   // Hook magic
   const { books: libraryBooks, loading } = useLibraryData();
   const columns = useResponsiveColumns();

   const sortOptions = [
      { id: 'a-z', label: 'A-Z', icon: ArrowUp },
      { id: 'z-a', label: 'Z-A', icon: ArrowUp },
      { id: 'downloads', label: 'DESCARGAS', icon: Download },
      { id: 'rating', label: 'VALORACIÓN', icon: Star },
      { id: 'added', label: 'AÑADIDO', icon: Calendar },
      { id: 'updated', label: 'ACTUALIZADO', icon: Clock },
   ];

   const sortedBooks = useMemo(() => {
      const sorted = [...libraryBooks];
      if (activeSort === 'a-z') return sorted.sort((a, b) => (a.title || '').localeCompare(b.title || '', undefined, { numeric: true, sensitivity: 'base' }));
      if (activeSort === 'z-a') return sorted.sort((a, b) => (b.title || '').localeCompare(a.title || '', undefined, { numeric: true, sensitivity: 'base' }));
      return sorted;
   }, [libraryBooks, activeSort]);

   const rows = useMemo(() => chunkArray(sortedBooks, columns), [sortedBooks, columns]);

   return (
      <div className="h-full flex flex-col max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-4 animate-in fade-in duration-500">
         <div className="shrink-0 z-10 bg-[var(--app-bg)] pb-4">
            <LibraryHeader />

            {/* Filter Chips (Quick Filters) */}
            <div className="flex flex-wrap gap-2 mb-2">
               <button className="h-10 px-6 rounded-premium-full bg-primary text-white text-[11px] font-black uppercase tracking-[0.2em] shadow-premium active:scale-95 transition-all">
                  Todas
               </button>
               <button className="h-10 px-6 rounded-premium-full bg-white/5 border border-white/5 hover:bg-white/10 text-gray-400 hover:text-white text-[11px] font-black uppercase tracking-[0.2em] transition-all flex items-center gap-3">
                  Actualizadas
                  <span className="flex h-5 w-5 items-center justify-center rounded-premium-sm bg-primary text-[9px] font-black text-white shadow-lg">1</span>
               </button>
               <button className="h-10 px-6 rounded-premium-full bg-white/5 border border-white/5 hover:bg-white/10 text-gray-400 hover:text-white text-[11px] font-black uppercase tracking-[0.2em] transition-all">
                  Completadas
               </button>
            </div>
         </div>

         <div className="flex-1 min-h-0 relative">
            {!loading && libraryBooks.length > 0 ? (
               <VList style={{ height: '100%' }}>
                  {rows.map((row, rowIndex) => (
                     <div key={rowIndex} className="grid gap-6 mb-6" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
                        {row.map((book) => (
                           <LibraryCard
                              key={book.id}
                              book={book}
                              onClick={() => onSelectBook && onSelectBook(book.id)}
                           />
                        ))}
                        {/* Filler divs to keep grid alignment in last row */}
                        {Array.from({ length: columns - row.length }).map((_, i) => (
                           <div key={`empty-${i}`} />
                        ))}
                     </div>
                  ))}
               </VList>
            ) : !loading ? (
               <EmptyLibrary onGoToCatalog={() => onNavigate && onNavigate('search')} />
            ) : (
               <div className="flex justify-center py-20">
                  <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-premium-full animate-spin"></div>
               </div>
            )}
         </div>

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
