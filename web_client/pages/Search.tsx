import React, { useState, useRef, useEffect } from 'react';
import {
  Search as SearchIcon,
  Filter,
  Star,
  Download,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ArrowUp,
  ArrowDownUp,
  Calendar,
  Clock,
  Check,
  LayoutGrid,
  List,
  Book,
  Hash,
  Home,
  PlusCircle
} from 'lucide-react';
import { Series } from '../types';
import { SearchScopeModal } from '../components/SearchScopeModal';
import { api } from '../src/services/api';

interface SearchProps {
  onSelectSeries: (series: Series) => void;
  onNavigate?: (tab: string) => void;
}

export const Search: React.FC<SearchProps> = ({ onSelectSeries, onNavigate }) => {
  const [isSortMenuOpen, setIsSortMenuOpen] = useState(false);
  const [isScopeModalOpen, setIsScopeModalOpen] = useState(false);
  const [activeSort, setActiveSort] = useState('a-z');
  const [selectedScope, setSelectedScope] = useState('TODOS');
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [searchTerm, setSearchTerm] = useState('');

  // Data State
  const [series, setSeries] = useState<Series[]>([]);
  const [loading, setLoading] = useState(false);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalResults, setTotalResults] = useState(0);

  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Perform Search
  const doSearch = async (query: string, page: number) => {
    setLoading(true);
    try {
      // If query is empty, we might want to show "Recent" or nothing.
      // For now let's search empty string which backend might handle as "all" or specific logic
      const res = await api.searchBooks(query, page, selectedScope.toLowerCase());

      if (res && res.results) {
        // Map backend results to Series type
        const mapped: Series[] = res.results.map((item: any) => ({
          id: item.id || item.link,
          title: item.title,
          author: item.author,
          coverUrl: item.cover || '',
          description: item.summary,
          genre: item.categories ? item.categories.join(', ') : '',
          type: item.fileType ? item.fileType.replace('application/', '').toUpperCase() : 'EPUB',
          rating: item.rating_average || 0,
          voteCount: item.rating_count || 0,
          downloadCount: item.download_count || 0,
          volumesCount: item.numBooks || 1,
          status: 'Completed',
          lastUpdated: item.updatedDate || 'Reciente',
          volumes: []
        }));

        setSeries(mapped);
        setTotalPages(res.totalPages || 1);
        setTotalResults(res.totalResults || mapped.length);
      } else {
        setSeries([]);
      }
    } catch (e) {
      console.error("Search error", e);
    } finally {
      setLoading(false);
    }
  };

  // Initial Search & Search on Enter
  useEffect(() => {
    // Debounce could be added here
    const timer = setTimeout(() => {
      doSearch(searchTerm, currentPage);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm, currentPage, selectedScope]);

  // Restore Scroll Position on Mount
  useEffect(() => {
    const savedScrollPos = sessionStorage.getItem('search_scroll_pos');
    if (savedScrollPos) {
      const mainContainer = document.querySelector('main');
      if (mainContainer) {
        setTimeout(() => {
          mainContainer.scrollTop = parseInt(savedScrollPos);
        }, 0);
      }
    }
  }, []);

  const handleSelectSeries = (series: Series) => {
    const mainContainer = document.querySelector('main');
    if (mainContainer) {
      sessionStorage.setItem('search_scroll_pos', mainContainer.scrollTop.toString());
    }
    onSelectSeries(series);
  };

  const scrollToTop = () => {
    const mainContainer = document.querySelector('main');
    if (mainContainer) {
      mainContainer.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  useEffect(() => {
    const mainContainer = document.querySelector('main');
    if (mainContainer && sessionStorage.getItem('search_scroll_pos') === null) {
      mainContainer.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [currentPage]);

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(prev => prev + 1);
      scrollToTop();
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(prev => prev - 1);
      scrollToTop();
    }
  };

  const currentSeries = series;

  const sortOptions = [
    { id: 'a-z', label: 'A-Z', icon: null },
    { id: 'added', label: 'AÑADIDO', icon: Calendar },
    { id: 'updated', label: 'ACTUALIZADO', icon: Clock },
    { id: 'downloads', label: 'DESCARGAS', icon: Download },
    { id: 'rating', label: 'VALORACIÓN', icon: Star },
  ];

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-300 relative" ref={scrollContainerRef}>

      <SearchScopeModal
        isOpen={isScopeModalOpen}
        onClose={() => setIsScopeModalOpen(false)}
        selectedScope={selectedScope}
        onSelectScope={setSelectedScope}
      />

      {/* Search Header - Floating Glass (Desktop/Tablet) */}
      <div className="sticky top-0 z-30 p-4">
        <div className="glass-panel rounded-2xl p-4 border border-white/10 shadow-lg shadow-black/20 backdrop-blur-xl">
          <div className="flex flex-row gap-2 sm:gap-4 items-center justify-between">
            <div className="relative w-full max-w-xl group flex-1">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <SearchIcon className="text-gray-400 w-5 h-5 group-focus-within:text-[#2AABEE] transition-colors" />
              </div>
              <input
                className="block w-full pl-10 pr-24 py-3 rounded-xl border border-white/5 bg-black/20 text-white placeholder-gray-500 focus:ring-1 focus:ring-[#2AABEE] focus:border-[#2AABEE] focus:bg-black/40 text-sm transition-all shadow-inner"
                placeholder="Buscar..."
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <div className="absolute inset-y-0 right-1 flex items-center">
                <button
                  onClick={() => setIsScopeModalOpen(true)}
                  className="px-3 py-1.5 rounded-lg bg-[#0f1318] hover:bg-[#2AABEE]/10 border border-white/10 hover:border-[#2AABEE]/30 text-[#2AABEE] text-[10px] font-black uppercase tracking-widest transition-all"
                >
                  {selectedScope}
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2 sm:gap-3 shrink-0">
              {/* View Toggles */}
              <div className="bg-black/20 p-1 rounded-lg border border-white/5 flex shrink-0">
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-md transition-all ${viewMode === 'list' ? 'bg-white/10 text-white shadow-sm' : 'text-gray-400 hover:text-white'}`}
                  title="Vista de Lista"
                >
                  <List className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded-md transition-all ${viewMode === 'grid' ? 'bg-white/10 text-white shadow-sm' : 'text-gray-400 hover:text-white'}`}
                  title="Vista de Cuadrícula"
                >
                  <LayoutGrid className="w-4 h-4" />
                </button>
              </div>

              {loading && <RefreshCw className="w-5 h-5 animate-spin text-[#2AABEE]" />}

              {/* Desktop Sort Controls (Hidden on Mobile) */}
              <div className="hidden md:flex items-center gap-3">
                <div className="h-6 w-px bg-white/10 mx-1"></div>
                <div className="flex bg-black/20 p-1 rounded-lg border border-white/5">
                  <button className="px-3 py-1.5 rounded-md bg-white/10 text-white shadow-sm text-xs font-bold transition-all">Título</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* List Content */}
      <div className="flex-1 px-4 pb-32 md:pb-6">
        <div className="max-w-7xl mx-auto space-y-3">

          {viewMode === 'list' ? (
            // LIST VIEW
            currentSeries.map((series) => (
              <div
                key={series.id}
                onClick={() => handleSelectSeries(series)}
                className="group flex gap-4 p-3 rounded-lg bg-[#0d1117]/80 hover:bg-[#161b22] transition-all duration-200 cursor-pointer relative overflow-hidden border border-white/5"
              >
                {/* Left: Cover Image */}
                <div className="relative shrink-0 w-[85px] sm:w-[100px] aspect-[2/3] shadow-lg rounded-md overflow-hidden bg-slate-800">
                  <img
                    alt={series.title}
                    className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
                    src={series.coverUrl}
                  />
                </div>

                {/* Right: Details */}
                <div className="flex flex-col flex-1 min-w-0 py-0.5">
                  {/* Title - Fixed to White as requested */}
                  <div className="flex justify-between items-start gap-2">
                    <h3 className="text-base sm:text-lg font-bold text-white leading-tight mb-1 line-clamp-2 sm:line-clamp-1">
                      {series.title}
                    </h3>
                    <button
                      onClick={(e) => { e.stopPropagation(); /* Add logic */ }}
                      className="p-1.5 rounded-full bg-white/5 hover:bg-[#2AABEE]/20 text-gray-400 hover:text-[#2AABEE] transition-colors shrink-0"
                    >
                      <PlusCircle className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Author */}
                  <p className="text-sm text-[#2AABEE] font-medium mb-1.5 truncate">
                    {series.author}
                  </p>

                  {/* Genres */}
                  <p className="text-xs text-gray-500 mb-auto line-clamp-1">
                    <span className="font-bold text-gray-600 uppercase tracking-wide mr-1">GÉNEROS:</span>
                    {series.genre}
                  </p>

                  {/* Meta Info Row */}
                  <div className="flex flex-wrap items-center gap-3 mt-3 mb-2">
                    <span className="text-[10px] sm:text-xs font-bold text-gray-400 uppercase tracking-widest">
                      {series.volumesCount} {series.volumesCount === 1 ? 'VOLUMEN' : 'VOLÚMENES'}
                    </span>

                    {series.type && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#004d40] text-[#4db6ac] uppercase tracking-wider border border-[#00695c]/30">
                        {series.type}
                      </span>
                    )}
                  </div>

                  {/* Stats Row */}
                  <div className="flex items-center gap-4 text-xs font-bold text-gray-500">
                    <div className="flex items-center gap-1.5 text-yellow-500">
                      <Star className="w-3.5 h-3.5 fill-current" />
                      <span className="text-gray-300">{series.rating.toFixed(1)}</span>
                      <span className="text-gray-600 font-normal">({series.voteCount || 0})</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-[#2AABEE]">
                      <Download className="w-3.5 h-3.5" />
                      <span>{series.downloadCount || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            // GRID VIEW
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {currentSeries.map((series) => (
                <div
                  key={series.id}
                  onClick={() => handleSelectSeries(series)}
                  className="group relative glass-panel rounded-2xl overflow-hidden hover:bg-white/5 shadow-sm hover:shadow-xl hover:shadow-[#2AABEE]/10 hover:-translate-y-1 transition-all duration-300 flex flex-col h-full cursor-pointer bg-black/20"
                >
                  {/* Format Badge (Top Right) */}
                  <div className="absolute top-3 right-3 z-10">
                    <span className="bg-black/60 backdrop-blur text-white text-[10px] font-bold px-2 py-1 rounded-md uppercase tracking-wider">
                      {series.type || 'EPUB'}
                    </span>
                  </div>

                  {/* Image Container */}
                  <div className="relative aspect-[2/3] overflow-hidden bg-slate-800">
                    <img
                      alt={series.title}
                      className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500 opacity-90 group-hover:opacity-100"
                      src={series.coverUrl}
                    />
                    {/* Bottom Gradient & Text Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent opacity-90"></div>
                    <div className="absolute bottom-4 left-4 right-4">
                      <h3 className="text-white font-bold text-base leading-tight line-clamp-2 drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">
                        {series.title}
                      </h3>
                      <p className="text-gray-200 text-xs font-medium mt-1 truncate drop-shadow-[0_1px_1px_rgba(0,0,0,0.8)]">
                        {series.author}
                      </p>
                    </div>
                  </div>

                  {/* Details Container */}
                  <div className="p-4 flex flex-col flex-1 bg-[#0d1117]">
                    {/* Top Row: Genre & Rating */}
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-[#2AABEE]/10 text-[#2AABEE] border border-[#2AABEE]/20 truncate max-w-[70%]">
                        {series.genre?.split(',')[0]}
                      </span>
                      <div className="flex items-center gap-1 text-yellow-500 text-xs shrink-0">
                        <Star className="w-3.5 h-3.5 fill-current" />
                        <span className="font-bold text-gray-200">{series.rating.toFixed(1)}</span>
                      </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 gap-2 text-[10px] text-gray-500 mb-4 font-mono">
                      <div className="flex items-center gap-1.5" title="Volúmenes">
                        <Book className="w-3.5 h-3.5" />
                        <span>{series.volumesCount} Vols</span>
                      </div>
                      <div className="flex items-center gap-1.5" title="Actualizado">
                        <Clock className="w-3.5 h-3.5" />
                        <span>Hoy</span>
                      </div>
                    </div>

                    {/* Footer: Publisher & Download */}
                    <div className="mt-auto pt-3 border-t border-white/5 flex items-center justify-between">
                      <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">
                        {series.status === 'Ongoing' ? 'EN EMISIÓN' : 'FINALIZADO'}
                      </span>
                      <div className="flex gap-2">
                        <button className="p-2 rounded-full bg-white/5 text-gray-400 hover:bg-[#2AABEE] hover:text-white transition-colors" onClick={(e) => { e.stopPropagation(); }}>
                          <PlusCircle className="w-4 h-4" />
                        </button>
                        <button className="p-2 rounded-full bg-white/5 text-gray-400 hover:bg-[#2AABEE] hover:text-white transition-colors">
                          <Download className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination Info */}
          <div className="text-center py-4 text-xs text-gray-500 font-medium">
            Página {currentPage} de {totalPages} • {totalResults} Resultados
          </div>
        </div>
      </div>

      {/* Mobile Catalog Bottom Bar */}
      <div className="md:hidden fixed bottom-6 left-4 right-4 z-40 flex flex-col gap-3">
        {isSortMenuOpen && (
          <div className="glass-panel rounded-2xl p-2 border border-white/10 shadow-2xl bg-[#0f1115]/95 backdrop-blur-xl animate-in slide-in-from-bottom-2 fade-in duration-200">
            <div className="flex items-center gap-2 overflow-x-auto no-scrollbar pb-1">
              {sortOptions.map((option) => {
                const isActive = activeSort === option.id;
                return (
                  <button
                    key={option.id}
                    onClick={() => setActiveSort(option.id)}
                    className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest whitespace-nowrap transition-all border ${isActive
                      ? 'bg-[#2AABEE] text-white border-[#2AABEE] shadow-lg shadow-blue-500/20'
                      : 'bg-white/5 text-gray-400 border-transparent hover:bg-white/10 hover:text-white'
                      }`}
                  >
                    {option.icon && <option.icon className="w-3 h-3" />}
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        <div className="glass-panel rounded-full p-1 border border-white/10 shadow-2xl bg-[#0f1115]/90 backdrop-blur-md flex items-center justify-between">
          <button
            onClick={handlePrevPage}
            disabled={currentPage === 1}
            className={`flex-1 flex flex-col items-center justify-center py-2.5 px-2 rounded-l-full hover:bg-white/5 active:bg-white/10 transition-colors group ${currentPage === 1 ? 'opacity-30 cursor-not-allowed' : 'text-gray-400 active:text-white'}`}
          >
            <ChevronLeft className="w-4 h-4 mb-0.5 group-active:-translate-x-1 transition-transform" />
            <span className="text-[9px] font-black uppercase tracking-widest">Anterior</span>
          </button>

          <div className="w-px h-8 bg-white/5"></div>

          <button
            onClick={() => setIsSortMenuOpen(!isSortMenuOpen)}
            className={`flex-1 flex flex-col items-center justify-center py-2.5 px-2 hover:bg-white/5 transition-colors group relative ${isSortMenuOpen ? 'text-[#2AABEE]' : 'text-gray-300'}`}
          >
            <div className={`absolute inset-x-2 bottom-0 h-0.5 rounded-t-full bg-[#2AABEE] transition-all duration-300 ${isSortMenuOpen ? 'opacity-100' : 'opacity-0'}`}></div>
            <ArrowDownUp className="w-4 h-4 mb-0.5" />
            <span className="text-[9px] font-black uppercase tracking-widest">Ordenar</span>
          </button>

          <div className="w-px h-8 bg-white/5"></div>

          <button
            onClick={() => onNavigate && onNavigate('dashboard')}
            className="flex-1 flex flex-col items-center justify-center py-2.5 px-2 hover:bg-white/5 text-gray-400 active:text-white transition-colors group"
          >
            <Home className="w-4 h-4 mb-0.5 group-active:-translate-y-1 transition-transform" />
            <span className="text-[9px] font-black uppercase tracking-widest">Inicio</span>
          </button>

          <div className="w-px h-8 bg-white/5"></div>

          <button
            onClick={handleNextPage}
            disabled={currentPage === totalPages}
            className={`flex-1 flex flex-col items-center justify-center py-2.5 px-2 rounded-r-full hover:bg-white/5 active:bg-white/10 transition-colors group ${currentPage === totalPages ? 'opacity-30 cursor-not-allowed' : 'text-gray-400 active:text-white'}`}
          >
            <ChevronRight className="w-4 h-4 mb-0.5 group-active:translate-x-1 transition-transform" />
            <span className="text-[9px] font-black uppercase tracking-widest">Siguiente</span>
          </button>
        </div>
      </div>

    </div>
  );
};