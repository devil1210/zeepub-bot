import React, { useState, useEffect } from 'react';
import { useTheme, adjustBrightness } from '../contexts/ThemeContext';
import { useTelegram } from '../contexts/TelegramContext';
import {
  LogOut,
  ChevronRight,
  BookOpen,
  Bug,
  Palette,
  Moon,
  Sun,
  Contrast,
  PenTool,
  Wrench,
  Trash2,
  RotateCcw,
  Save,
  ArrowLeft,
  ShieldCheck,
  Home,
  Download,
  Terminal,
  Eraser,
  Eye,
  CheckCircle2,
  Upload
} from 'lucide-react';
import { ReportIssueModal } from '../components/ReportIssueModal';
import { RequestBookModal } from '../components/RequestBookModal';

interface SettingsProps {
  onNavigate?: (tab: string) => void;
}

export const Settings: React.FC<SettingsProps> = ({ onNavigate }) => {
  const { settings, updateSettings, resetSettings } = useTheme();
  const {
    user: tgUser,
    isAdmin,
    isRealAdmin,
    status,
    customThemes,
    simulatedLevel,
    setSimulatedLevel,
    showRecommendations,
    setShowRecommendations,
    uiExportedSettings,
    extendedInfo,
    canUploadEpub
  } = useTelegram();
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const [availableLevels, setAvailableLevels] = useState<Array<{ id: number, name: string, color: string }>>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [selectedElement, setSelectedElement] = useState<'nav' | 'searchbar' | 'header'>('nav');
  const [availableThemes, setAvailableThemes] = useState<any[]>([]);
  const { allowThemeTemplates } = useTelegram();

  const handleColorChange = (color: string) => {
    updateSettings({
      primaryColor: color,
      primaryColorDark: adjustBrightness(color, -20)
    });
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveMessage(null);
    try {
      const { api } = await import('../src/services/api');
      const res = await api.savePersonalSettings(settings);
      if (res.success) {
        setSaveMessage({ type: 'success', text: 'Configuración guardada correctamente' });
        setTimeout(() => setSaveMessage(null), 3000);
      } else {
        throw new Error(res.message || 'Error al guardar');
      }
    } catch (err: any) {
      setSaveMessage({ type: 'error', text: err.message || 'Error al conectar con el servidor' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleClearCache = () => {
    localStorage.clear();
    sessionStorage.clear();
    window.location.reload();
  };

  const handleBack = () => {
    if (onNavigate) {
      onNavigate('dashboard');
    }
  };

  // Fetch available levels for admin simulation
  useEffect(() => {
    if (isRealAdmin) {
      import('../src/services/api').then(({ api }) => {
        api.getAdminTiers().then((res: any) => {
          if (res.levels) {
            setAvailableLevels([
              { id: 0, name: 'Global (Default)', color: '#ffffff' },
              ...res.levels.map((l: any) => ({
                id: l.id,
                name: l.name,
                color: l.color || '#6b7280'
              }))
            ]);
          }
        }).catch(console.error);
      });
    }
  }, [isRealAdmin]);

  // Fetch themes for templates
  useEffect(() => {
    if (allowThemeTemplates || isAdmin) {
      import('../src/services/api').then(({ api }) => {
        api.getAvailableThemes().then((res: any) => {
          if (res.success) {
            setAvailableThemes(res.themes);
          }
        }).catch(console.error);
      });
    }
  }, [allowThemeTemplates, isAdmin]);

  const isVisible = (key: string) => {
    if (isAdmin) return true;
    if (!customThemes) return false;
    return uiExportedSettings.includes(key);
  };

  const hasPersonalization = isAdmin || customThemes;

  return (
    <div className="max-w-[1800px] mx-auto pb-32 md:pb-12 p-4 md:p-8 animate-in fade-in duration-300 font-sans text-gray-900 dark:text-gray-100">
      <ReportIssueModal isOpen={isReportModalOpen} onClose={() => setIsReportModalOpen(false)} />
      <RequestBookModal isOpen={isRequestModalOpen} onClose={() => setIsRequestModalOpen(false)} />

      {/* Admin Level Simulation Banner */}
      {isRealAdmin && (
        <div className="glass-panel p-4 rounded-2xl border border-purple-500/30 bg-purple-500/10 mb-6 animate-in slide-in-from-top-4 duration-300">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400 border border-purple-500/20">
                <Eye className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-bold text-white">Simulación de Nivel</p>
                <p className="text-xs text-gray-400">Ver la interfaz como un usuario de determinado nivel</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={simulatedLevel === 0 ? '0' : (simulatedLevel || '')}
                onChange={(e) => setSimulatedLevel(e.target.value === '' ? null : parseInt(e.target.value))}
                className="px-4 py-2 text-sm font-medium border border-white/10 bg-black/20 text-white focus:outline-none focus:ring-1 focus:ring-purple-500 focus:border-purple-500 rounded-xl appearance-none min-w-[160px]"
              >
                <option value="">Sin simulación</option>
                {availableLevels.map(level => (
                  <option key={level.id} value={level.id} style={{ color: level.color }}>
                    {level.name}
                  </option>
                ))}
              </select>
              {simulatedLevel && (
                <button
                  onClick={() => setSimulatedLevel(null)}
                  className="px-3 py-2 text-xs font-bold bg-red-500/20 text-red-400 rounded-lg border border-red-500/20 hover:bg-red-500/30 transition-colors"
                >
                  Desactivar
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Save Message Notification */}
      {saveMessage && (
        <div className={`fixed top-20 right-4 z-[100] p-4 rounded-xl border animate-in slide-in-from-right-4 duration-300 ${saveMessage.type === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-400' : 'bg-red-500/10 border-red-500/20 text-red-400'
          }`}>
          <div className="flex items-center gap-2">
            <div className={`p-1.5 rounded-lg ${saveMessage.type === 'success' ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
              <Save className="w-4 h-4" />
            </div>
            <p className="text-sm font-bold">{saveMessage.text}</p>
          </div>
        </div>
      )}


      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Profile & Quick Actions */}
        {/* Left Column: Profile & Navigation */}
        <div className="lg:col-span-4 space-y-8">
          {/* Profile Card (Premium) */}
          {/* Profile Card (Pro Max) */}
          <div className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-primary/50 to-purple-600/50 rounded-[3rem] blur-2xl opacity-20 group-hover:opacity-40 transition-opacity duration-1000"></div>
            <div className="glass-panel p-10 rounded-[3rem] relative overflow-hidden shadow-premium border-white/10">
              <div className="absolute top-0 left-0 w-full h-40 bg-gradient-to-br from-primary/40 via-purple-600/20 to-transparent"></div>
              <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:scale-110 group-hover:rotate-12 transition-transform duration-1000">
                <Palette className="w-24 h-24" />
              </div>

              <div className="relative flex flex-col items-center text-center mt-6">
                <div className="relative mb-8">
                  <div className="absolute inset-0 bg-gradient-to-tr from-primary via-purple-500 to-transparent rounded-full blur-xl opacity-30 animate-pulse"></div>
                  <div className="relative">
                    <img
                      alt="Avatar"
                      className="h-32 w-32 rounded-full ring-[6px] ring-[#0a0a0c] shadow-[0_0_50px_rgba(0,0,0,0.5)] object-cover z-10 scale-100 group-hover:scale-105 transition-transform duration-700"
                      src={tgUser?.photo_url || "https://lh3.googleusercontent.com/aida-public/AB6AXuD2rcMIxLOx5eu6yRpav3Y8qGpkFD2kC_fFSpyVjNI_zmfvjfPwU7tT0o4IWo8bJUd_Zt_ZE-XvtCRq0VFH6xkeCOZ6RNUSwUMkYvnq49dlaImBSvbx2y0LQ2ZShi-zZJ9SOX46KZQVmAqGJjihqPPZMUyxWkrYEvOQ0wjuaZfwx1Ux3D3P5FEFAo_3D3gvoUpdmv1x-qcgKh0DHSyh9-GHQ9EN3s9kFdAWafA1e_VN0XlAN9MZ3UD7h_56GH1_qsJ9cFtwIf5rKrw"}
                    />
                    <div className="absolute inset-0 rounded-full border border-white/20 z-20 pointer-events-none"></div>
                  </div>
                  <button className="absolute bottom-1 right-1 z-30 p-2.5 bg-primary rounded-2xl text-white shadow-2xl border-4 border-[#0a0a0c] hover:scale-110 active:scale-90 transition-all">
                    <PenTool className="w-4 h-4" />
                  </button>
                </div>

                <div className="space-y-1 mb-6">
                  <h2 className="text-3xl font-black text-white tracking-tighter drop-shadow-lg">
                    {tgUser?.first_name ? `${tgUser.first_name} ${tgUser.last_name || ''}` : 'Lectores'}
                  </h2>
                  <p className="text-[11px] text-primary font-black uppercase tracking-[0.4em] opacity-80">
                    {tgUser?.username ? `@${tgUser.username}` : `UID: ${tgUser?.id}`}
                  </p>
                </div>

                <div className="flex flex-wrap justify-center gap-2 mb-10">
                  <div className="px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-[0.25em] bg-white/[0.03] text-gray-400 border border-white/10 group-hover:border-primary/40 group-hover:text-primary transition-all duration-500">
                    {status?.user?.status_label || 'MIEMBRO'}
                  </div>
                  {isAdmin && (
                    <div className="px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-[0.25em] bg-red-500/10 text-red-500 border border-red-500/20 animate-pulse">
                      ADMIN
                    </div>
                  )}
                </div>

                <button className="w-full py-5 px-8 bg-white/[0.03] hover:bg-white/5 border border-white/10 rounded-[2rem] text-[11px] font-black uppercase tracking-[0.4em] text-gray-500 hover:text-white transition-all flex items-center justify-center gap-4 group/logout">
                  <LogOut className="w-4 h-4 group-hover/logout:-translate-x-1 transition-transform" />
                  Cerrar Sesión
                </button>
              </div>
            </div>
          </div>


          {/* Navigation / Links (Premium List) */}
          {/* Navigation / Links (Premium List) */}
          <div className="glass-panel rounded-[3rem] overflow-hidden shadow-2xl border-white/5">
            <div className="p-8 border-b border-white/5 flex items-center justify-between">
              <h3 className="text-[11px] font-black text-gray-500 uppercase tracking-[0.4em]">Panel de Control</h3>
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
            </div>
            <div className="p-3 space-y-2">
              {[
                { id: 'admin', icon: ShieldCheck, label: 'Admin Terminal', desc: 'Gestionar Sistema', visible: isAdmin, color: 'text-red-400', bg: 'bg-red-500/10' },
                { id: 'requests', icon: BookOpen, label: 'Biblioteca', desc: 'Gestionar Pedidos', visible: status?.user?.can_request_books !== false, color: 'text-blue-400', bg: 'bg-blue-500/10', action: () => setIsRequestModalOpen(true) },
                { id: 'downloads', icon: Download, label: 'Descargas', desc: 'Recursos Locales', visible: status?.user?.has_library_access !== false, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
                { id: 'upload', icon: Upload, label: 'Subir Archivo', desc: 'Aportar Contenido', visible: canUploadEpub, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
                { id: 'report', icon: Bug, label: 'Asistencia', desc: 'Reportar Incidencia', visible: true, color: 'text-amber-400', bg: 'bg-amber-500/10', action: () => setIsReportModalOpen(true) }
              ].filter(i => i.visible).map((item) => (
                <button
                  key={item.id}
                  onClick={() => item.action ? item.action() : onNavigate && onNavigate(item.id)}
                  className="w-full flex items-center justify-between p-5 rounded-[2.5rem] hover:bg-white/[0.04] transition-all duration-500 group"
                >
                  <div className="flex items-center gap-5">
                    <div className={`p-3.5 rounded-2xl ${item.bg} ${item.color} border border-white/10 shadow-lg group-hover:scale-110 group-hover:rotate-3 transition-all duration-500`}>
                      <item.icon className="w-5 h-5" strokeWidth={2.5} />
                    </div>
                    <div className="text-left">
                      <p className="text-[13px] font-black text-white uppercase tracking-tight group-hover:text-primary transition-colors">{item.label}</p>
                      <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest opacity-60 mt-0.5">{item.desc}</p>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-700 group-hover:text-primary group-hover:translate-x-1 transition-all duration-500" />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Settings and Personalization */}
        <div className="lg:col-span-8 space-y-6">

          {/* Reading and System Settings */}
          <div className="glass-panel p-10 rounded-[2.5rem] shadow-2xl border-white/5 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity duration-1000">
              <Wrench className="w-32 h-32" />
            </div>

            <h3 className="text-xl font-black text-white flex items-center gap-4 mb-10 uppercase tracking-tighter">
              <div className="p-2 rounded-xl bg-primary/20 text-primary border border-primary/20">
                <Palette className="w-5 h-5" />
              </div>
              Sistema e Interfaz
            </h3>

            <div className="space-y-12">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                <div className="space-y-4">
                  <div className="flex justify-between items-center px-1">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Escala de Texto</label>
                    <span className="text-[11px] font-black text-primary bg-primary/10 px-2 py-0.5 rounded-lg font-mono">{settings.fontSize}px</span>
                  </div>
                  <div className="flex items-center gap-4 bg-white/[0.03] p-4 rounded-2xl border border-white/5 group/slider hover:bg-white/[0.05] transition-all">
                    <span className="text-[10px] text-gray-600 font-black">A</span>
                    <input
                      type="range"
                      min="12"
                      max="20"
                      value={settings.fontSize}
                      onChange={(e) => updateSettings({ fontSize: parseInt(e.target.value) })}
                      className="w-full h-1 bg-gray-800 rounded-full appearance-none cursor-pointer accent-primary"
                    />
                    <span className="text-lg text-gray-400 font-black">A</span>
                  </div>
                </div>

                <div className="space-y-4">
                  <label className="block text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] px-1">Localización</label>
                  <div className="relative group/select">
                    <select className="block w-full px-5 py-4 text-[13px] font-black border border-white/5 bg-white/[0.03] text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary rounded-2xl appearance-none group-hover/select:bg-white/[0.05] transition-all uppercase tracking-widest">
                      <option>English (US)</option>
                      <option selected>Español</option>
                      <option>Français</option>
                      <option>Русский</option>
                      <option>简体中文</option>
                    </select>
                    <div className="absolute inset-y-0 right-0 flex items-center pr-5 pointer-events-none text-gray-600 group-hover/select:text-primary transition-colors">
                      <ChevronRight className="w-5 h-5 rotate-90" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Cover Quality Preference */}
              <div className="pt-8 border-t border-white/5">
                <label className="block text-[10px] font-black text-gray-500 mb-6 uppercase tracking-[0.2em] px-1">Motor de Portadas (Calidad de Renderizado)</label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  {[
                    { id: 'pequeña', label: 'Eco', desc: 'Ahorro' },
                    { id: 'mediana', label: 'Estandar', desc: 'Media' },
                    { id: 'grande', label: 'Premium', desc: 'Res.' },
                    { id: 'original', label: 'Ultra', desc: 'Max.' }
                  ].map((q) => (
                    <label key={q.id} className="cursor-pointer group/radio">
                      <input
                        type="radio"
                        name="coverQuality"
                        className="hidden peer"
                        checked={(settings as any).coverQuality === q.id}
                        onChange={() => updateSettings({ coverQuality: q.id as any } as any)}
                      />
                      <div className="p-4 rounded-[1.5rem] border border-white/5 bg-white/[0.03] flex flex-col items-center justify-center text-center peer-checked:border-primary peer-checked:bg-primary/10 peer-checked:shadow-[0_0_20px_rgba(var(--color-primary-rgb),0.2)] transition-all hover:bg-white/[0.06]">
                        <span className="text-[11px] font-black text-white uppercase tracking-widest transition-colors peer-checked:text-primary">{q.label}</span>
                        <span className="text-[8px] text-gray-500 font-black uppercase tracking-widest mt-1 opacity-50">{q.desc}</span>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* User Specific UI Personalization */}
          {hasPersonalization && (
            <div className="glass-panel p-10 rounded-[2.5rem] flex flex-col gap-12 border border-white/5 shadow-2xl relative overflow-hidden group">
              <div className="absolute -top-24 -right-24 w-64 h-64 bg-primary/10 rounded-full blur-[100px] pointer-events-none group-hover:bg-primary/20 transition-all duration-1000"></div>

              <div className="flex border-b border-white/5 pb-8">
                <div className="flex items-center gap-5">
                  <div className="p-3 rounded-[1.25rem] bg-indigo-500/20 text-indigo-400 border border-indigo-500/20 shadow-lg">
                    <Palette className="w-6 h-6" strokeWidth={2.5} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-black text-white uppercase tracking-tighter">Estética Pro Max</h2>
                    <p className="text-[10px] text-indigo-400/60 font-black uppercase tracking-[0.3em] leading-none mt-1.5">Arquitectura visual avanzada</p>
                  </div>
                </div>
              </div>

              {/* Theme Templates Selector */}
              {(allowThemeTemplates || isAdmin) && availableThemes.length > 0 && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between px-1">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Templates de Autor</label>
                    <span className="text-[9px] font-black text-primary bg-primary/10 px-3 py-1 rounded-full uppercase tracking-widest">{availableThemes.length} Curados</span>
                  </div>
                  <div className="flex gap-5 overflow-x-auto pb-6 custom-scrollbar px-1">
                    {availableThemes.map((theme) => {
                      const isCurrent = settings.theme === theme.theme_type && (settings.primaryColor === theme.primary_color || settings.primaryColor === theme.primaryColor);
                      return (
                        <button
                          key={theme.id}
                          onClick={() => {
                            updateSettings({
                              theme: theme.theme_type,
                              primaryColor: theme.primaryColor || theme.primary_color,
                              primaryColorDark: adjustBrightness(theme.primaryColor || theme.primary_color, -20),
                              backgroundColor: theme.backgroundColor || theme.background_color,
                              cardColor: theme.cardColor || theme.card_color,
                              glassBlur: theme.glassBlur || theme.glass_blur,
                              glassOpacity: theme.glassOpacity || theme.glass_opacity,
                              navOpacity: theme.navOpacity || theme.nav_opacity,
                              accentOpacity: theme.accentOpacity || theme.accent_opacity,
                              cardGlowIntensity: theme.cardGlowIntensity || theme.card_glow_intensity || 0.5,
                            });
                          }}
                          className={`flex-shrink-0 w-44 p-5 rounded-[2rem] border-2 transition-all duration-500 flex flex-col gap-4 group/theme relative overflow-hidden ${isCurrent ? 'border-primary bg-primary/10 shadow-[0_20px_40px_-10px_rgba(var(--color-primary-rgb),0.3)]' : 'border-white/5 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.06]'}`}
                        >
                          <div className="absolute top-0 right-0 p-3 opacity-5 group-hover/theme:rotate-12 transition-transform">
                            <Palette className="w-10 h-10" />
                          </div>

                          <div className="flex flex-col gap-1 z-10 text-left">
                            <span className={`text-[12px] font-black uppercase transition-colors ${isCurrent ? 'text-primary' : 'text-white'}`}>{theme.name}</span>
                            <span className="text-[8px] font-black text-gray-500 uppercase tracking-widest">{theme.theme_type} Engine</span>
                          </div>

                          <div className="flex gap-2 mt-auto">
                            <div className="size-5 rounded-full shadow-2xl border-2 border-[#0a0a0c]" style={{ backgroundColor: theme.primary_color || theme.primaryColor }}></div>
                            <div className="size-5 rounded-full shadow-2xl border-2 border-[#0a0a0c]" style={{ backgroundColor: theme.background_color || theme.backgroundColor }}></div>
                          </div>

                          {isCurrent && (
                            <div className="absolute top-3 right-3 animate-in zoom-in duration-500">
                              <CheckCircle2 className="w-4 h-4 text-primary" strokeWidth={3} />
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-12">
                {/* Theme Selection */}
                {isVisible('theme') && (
                  <div className="space-y-6">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] px-1">Motor de Renderizado</label>
                    <div className="grid grid-cols-1 gap-3">
                      {[
                        { id: 'light', icon: Sun, label: 'Crystal Light', desc: 'Diseño suave y luminoso' },
                        { id: 'dark', icon: Moon, label: 'Midnight Glass', desc: 'Profundidad y elegancia' },
                        { id: 'amoled', icon: Contrast, label: 'Absolute Black', desc: 'Optimizado para OLED' },
                      ].map((t) => (
                        <button
                          key={t.id}
                          onClick={() => updateSettings({ theme: t.id as any })}
                          className={`flex items-center gap-5 p-5 rounded-[1.75rem] border-2 transition-all duration-500 group/item relative overflow-hidden ${settings.theme === t.id
                            ? 'bg-primary/10 border-primary text-primary shadow-[0_0_25px_rgba(var(--color-primary-rgb),0.1)]'
                            : 'bg-white/[0.03] border-white/5 text-gray-500 hover:border-white/20'
                            }`}
                        >
                          <div className={`p-3 rounded-2xl transition-all duration-500 ${settings.theme === t.id ? 'bg-primary text-white shadow-lg' : 'bg-white/5 text-gray-600 group-hover/item:text-gray-300'}`}>
                            <t.icon className="w-5 h-5" strokeWidth={2.5} />
                          </div>
                          <div className="text-left">
                            <span className={`text-[13px] font-black uppercase tracking-tight block ${settings.theme === t.id ? 'text-white' : 'text-gray-400'}`}>{t.label}</span>
                            <span className="text-[9px] font-bold uppercase tracking-widest opacity-40">{t.desc}</span>
                          </div>
                          {settings.theme === t.id && <div className="ml-auto pr-2"><div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_10px_rgba(var(--color-primary-rgb),0.8)]"></div></div>}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Accent Color Selection */}
                {isVisible('primaryColor') && (
                  <div className="space-y-6">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] px-1">Firma de Color (Énfasis)</label>
                    <div className="p-6 bg-white/[0.03] border border-white/5 rounded-[2rem] flex flex-col gap-8">
                      <div className="flex flex-wrap gap-4">
                        {['#FB7185', '#38BDF8', '#4ADE80', '#FBBF24', '#818CF8', '#F472B6', '#A78BFA'].map((color) => (
                          <button
                            key={color}
                            onClick={() => handleColorChange(color)}
                            className={`w-10 h-10 rounded-2xl transition-all duration-500 border-4 flex items-center justify-center relative overflow-hidden ${settings.primaryColor === color ? 'border-primary scale-110 shadow-2xl' : 'border-white/5 hover:scale-105'}`}
                            style={{ backgroundColor: color }}
                          >
                            {settings.primaryColor === color && <div className="absolute inset-0 bg-white/20 animate-pulse" />}
                          </button>
                        ))}
                      </div>
                      <div className="flex items-center gap-4 pt-6 border-t border-white/5">
                        <div className="p-2.5 rounded-xl bg-white/5 text-gray-500"><PenTool className="w-4 h-4" /></div>
                        <div className="flex-1 text-[11px] font-black text-gray-500 uppercase tracking-widest">Personalizar Tono</div>
                        <label className="relative flex items-center gap-3 cursor-pointer group/native">
                          <div className="w-12 h-12 rounded-2xl border-2 border-white/10 group-hover/native:border-primary transition-all p-1">
                            <div className="w-full h-full rounded-xl shadow-inner border border-white/10" style={{ backgroundColor: settings.primaryColor }}></div>
                          </div>
                          <input
                            type="color"
                            value={settings.primaryColor}
                            onChange={(e) => handleColorChange(e.target.value)}
                            className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                          />
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Transparency Effects */}
                {(isVisible('glassBlur') || isVisible('glassOpacity')) && (
                  <div className="space-y-8 col-span-full border-t border-white/5 pt-10">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] px-1">Arquitectura de Cristal</label>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                      {isVisible('glassBlur') && (
                        <div className="space-y-5">
                          <div className="flex justify-between items-center px-1">
                            <span className="text-[11px] font-black text-white uppercase tracking-widest">Difusión (Gaussian Blur)</span>
                            <span className="text-[11px] font-black text-primary font-mono bg-primary/10 px-2 py-0.5 rounded-lg">{settings.glassBlur}px</span>
                          </div>
                          <div className="bg-white/[0.03] p-5 rounded-2xl border border-white/5">
                            <input
                              type="range"
                              min="0"
                              max="40"
                              value={settings.glassBlur}
                              onChange={(e) => updateSettings({ glassBlur: parseInt(e.target.value) })}
                              className="w-full accent-primary h-1 bg-gray-800 rounded-full appearance-none cursor-pointer"
                            />
                          </div>
                        </div>
                      )}
                      {isVisible('glassOpacity') && (
                        <div className="space-y-5">
                          <div className="flex justify-between items-center px-1">
                            <span className="text-[11px] font-black text-white uppercase tracking-widest">Densidad de Capa</span>
                            <span className="text-[11px] font-black text-primary font-mono bg-primary/10 px-2 py-0.5 rounded-lg">{Math.round(settings.glassOpacity * 100)}%</span>
                          </div>
                          <div className="bg-white/[0.03] p-5 rounded-2xl border border-white/5">
                            <input
                              type="range"
                              min="0"
                              max="100"
                              value={settings.glassOpacity * 100}
                              onChange={(e) => updateSettings({ glassOpacity: parseInt(e.target.value) / 100 })}
                              className="w-full accent-primary h-1 bg-gray-800 rounded-full appearance-none cursor-pointer"
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between gap-6 pt-10 border-t border-white/5">
                <button
                  onClick={resetSettings}
                  className="px-8 py-4 rounded-[1.5rem] text-[10px] font-black uppercase tracking-[0.3em] text-gray-500 hover:text-white border border-white/10 hover:bg-white/5 transition-all flex items-center gap-3"
                >
                  <RotateCcw className="w-4 h-4" />
                  Resetear Perfil
                </button>
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className={`px-12 py-4 rounded-[1.5rem] text-[10px] font-black uppercase tracking-[0.3em] text-white shadow-2xl flex items-center gap-4 transition-all hover:scale-105 active:scale-95 ${isSaving ? 'bg-gray-800 cursor-not-allowed opacity-50 border-white/5' : 'bg-primary border border-white/20 shadow-primary/30'
                    }`}
                >
                  {isSaving ? <RotateCcw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  {isSaving ? 'Aplicando...' : 'Confirmar Cambios'}
                </button>
              </div>
            </div>
          )}

          {/* Troubleshooting */}
          <div className="glass-panel p-6 rounded-2xl border border-white/5">
            <h3 className="text-lg font-black text-white flex items-center gap-2 mb-4 uppercase tracking-tight">
              <Wrench className="text-red-400 w-5 h-5" />
              Solución de Problemas
            </h3>
            <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-4 bg-red-900/10 border border-red-900/30 rounded-xl">
              <div>
                <p className="text-sm font-bold text-red-200">Almacenamiento de Caché Local</p>
                <p className="text-xs text-red-400 mt-1">Si notas comportamientos extraños, limpia la caché.</p>
              </div>
              <button
                onClick={handleClearCache}
                className="px-4 py-2 bg-red-900/30 hover:bg-red-900/50 text-red-200 text-[10px] font-black uppercase tracking-widest rounded-lg border border-red-800 transition-colors"
                title="Limpiar Caché"
              >
                Limpiar Caché
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Bottom Floating Action Bar */}
      <div className="md:hidden fixed bottom-6 left-8 right-8 z-50 animate-in slide-in-from-bottom-4 duration-300">
        <div
          className="glass-panel rounded-3xl p-1 border border-white/10 shadow-2xl flex items-center justify-between overflow-hidden"
          style={{
            background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
            backdropFilter: `blur(${settings.glassBlur}px)`,
            WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
          }}
        >
          <button
            onClick={() => onNavigate && onNavigate('dashboard')}
            className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 text-gray-400 hover:text-black dark:hover:text-white"
          >
            <div className="p-1.5 rounded-full transition-all duration-300">
              <Home className="w-4 h-4" strokeWidth={2} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest mt-1">Inicio</span>
          </button>

          <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

          <button
            onClick={resetSettings}
            className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 text-gray-400 hover:text-black dark:hover:text-white"
          >
            <div className="p-1.5 rounded-full transition-all duration-300">
              <RotateCcw className="w-4 h-4" strokeWidth={2} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest mt-1">Restaurar</span>
          </button>

          <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 text-[var(--color-primary)] disabled:opacity-50"
          >
            <div className="p-1.5 rounded-full bg-[var(--color-primary)] shadow-[0_0_15px_rgba(43,108,238,0.5)] translate-y-[-2px]">
              {isSaving ? <RotateCcw className="w-4 h-4 text-white animate-spin" strokeWidth={2.5} /> : <Save className="w-4 h-4 text-white" strokeWidth={2.5} />}
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest mt-1 text-[var(--color-primary)]">{isSaving ? 'Guardando' : 'Guardar'}</span>
          </button>
        </div>
      </div>

    </div >
  );
};