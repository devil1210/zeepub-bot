import React from 'react';
import {
  LayoutDashboard,
  Search,
  Library,
  Settings,
  ShieldCheck,
  BookOpen,
  LogOut,
  ChevronRight,
  Upload,
  BrainCircuit
} from 'lucide-react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { useNavigation } from '@shared/contexts/NavigationContext';
import { UniversalFloatingNav } from './UniversalFloatingNav';
import { SearchHeader } from '@features/search/components/SearchHeader';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tab: string) => void;
  showMobileBottomNav?: boolean;
}

export const Layout: React.FC<LayoutProps> = ({ children, activeTab, onTabChange }) => {
  const { settings } = useTheme();
  const { user: tgUser, status, isAdmin, botInfo, canUploadEpub } = useTelegram();
  const {
    state: navState,
    handleSearchChange,
    handleSearchSubmit,
    handleScopeClick,
    setViewMode
  } = useNavigation();

  const navItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Inicio' },
    { id: 'search', icon: Search, label: 'Búsqueda y Catálogos' },
    { id: 'library', icon: Library, label: 'Mi Biblioteca' },
    { id: 'settings', icon: Settings, label: 'Ajustes' },
    ...(isAdmin ? [
      { id: 'ai', icon: BrainCircuit, label: 'AI Hub' },
      { id: 'admin', icon: ShieldCheck, label: 'Admin' }
    ] : []),
    ...(canUploadEpub ? [{ id: 'upload', icon: Upload, label: 'Subir' }] : []),
  ];

  const isMobile = typeof window !== 'undefined' && window.innerWidth < 1024;

  return (
    <div
      className="flex h-screen w-full text-white overflow-hidden selection:bg-primary selection:text-white relative transition-colors duration-300"
      style={{
        backgroundColor: 'var(--app-bg)',
        paddingTop: 'env(safe-area-inset-top)',
        '--banner-content-offset': `${settings.bannerContentOffset || 0}px`
      } as React.CSSProperties}
    >
      {/* Background Mesh Gradients (Immersive) */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0 opacity-50">
        <div className="absolute top-[-20%] right-[-10%] w-[1000px] h-[1000px] bg-primary/20 rounded-full blur-[180px] animate-pulse-slow"></div>
        <div className="absolute bottom-[-15%] left-[-20%] w-[800px] h-[800px] bg-purple-600/10 rounded-full blur-[150px] animate-float"></div>
        <div className="absolute top-[20%] left-[10%] w-[500px] h-[500px] bg-blue-400/5 rounded-full blur-[120px] animate-pulse-slow" style={{ animationDelay: '2s' }}></div>
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[var(--bg-color)]/20 to-[var(--bg-color)]"></div>
      </div>

      <div className="fixed inset-0 bg-[var(--bg-color)]/60 z-[1] pointer-events-none"></div>

      {/* ================= DESKTOP SIDEBAR ================= */}
      <aside className="hidden md:flex flex-col w-72 h-full z-20 glass-panel border-r border-[var(--panel-border)] relative rounded-none">

        {/* Logo Area */}
        <div className="p-8 pb-4">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-premium-sm bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center shadow-lg shadow-primary/20">
              <BookOpen className="text-white w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight leading-none text-white">Zeepub<span className="text-primary">Bot</span></h1>
              <span className="text-[10px] text-gray-500 font-medium uppercase tracking-widest">{botInfo?.version || 'v8.4.2-STABLE'}</span>
            </div>
          </div>

          <div className="h-px w-full bg-gradient-to-r from-transparent via-[var(--panel-border)] to-transparent"></div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-5 space-y-1.5 overflow-y-auto custom-scrollbar pt-4">
          <p className="px-4 text-[10px] font-black text-gray-500 uppercase tracking-[0.3em] mb-4 opacity-70">Menú Principal</p>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-4 px-4 py-4 rounded-premium-sm transition-all duration-500 group relative overflow-hidden ${isActive
                  ? 'bg-white/[0.08] text-white shadow-premium'
                  : 'text-gray-500 hover:text-white hover:bg-white/5'
                  }`}
              >
                {isActive && (
                  <>
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-10 bg-primary rounded-r-full shadow-[0_0_15px_rgba(var(--color-primary-rgb),0.8)]"></div>
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent opacity-50"></div>
                  </>
                )}
                <item.icon className={`w-5.5 h-5.5 transition-all duration-500 group-hover:scale-110 ${isActive ? 'text-primary drop-shadow-[0_0_8px_rgba(var(--color-primary-rgb),0.5)]' : 'text-gray-600 group-hover:text-white'}`} />
                <span className={`text-sm tracking-tight transition-all duration-500 ${isActive ? 'font-black' : 'font-medium'}`}>{item.label}</span>
                {isActive && <ChevronRight className="w-4 h-4 ml-auto text-primary animate-in fade-in slide-in-from-left-2" />}
              </button>
            );
          })}

          {isAdmin && (
            <div className="pt-6 pb-2">
              <p className="px-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Administración</p>
              <button
                onClick={() => onTabChange('admin')}
                className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-premium-sm transition-all duration-200 group ${activeTab === 'admin'
                  ? 'bg-primary/20 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-[var(--panel-bg-subtle)]'
                  }`}
              >
                <ShieldCheck className="w-5 h-5 group-hover:text-red-400 transition-colors" />
                <span className="text-sm font-medium">Panel Admin</span>
              </button>
            </div>
          )}
        </nav>

        {/* User Profile (Bottom of Sidebar) */}
        <div className="p-6 mt-auto">
          <div
            onClick={() => onTabChange('settings')}
            className="glass-panel p-4 rounded-premium border border-white/5 flex items-center gap-4 hover:border-primary/40 hover:bg-white/[0.05] transition-all duration-500 cursor-pointer group shadow-2xl"
          >
            <div className="relative group/avatar">
              <div className="absolute -inset-1 bg-gradient-to-tr from-primary to-purple-600 rounded-full blur opacity-20 group-hover/avatar:opacity-60 transition duration-500"></div>
              <div className="relative w-11 h-11 rounded-full bg-white/10 p-[2px] overflow-hidden">
                <img
                  src={tgUser?.photo_url || "https://images.unsplash.com/photo-1544947950-fa07a98d237f?q=80&w=200"}
                  alt="User"
                  className="w-full h-full rounded-full object-cover grayscale-[20%] group-hover/avatar:grayscale-0 transition-all duration-500"
                />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-black text-white truncate leading-tight">{tgUser?.first_name ? `${tgUser.first_name} ${tgUser.last_name || ''}` : 'Usuario'}</p>
              <p className="text-[10px] text-primary font-black truncate uppercase tracking-widest mt-1 opacity-80">{status?.user?.status_label || 'Visitante'}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* ================= MAIN CONTENT AREA ================= */}
      <div className="flex-1 flex flex-col h-full w-full relative z-10 min-w-0">

        <header
          className="md:hidden flex items-center justify-between px-4 py-4 z-40 sticky top-0 border-b border-[var(--panel-border)] shrink-0"
          style={{
            background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
            backdropFilter: `blur(${settings.glassBlur}px)`,
            WebkitBackdropFilter: `blur(${settings.glassBlur}px)`,
            marginTop: 'calc(-1 * env(safe-area-inset-top, 0px))',
            paddingTop: 'calc(env(safe-area-inset-top, 0px) + 1rem)'
          }}
        >
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <BookOpen className="text-white w-5 h-5" />
            </div>
            <span className="font-bold text-lg text-white">ZeepubBot</span>
          </div>
          <button onClick={() => onTabChange('settings')} className="w-8 h-8 rounded-full overflow-hidden border border-white/20">
            <img src={tgUser?.photo_url || "https://lh3.googleusercontent.com/aida-public/AB6AXuD2rcMIxLOx5eu6yRpav3Y8qGpkFD2kC_fFSpyVjNI_zmfvjfPwU7tT0o4IWo8bJUd_Zt_ZE-XvtCRq0VFH6xkeCOZ6RNUSwUMkYvnq49dlaImBSvbx2y0LQ2ZShi-zZJ9SOX46KZQVmAqGJjihqPPZMUyxWkrYEvOQ0wjuaZfwx1Ux3D3P5FEFAo_3D3gvoUpdmv1x-qcgKh0DHSyh9-GHQ9EN3s9kFdAWafA1e_VN0XlAN9MZ3UD7h_56GH1_qsJ9cFtwIf5rKrw"} alt="Profile" />
          </button>
        </header>

        {/* Scrollable Content */}
        <main
          className={`flex-1 overflow-y-auto relative scroll-smooth custom-scrollbar pb-24 md:pb-0 ${activeTab === 'search' ? '' : 'pt-4 md:pt-8'}`}
          style={{
            paddingTop: (isMobile && activeTab !== 'search') ? 'calc(1.5rem + 1rem + 0.5rem)' : undefined,
            marginTop: (isMobile && activeTab !== 'search') ? 'calc(-1 * env(safe-area-inset-top, 0px))' : undefined
          }}
        >
          {/* Search Header - Sticky inside scroll area */}
          {activeTab === 'search' && navState.isVisible && (
            <div className="sticky top-0 z-30 transition-all duration-300">
              <SearchHeader
                searchTerm={navState.searchTerm}
                onSearchChange={handleSearchChange}
                onSearchSubmit={handleSearchSubmit}
                selectedScope={navState.selectedScope}
                onScopeClick={handleScopeClick}
                viewMode={navState.viewMode}
                onViewModeChange={setViewMode}
                loading={navState.loading}
              />
            </div>
          )}
          {children}
        </main>

        {/* Universal Floating Navigation Bar */}
        <UniversalFloatingNav activeTab={activeTab} onTabChange={onTabChange} />
      </div>
    </div>
  );
};
