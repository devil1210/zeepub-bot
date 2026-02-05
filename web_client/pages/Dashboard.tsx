import React, { useEffect } from 'react';
import {
  Search,
  BookOpen,
  Settings,
  ArrowDownToLine,
  Library,
  ShieldCheck,
  Copy,
  Upload,
  History,
  ShieldHalf,
  BrainCircuit,
  Download,
  Star
} from 'lucide-react';
import { useTelegram } from '../contexts/TelegramContext';
import { useTheme } from '../contexts/ThemeContext';
import { useNavigation } from '../contexts/NavigationContext';
import { useDashboardData } from '../hooks/useDashboardData';

// Modular Components
import { DashboardHero } from '../components/dashboard/DashboardHero';
import { DashboardSearch } from '../components/dashboard/DashboardSearch';
import { QuickActions } from '../components/dashboard/QuickActions';
import { RecommendationsGrid } from '../components/dashboard/RecommendationsGrid';
import { StatsWidget } from '../components/dashboard/StatsWidget';
import { ActivityFeed } from '../components/dashboard/ActivityFeed';
import { QuoteWidget } from '../components/dashboard/QuoteWidget';

interface DashboardProps {
  onNavigate?: (tab: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigate }) => {
  const { user: tgUser, status, showRecommendations, extendedInfo, isAdmin } = useTelegram();
  const { settings } = useTheme();
  const { setVisible } = useNavigation();

  // Use SWR Hook for Data Fetching
  const { history, recommendations, loading } = useDashboardData();

  useEffect(() => {
    setVisible(false);
    return () => setVisible(true);
  }, [setVisible]);

  const userName = extendedInfo?.nickname || extendedInfo?.name || (tgUser ? `${tgUser.first_name}${tgUser.last_name ? ' ' + tgUser.last_name : ''}` : (status?.user?.username || "Lector"));
  const userLevel = status?.user?.status_label || "Lector";
  const downloadsUsed = status?.user?.downloads?.used || 0;
  const downloadsLimit = status?.user?.downloads?.limit || 0;
  const isUnlimited = status?.user?.downloads?.limit === -1 || status?.hasUnlimitedDownloads;
  const limitDisplay = isUnlimited ? "∞" : downloadsLimit;
  const totalDownloads = status?.user?.downloads?.total || 0;

  let progressPercent = 0;
  if (!isUnlimited && downloadsLimit > 0) {
    progressPercent = (downloadsUsed / downloadsLimit) * 100;
  }

  const mainActions = [
    { id: 'search', icon: Search, label: 'Catálogo', desc: 'Explorar Todo', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20', visible: true },
    { id: 'library', icon: Library, label: 'Biblioteca', desc: 'Mis Libros', color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20', visible: status?.user?.has_library_access !== false },
    { id: 'requests', icon: BookOpen, label: 'Pedidos', desc: 'Solicitar Libros', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', visible: status?.user?.can_request_books !== false },
    { id: 'ai', icon: BrainCircuit, label: 'AI Hub', desc: 'IA Gardener', color: 'text-purple-500', bg: 'bg-purple-500/10', border: 'border-purple-500/20', visible: isAdmin },
    { id: 'settings', icon: Settings, label: 'Ajustes', desc: 'Personalización', color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', visible: true },
  ].filter(a => a.visible);

  const controlActions = [
    { id: 'downloads', icon: ArrowDownToLine, label: 'Descargas', desc: 'Mis Libros', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20', visible: true },
    { id: 'upload', icon: Upload, label: 'Subir Epub', desc: 'Aportar Contenido', color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20', visible: status?.user?.can_upload_epub !== false },
    { id: 'admin?view=duplicates', icon: Copy, label: 'Duplicados', desc: 'Gestión DB', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', visible: isAdmin },
    { id: 'admin', icon: ShieldCheck, label: 'Admin Panel', desc: 'Sistema Global', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', visible: isAdmin },
    { id: 'admin?view=uploads', icon: History, label: 'Subidas', desc: 'Historial Global', color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', visible: isAdmin },
    { id: 'admin?view=access', icon: ShieldHalf, label: 'Niveles', desc: 'Accesos', color: 'text-indigo-400', bg: 'bg-indigo-500/10', border: 'border-indigo-500/20', visible: isAdmin },
  ].filter(a => a.visible);

  const recentActivities = [
    { action: 'Descargado', title: 'Oregairu Vol. 14', time: 'Hace 2h', icon: Download, color: 'text-primary' },
    { action: 'Agregado', title: 'Mushoku Tensei Especial', time: 'Ayer', icon: Star, color: 'text-yellow-500' },
  ];

  return (
    <div className="max-w-[1800px] mx-auto px-4 md:px-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-8">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* LEFT COLUMN */}
        <div className="lg:col-span-8 space-y-8">
          <DashboardHero
            userName={userName}
            customStatus={extendedInfo?.customStatus}
            insignias={extendedInfo?.insignias}
          />

          <DashboardSearch onSearchClick={() => onNavigate && onNavigate('search')} />

          <QuickActions
            title="Acceso Directo"
            actions={mainActions}
            onNavigate={(id) => onNavigate && onNavigate(id)}
          />

          {showRecommendations && (
            <RecommendationsGrid
              loading={loading}
              recommendations={recommendations}
              settings={settings}
              onNavigate={(id) => onNavigate && onNavigate(id)}
              onExploreMore={() => onNavigate && onNavigate('search')}
            />
          )}

          <QuickActions
            title="Panel de Control"
            actions={controlActions}
            onNavigate={(id) => onNavigate && onNavigate(id)}
          />
        </div>

        {/* RIGHT COLUMN */}
        <div className="lg:col-span-4 space-y-6">
          <StatsWidget
            userLevel={userLevel}
            role={status?.user?.role || "Free Member"}
            username={tgUser?.username ? `@${tgUser.username}` : `ID: ${tgUser?.id}`}
            photoUrl={tgUser?.photo_url}
            downloadsUsed={downloadsUsed}
            limitDisplay={limitDisplay}
            progressPercent={progressPercent}
            totalDownloads={totalDownloads}
            isUnlimited={isUnlimited}
            settings={settings}
          />

          <ActivityFeed activities={recentActivities} />

          <QuoteWidget
            quote="Un lector vive mil vidas antes de morir. Aquel que nunca lee vive solo una."
            author="George R.R. Martin"
            settings={settings}
          />
        </div>
      </div>
    </div>
  );
};
