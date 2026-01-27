import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import {
   Bell,
   Send,
   SlidersHorizontal,
   Home,
   ArrowDownUp,
   Filter,
   ArrowUp,
   Star,
   Calendar,
   Clock,
   Download
} from 'lucide-react';
import { preloadImages } from '../src/utils/imagePreloader';
import { api } from '../src/services/api';

interface LibraryProps {
   onNavigate?: (tab: string) => void;
   onSelectBook?: (title: string, author: string, cover: string) => void;
}

export const Library: React.FC<LibraryProps> = ({ onNavigate, onSelectBook }) => {
   const { settings } = useTheme();
   const [isSortMenuOpen, setIsSortMenuOpen] = React.useState(false);
   const [activeSort, setActiveSort] = React.useState('a-z');

   const sortOptions = [
      { id: 'a-z', label: 'A-Z', icon: ArrowUp },
      { id: 'z-a', label: 'Z-A', icon: ArrowUp },
      { id: 'downloads', label: 'DESCARGAS', icon: Download },
      { id: 'rating', label: 'VALORACIÓN', icon: Star },
      { id: 'added', label: 'AÑADIDO', icon: Calendar },
      { id: 'updated', label: 'ACTUALIZADO', icon: Clock },
   ];

   const [libraryBooks, setLibraryBooks] = React.useState<any[]>([]);
   const [loading, setLoading] = React.useState(true);

   React.useEffect(() => {
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

   const sortedBooks = React.useMemo(() => {
      const sorted = [...libraryBooks];
      if (activeSort === 'a-z') return sorted.sort((a, b) => (a.title || '').localeCompare(b.title || '', undefined, { numeric: true, sensitivity: 'base' }));
      if (activeSort === 'z-a') return sorted.sort((a, b) => (b.title || '').localeCompare(a.title || '', undefined, { numeric: true, sensitivity: 'base' }));
      return sorted;
   }, [libraryBooks, activeSort]);

   return (
      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-4 animate-in fade-in duration-500 pb-28">

         {/* Page Header */}
         <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between mb-12">
            <div>
               <h1 className="text-5xl font-black tracking-tighter text-white mb-3">Mi Biblioteca</h1>
               <p className="text-gray-500 font-medium tracking-wide">Gestiona tu colección y sigue tus lecturas.</p>
            </div>
            {/* Filter Chips */}
            <div className="flex flex-wrap gap-2">
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
         </div>

         {/* Grid Section */}
         {!loading && libraryBooks.length > 0 ? (
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 mb-12">
               {sortedBooks.map((book) => (
                  <div
                     key={book.id}
                     onClick={() => onSelectBook && onSelectBook(book.title, book.author, book.cover)}
                     className={`group relative flex flex-col gap-4 rounded-[2.5rem] p-4 transition-all duration-700 glass-panel hover:bg-white/[0.08] hover:border-primary/40 hover:-translate-y-2 cursor-pointer shadow-premium ${book.isNew ? 'border-primary/30 ring-1 ring-primary/20' : ''}`}
                  >
                     {/* Status Badges */}
                     <div className="absolute top-6 right-6 z-20 flex flex-col gap-2">
                        {book.isNew && (
                           <div className="bg-primary text-white px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest shadow-xl animate-pulse">
                              Nuevo
                           </div>
                        )}
                        {book.updated && (
                           <div className="bg-emerald-500 text-white px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest shadow-xl">
                              Upd
                           </div>
                        )}
                     </div>

                     {/* Image Container */}
                     <div className="relative aspect-[2/3] w-full overflow-hidden rounded-[1.75rem] bg-white/5 shadow-2xl border border-white/10">
                        <div
                           className="absolute inset-0 bg-cover bg-center transition-all duration-1000 group-hover:scale-110 grayscale-[30%] group-hover:grayscale-0"
                           style={{ backgroundImage: `url("${book.cover}")` }}
                        ></div>

                        {/* Modern Multi-Layer Gradient */}
                        <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black via-black/40 to-transparent"></div>

                        {/* Pulsing Notification */}
                        {book.updated && (
                           <div className="absolute bottom-4 left-4 flex items-center gap-2">
                              <div className="relative flex h-3 w-3">
                                 <div className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></div>
                                 <div className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></div>
                              </div>
                              <span className="text-[10px] font-black text-white uppercase tracking-[0.2em] drop-shadow-md">Updated</span>
                           </div>
                        )}
                     </div>

                     {/* Content */}
                     <div className="flex flex-col gap-1 px-1">
                        <h3 className="truncate text-[15px] font-black text-white group-hover:text-primary transition-colors tracking-tight">{book.title}</h3>
                        <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-gray-500">
                           <span>Vol {book.vol}</span>
                           <span className="opacity-50">{book.time}</span>
                        </div>
                     </div>

                     {/* Hover Accent Glow */}
                     <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
                  </div>
               ))}
            </div>
         ) : !loading ? (
            <div className="glass-panel rounded-[2.5rem] p-12 text-center border border-white/5 flex flex-col items-center justify-center gap-6 mb-12">
               <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center text-gray-500">
                  <Download className="w-10 h-10" />
               </div>
               <div>
                  <h2 className="text-xl font-bold text-white mb-2">Biblioteca vacía</h2>
                  <p className="text-gray-400 max-w-xs mx-auto text-sm">Explora el catálogo y descarga libros para verlos aquí.</p>
               </div>
               <button
                  onClick={() => onNavigate && onNavigate('search')}
                  className="px-8 py-3 bg-primary hover:bg-primary-dark text-white rounded-premium-sm text-xs font-black uppercase tracking-widest transition-all"
               >
                  IR AL CATÁLOGO
               </button>
            </div>
         ) : (
            <div className="flex justify-center py-20">
               <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
            </div>
         )}

         {/* Floating Bottom Action Bar (Same style as Catalog) */}
         <div className="md:hidden fixed bottom-6 left-8 right-8 z-40 animate-in slide-in-from-bottom-4 duration-300 flex flex-col gap-3 max-w-5xl mx-auto">
            {isSortMenuOpen && (
               <div
                  className="glass-panel rounded-premium p-3 border border-white/10 shadow-2xl animate-in slide-in-from-bottom-2 fade-in duration-200"
                  style={{
                     background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                     backdropFilter: `blur(${settings.glassBlur}px)`,
                     WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
                  }}
               >
                  <div className="grid grid-cols-3 gap-2">
                     {sortOptions.map((option) => {
                        const isActive = activeSort === option.id;
                        return (
                           <button
                              key={option.id}
                              onClick={() => {
                                 setActiveSort(option.id);
                                 setIsSortMenuOpen(false);
                              }}
                              className={`flex flex-col items-center gap-1 px-2 py-2.5 rounded-premium-sm text-[9px] font-black uppercase tracking-widest transition-all border ${isActive
                                 ? 'bg-primary text-white border-primary shadow-lg shadow-blue-500/20'
                                 : 'bg-white/5 text-gray-400 border-transparent hover:bg-white/10 hover:text-white'
                                 }`}
                           >
                              {option.icon && <option.icon className={`w-4 h-4 ${option.id === 'z-a' ? 'rotate-180' : ''}`} />}
                              <span className="text-center leading-tight">{option.label}</span>
                           </button>
                        );
                     })}
                  </div>
               </div>
            )}

            <div
               className="glass-panel rounded-premium p-1 border border-black/10 dark:border-white/10 shadow-2xl flex items-center justify-between overflow-hidden"
               style={{
                  background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                  backdropFilter: `blur(${settings.glassBlur}px)`,
                  WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
               }}
            >
               {/* Home/Back */}
               <button
                  onClick={() => onNavigate && onNavigate('dashboard')}
                  className="flex-1 flex flex-col items-center justify-center py-2 rounded-premium-sm transition-all duration-300 text-gray-500 hover:text-black dark:hover:text-white"
               >
                  <div className="p-1.5 rounded-full transition-all duration-300">
                     <Home className="w-4 h-4" strokeWidth={2} />
                  </div>
                  <span className="text-[9px] font-black uppercase tracking-widest mt-1">Inicio</span>
               </button>

               <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

               {/* Sort Toggle */}
               <button
                  onClick={() => setIsSortMenuOpen(!isSortMenuOpen)}
                  className={`flex-1 flex flex-col items-center justify-center py-2 rounded-premium-sm transition-all duration-300 relative z-10 ${isSortMenuOpen ? 'text-black dark:text-white' : 'text-gray-500 hover:text-black dark:hover:text-white'}`}
               >
                  <div className={`p-1.5 rounded-full transition-all duration-300 ${isSortMenuOpen ? 'bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)] translate-y-[-2px]' : ''}`}>
                     <ArrowDownUp className={`w-4 h-4 ${isSortMenuOpen ? 'text-white' : ''}`} strokeWidth={isSortMenuOpen ? 2.5 : 2} />
                  </div>
                  <span className="text-[9px] font-black uppercase tracking-widest mt-1">Ordenar</span>
               </button>

               <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

               {/* Filter Toggle */}
               <button
                  className="flex-1 flex flex-col items-center justify-center py-2 rounded-premium-sm transition-all duration-300 text-gray-500 hover:text-black dark:hover:text-white"
               >
                  <div className="p-1.5 rounded-full transition-all duration-300">
                     <Filter className="w-4 h-4" strokeWidth={2} />
                  </div>
                  <span className="text-[9px] font-black uppercase tracking-widest mt-1">Filtrar</span>
               </button>
            </div>
         </div>

      </div>
   );
};
