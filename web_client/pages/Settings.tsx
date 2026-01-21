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
  CheckCircle2
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
    extendedInfo
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
    <div className="max-w-6xl mx-auto pb-32 md:pb-12 p-4 md:p-8 animate-in fade-in duration-300 font-sans text-gray-900 dark:text-gray-100">
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
        <div className="lg:col-span-4 space-y-6">
          {/* Profile Card */}
          <div className="glass-panel p-6 rounded-2xl relative overflow-hidden border border-white/5 shadow-xl">
            <div className="absolute top-0 left-0 w-full h-24 bg-gradient-to-r from-primary/20 to-purple-600/20"></div>
            <div className="relative flex flex-col items-center text-center mt-8">
              <div className="relative group cursor-pointer">
                <img
                  alt="Avatar de Usuario"
                  className="h-24 w-24 rounded-full ring-4 ring-[#121212] shadow-2xl object-cover"
                  src={tgUser?.photo_url || "https://lh3.googleusercontent.com/aida-public/AB6AXuB4k5u3hJ-stj856Bvv__7CQz0Oynqfc4SX4g2PgE825IwIx0nNowP9TzRSjkIDDcA7GwSCgn-oZ_2NTFtopYKSXGpfH4AIHKu57ENJCuaJ4MPydF7uAB_dGFJFsnhhczBJX4I1T2igBXRb8HnhCjflxVCan3rSeljiKNXrDK-tU83AANxLXst6PrRelgTnArgn3vvH88AyJrMPrKjxhPGHyxvLqe-Xz4Po9X6G90nxaYRmNkUbVj9l6r7CP8J3rxfdySsH17xgfBs"}
                />
                <div className="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <PenTool className="text-white w-5 h-5" />
                </div>
              </div>
              <h2 className="text-xl font-bold text-white mt-4">{tgUser?.first_name ? `${tgUser.first_name} ${tgUser.last_name || ''}` : 'Usuario'}</h2>
              <p className="text-sm text-gray-400">@{tgUser?.username || 'usuario'}</p>
              {tgUser?.id && (
                <div className="mt-1 flex items-center gap-1.5 opacity-40 hover:opacity-100 transition-opacity">
                  <Terminal className="w-3 h-3" />
                  <span className="text-[10px] font-mono text-gray-500">{tgUser.id}</span>
                </div>
              )}
              <div className="mt-3 flex gap-2">
                {isAdmin ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-widest bg-primary/10 text-primary border border-primary/20">
                    Administrador
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-widest bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    {status?.user?.status_label || extendedInfo?.customStatus || 'Usuario'}
                  </span>
                )}
              </div>
              <button className="mt-6 w-full py-2.5 px-4 border border-white/10 rounded-xl text-xs font-black uppercase tracking-widest text-gray-300 hover:bg-white/5 transition-colors flex items-center justify-center gap-2">
                <LogOut className="w-4 h-4" />
                Cerrar Sesión
              </button>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="glass-panel rounded-2xl overflow-hidden border border-white/5 shadow-lg">
            <div className="p-4 border-b border-white/5 bg-white/5">
              <h3 className="text-xs font-black text-white uppercase tracking-wider">Acciones Rápidas</h3>
            </div>
            <div className="divide-y divide-white/5">

              {/* Admin Panel Button (Visible if Admin) */}
              {isAdmin && (
                <button
                  onClick={() => onNavigate && onNavigate('admin')}
                  className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors group cursor-pointer text-left bg-red-500/5 hover:bg-red-500/10"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-red-500/10 text-red-400 border border-red-500/10">
                      <ShieldCheck className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-white">Panel de Administración</p>
                      <p className="text-xs text-gray-400">Gestionar sistema y usuarios</p>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-primary transition-colors" />
                </button>
              )}

              {status?.user?.can_request_books !== false && (
                <button
                  onClick={() => setIsRequestModalOpen(true)}
                  className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors group cursor-pointer text-left"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/10">
                      <BookOpen className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-white">Solicitudes de Libros</p>
                      <p className="text-xs text-gray-400">Enviar peticiones de nuevo contenido</p>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-primary transition-colors" />
                </button>
              )}
              {status?.user?.has_library_access !== false && (
                <button
                  onClick={() => onNavigate && onNavigate('downloads')}
                  className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors group cursor-pointer text-left"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-green-500/10 text-green-400 border border-green-500/10">
                      <Download className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-white">Mis Descargas</p>
                      <p className="text-xs text-gray-400">Ver contenido recién descargado</p>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-primary transition-colors" />
                </button>
              )}
              {isAdmin && (
                <>
                  <button
                    onClick={() => {
                      if (confirm('¿Estás seguro de que quieres restablecer tus estadísticas? Esta acción no se puede deshacer.')) {
                        // api.rpc('reset_user_stats', {})
                      }
                    }}
                    className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors group cursor-pointer text-left"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-xl bg-orange-500/10 text-orange-400 border border-orange-500/10">
                        <RotateCcw className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-white">Restablecer Estadísticas</p>
                        <p className="text-xs text-gray-400">Reiniciar contador de descargas y actividad</p>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-primary transition-colors" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('¿Quieres reiniciar tu contador de descargas diarias?')) {
                        // api.rpc('reset_download_counter', {})
                      }
                    }}
                    className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors group cursor-pointer text-left"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-xl bg-red-500/10 text-red-500 border border-red-500/10">
                        <Eraser className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-white">Reiniciar Contador Diario</p>
                        <p className="text-xs text-gray-400">Pone a cero el límite de descargas del día</p>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-primary transition-colors" />
                  </button>
                </>
              )}
              <button
                onClick={() => setIsReportModalOpen(true)}
                className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors group cursor-pointer text-left"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/10">
                    <Bug className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-white">Reportar un Problema</p>
                    <p className="text-xs text-gray-400">Enviar registros a desarrolladores</p>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-primary transition-colors" />
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Settings and Personalization */}
        <div className="lg:col-span-8 space-y-6">

          {/* Standard Settings Section */}
          <div className="glass-panel p-8 rounded-2xl border border-white/5 shadow-xl">
            <h3 className="text-lg font-black text-white flex items-center gap-2 mb-6 uppercase tracking-tight">
              <Palette className="text-primary w-5 h-5" />
              Ajustes de Lectura y Sistema
            </h3>

            <div className="space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-xs font-black text-gray-400 uppercase tracking-widest">Tamaño de Fuente</label>
                    <span className="text-xs font-mono text-primary">{settings.fontSize}px</span>
                  </div>
                  <div className="flex items-center gap-3 bg-black/20 p-3 rounded-xl border border-white/5">
                    <span className="text-xs text-gray-500 font-bold">A</span>
                    <input
                      type="range"
                      min="12"
                      max="20"
                      value={settings.fontSize}
                      onChange={(e) => updateSettings({ fontSize: parseInt(e.target.value) })}
                      className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                    <span className="text-lg text-gray-300 font-bold">A</span>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-black text-gray-400 mb-2 uppercase tracking-widest">Idioma</label>
                  <div className="relative">
                    <select className="block w-full pl-4 pr-10 py-2.5 text-sm font-medium border border-white/10 bg-black/20 text-white focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary rounded-xl appearance-none">
                      <option>English (US)</option>
                      <option selected>Español</option>
                      <option>Français</option>
                      <option>Русский</option>
                      <option>简体中文</option>
                    </select>
                    <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-gray-500">
                      <ChevronRight className="w-4 h-4 rotate-90" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Cover Quality Preference */}
              <div className="pt-4 border-t border-white/5">
                <label className="block text-xs font-black text-gray-400 mb-3 uppercase tracking-widest">Calidad de Imágenes de Portada</label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { id: 'pequeña', label: 'Baja (200px)', desc: 'Ahorro' },
                    { id: 'mediana', label: 'Media (600px)', desc: 'Estándar' },
                    { id: 'grande', label: 'Alta (1000px)', desc: 'Nítida' },
                    { id: 'original', label: 'Original', desc: 'Máxima' }
                  ].map((q) => (
                    <label key={q.id} className="cursor-pointer group">
                      <input
                        type="radio"
                        name="coverQuality"
                        className="hidden peer"
                        checked={(settings as any).coverQuality === q.id}
                        onChange={() => updateSettings({ coverQuality: q.id as any } as any)}
                      />
                      <div className="p-3 rounded-xl border-2 border-white/10 bg-black/20 flex flex-col items-center justify-center text-center peer-checked:border-primary peer-checked:ring-1 peer-checked:ring-primary transition-all hover:bg-black/30">
                        <span className="text-[10px] font-black text-white uppercase tracking-wider">{q.label}</span>
                        <span className="text-[9px] text-gray-500 font-bold mt-0.5">{q.desc}</span>
                      </div>
                    </label>
                  ))}
                </div>
                <p className="text-[10px] text-gray-500 mt-3 italic">Nota: Las calidades "Alta" y "Original" pueden aumentar el consumo de datos.</p>
              </div>
            </div>
          </div>

          {/* User Specific UI Personalization */}
          {hasPersonalization && (
            <div className="glass-panel p-6 rounded-2xl flex flex-col gap-8 border border-white/5 shadow-xl">
              <div className="flex border-b border-white/5 pb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-2xl bg-primary/10 text-primary border border-primary/20">
                    <Palette className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-xl font-black text-white uppercase tracking-tight">Personalización</h2>
                    <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest leading-none mt-1">Transforma tu experiencia visual</p>
                  </div>
                </div>
              </div>

              {/* Theme Templates Selector */}
              {(allowThemeTemplates || isAdmin) && availableThemes.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1">Biblioteca de Temas Profesionales</label>
                    <span className="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full uppercase">{availableThemes.length} Disponibles</span>
                  </div>
                  <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
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
                          className={`flex-shrink-0 w-40 p-4 rounded-2xl border-2 transition-all flex flex-col gap-3 group relative overflow-hidden ${isCurrent ? 'border-primary bg-primary/10' : 'border-white/5 bg-black/40 hover:border-white/10'}`}
                        >
                          <div className="absolute top-0 right-0 p-2 opacity-5 pointer-events-none">
                            <Palette className="w-8 h-8" />
                          </div>

                          <div className="flex flex-col gap-1 z-10">
                            <span className="text-[11px] font-black text-white truncate text-left">{theme.name}</span>
                            <span className="text-[8px] font-bold text-gray-500 uppercase text-left">{theme.theme_type}</span>
                          </div>

                          <div className="flex gap-1.5 mt-auto">
                            <div className="size-4 rounded-full shadow-lg" style={{ backgroundColor: theme.primary_color || theme.primaryColor }}></div>
                            <div className="size-4 rounded-full border border-white/10" style={{ backgroundColor: theme.background_color || theme.backgroundColor }}></div>
                            <div className="size-4 rounded-full border border-white/10" style={{ backgroundColor: theme.card_color || theme.cardColor }}></div>
                          </div>

                          {isCurrent && (
                            <div className="absolute top-2 right-2">
                              <CheckCircle2 className="w-3.5 h-3.5 text-primary" />
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-10">
                {/* Theme Selection */}
                {isVisible('theme') && (
                  <div className="space-y-4">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1">Apariencia del Sistema</label>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { id: 'light', icon: Sun, label: 'Claro' },
                        { id: 'dark', icon: Moon, label: 'Oscuro' },
                        { id: 'amoled', icon: Contrast, label: 'AMOLED' },
                      ].map((t) => (
                        <button
                          key={t.id}
                          onClick={() => updateSettings({ theme: t.id as any })}
                          className={`flex flex-col items-center gap-3 p-4 rounded-2xl border-2 transition-all group ${settings.theme === t.id
                            ? 'bg-primary/10 border-primary text-primary shadow-lg shadow-primary/10 scale-105'
                            : 'bg-black/20 border-white/5 text-gray-400 hover:border-white/10'
                            }`}
                        >
                          <t.icon className={`w-6 h-6 transition-transform ${settings.theme === t.id ? 'scale-110' : 'group-hover:scale-110'}`} />
                          <span className="text-[10px] font-black uppercase tracking-widest">{t.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Accent Color Selection */}
                {isVisible('primaryColor') && (
                  <div className="space-y-4">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1">Color de Énfasis (Primario)</label>
                    <div className="flex flex-wrap gap-4 p-4 bg-black/20 border border-white/5 rounded-2xl">
                      {['#FB7185', '#38BDF8', '#4ADE80', '#FBBF24', '#818CF8', '#F472B6', '#A78BFA'].map((color) => (
                        <button
                          key={color}
                          onClick={() => handleColorChange(color)}
                          className={`w-10 h-10 rounded-xl transition-all border-2 flex items-center justify-center group ${settings.primaryColor === color ? 'border-white scale-110 shadow-lg' : 'border-transparent hover:scale-105'}`}
                          style={{ backgroundColor: color }}
                        >
                          {settings.primaryColor === color && <div className="w-1.5 h-1.5 bg-white rounded-full shadow-lg" />}
                        </button>
                      ))}
                      <div className="w-px h-8 bg-white/5 mx-1" />
                      <label className="w-10 h-10 rounded-xl bg-gradient-to-tr from-gray-700 to-gray-500 flex items-center justify-center cursor-pointer hover:scale-105 transition-all relative overflow-hidden">
                        <Palette className="w-4 h-4 text-white" />
                        <input
                          type="color"
                          value={settings.primaryColor}
                          onChange={(e) => handleColorChange(e.target.value)}
                          className="absolute inset-0 opacity-0 cursor-pointer w-full h-full scale-150"
                        />
                      </label>
                    </div>
                  </div>
                )}

                {/* Background Color Selection */}
                {isVisible('backgroundColor') && (
                  <div className="space-y-4">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1">Color de Fondo</label>
                    <div className="flex flex-wrap gap-4 p-4 bg-black/20 border border-white/5 rounded-2xl">
                      {['#0f172a', '#1e293b', '#111827', '#18181b', '#0c0a09'].map((color) => (
                        <button
                          key={color}
                          onClick={() => updateSettings({ backgroundColor: color })}
                          className={`w-10 h-10 rounded-xl transition-all border-2 flex items-center justify-center group ${settings.backgroundColor === color ? 'border-white scale-110 shadow-lg' : 'border-transparent hover:scale-105'}`}
                          style={{ backgroundColor: color }}
                        >
                          {settings.backgroundColor === color && <div className="w-1.5 h-1.5 bg-white rounded-full shadow-lg" />}
                        </button>
                      ))}
                      <div className="w-px h-8 bg-white/5 mx-1" />
                      <label className="w-10 h-10 rounded-xl bg-gradient-to-tr from-gray-900 to-gray-700 flex items-center justify-center cursor-pointer hover:scale-105 transition-all relative overflow-hidden">
                        <Palette className="w-4 h-4 text-white" />
                        <input
                          type="color"
                          value={settings.backgroundColor || '#0f172a'}
                          onChange={(e) => updateSettings({ backgroundColor: e.target.value })}
                          className="absolute inset-0 opacity-0 cursor-pointer w-full h-full scale-150"
                        />
                      </label>
                    </div>
                  </div>
                )}

                {/* Card Color Selection */}
                {isVisible('cardColor') && (
                  <div className="space-y-4">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1">Color de Tarjetas</label>
                    <div className="flex flex-wrap gap-4 p-4 bg-black/20 border border-white/5 rounded-2xl">
                      {['#1e293b', '#334155', '#1f2937', '#27272a', '#292524'].map((color) => (
                        <button
                          key={color}
                          onClick={() => updateSettings({ cardColor: color })}
                          className={`w-10 h-10 rounded-xl transition-all border-2 flex items-center justify-center group ${settings.cardColor === color ? 'border-white scale-110 shadow-lg' : 'border-transparent hover:scale-105'}`}
                          style={{ backgroundColor: color }}
                        >
                          {settings.cardColor === color && <div className="w-1.5 h-1.5 bg-white rounded-full shadow-lg" />}
                        </button>
                      ))}
                      <div className="w-px h-8 bg-white/5 mx-1" />
                      <label className="w-10 h-10 rounded-xl bg-gradient-to-tr from-gray-700 to-gray-500 flex items-center justify-center cursor-pointer hover:scale-105 transition-all relative overflow-hidden">
                        <Palette className="w-4 h-4 text-white" />
                        <input
                          type="color"
                          value={settings.cardColor || '#1e293b'}
                          onChange={(e) => updateSettings({ cardColor: e.target.value })}
                          className="absolute inset-0 opacity-0 cursor-pointer w-full h-full scale-150"
                        />
                      </label>
                    </div>
                  </div>
                )}

                {/* Transparency Sliders Section */}
                {(isVisible('glassBlur') || isVisible('glassOpacity')) && (
                  <div className="space-y-6">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1 inline-block">Efectos de Transparencia</label>
                    {isVisible('glassBlur') && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center bg-white/5 p-3 rounded-xl border border-white/5">
                          <span className="text-xs font-bold text-gray-300">Intensidad del Desenfoque (Blur)</span>
                          <span className="text-sm font-black text-primary font-mono">{settings.glassBlur}px</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="40"
                          value={settings.glassBlur}
                          onChange={(e) => updateSettings({ glassBlur: parseInt(e.target.value) })}
                          className="w-full accent-primary h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
                        />
                      </div>
                    )}
                    {isVisible('glassOpacity') && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center bg-white/5 p-3 rounded-xl border border-white/5">
                          <span className="text-xs font-bold text-gray-300">Opacidad de Paneles</span>
                          <span className="text-sm font-black text-primary font-mono">{Math.round(settings.glassOpacity * 100)}%</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={settings.glassOpacity * 100}
                          onChange={(e) => updateSettings({ glassOpacity: parseInt(e.target.value) / 100 })}
                          className="w-full accent-primary h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* UI Element Transparency */}
                {isVisible('navOpacity') && (
                  <div className="space-y-4 col-span-full border-t border-white/5 pt-8">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest pl-1">Zonas de Transparencia</label>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="flex flex-col gap-3">
                        <span className="text-xs font-bold text-gray-300">Navegación</span>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={settings.navOpacity * 100}
                          onChange={(e) => updateSettings({ navOpacity: parseInt(e.target.value) / 100 })}
                          className="w-full accent-primary h-1 bg-white/10 rounded-lg appearance-none cursor-pointer"
                        />
                      </div>
                      <div className="flex flex-col gap-3">
                        <span className="text-xs font-bold text-gray-300">Búsqueda</span>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={((settings as any).searchBarOpacity || 0.8) * 100}
                          onChange={(e) => updateSettings({ searchBarOpacity: parseInt(e.target.value) / 100 } as any)}
                          className="w-full accent-primary h-1 bg-white/10 rounded-lg appearance-none cursor-pointer"
                        />
                      </div>
                      <div className="flex flex-col gap-3">
                        <span className="text-xs font-bold text-gray-300">Cabeceras</span>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={(settings.headerOpacity ?? 0.8) * 100}
                          onChange={(e) => updateSettings({ headerOpacity: parseInt(e.target.value) / 100 })}
                          className="w-full accent-primary h-1 bg-white/10 rounded-lg appearance-none cursor-pointer"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Glow & Recommendations */}
                <div className="col-span-full border-t border-white/5 pt-8 space-y-6">
                  {isVisible('cardGlowIntensity') && (
                    <div className="space-y-4">
                      <div className="flex justify-between">
                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Resplandor de Tarjetas</label>
                        <span className="text-sm font-black text-primary">{Math.round((settings.cardGlowIntensity || 0.5) * 100)}%</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={settings.cardGlowIntensity || 0.5}
                        onChange={(e) => updateSettings({ cardGlowIntensity: parseFloat(e.target.value) })}
                        className="w-full accent-primary h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
                      />
                    </div>
                  )}

                  {isVisible('showRecommendations') && (
                    <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5">
                      <div className="flex items-center gap-3">
                        <Eye className="w-5 h-5 text-primary" />
                        <div>
                          <p className="text-sm font-bold text-white">Recomendaciones</p>
                          <p className="text-[9px] text-gray-500 uppercase">Mostrar sugerencias en inicio</p>
                        </div>
                      </div>
                      <div
                        onClick={() => setShowRecommendations(!showRecommendations)}
                        className={`w-12 h-6 rounded-full p-1 transition-colors cursor-pointer flex items-center ${showRecommendations ? 'bg-primary' : 'bg-gray-700'}`}
                      >
                        <div className={`bg-white w-4 h-4 rounded-full transition-transform ${showRecommendations ? 'translate-x-6' : 'translate-x-0'}`} />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between gap-6 pt-6 border-t border-white/5 mt-auto">
                <button
                  onClick={resetSettings}
                  className="px-6 py-3 rounded-xl text-xs font-black uppercase tracking-widest text-gray-500 hover:text-white border border-white/5 hover:bg-white/5 transition-all flex items-center gap-2"
                >
                  <RotateCcw className="w-4 h-4" />
                  Restaurar
                </button>
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className={`px-10 py-3 rounded-xl text-xs font-black uppercase tracking-widest text-white shadow-xl flex items-center gap-2 transition-all hover:scale-105 active:scale-95 ${isSaving ? 'bg-gray-700 cursor-not-allowed opacity-50' : 'bg-primary shadow-primary/30'
                    }`}
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? 'Guardando...' : 'Guardar Todo'}
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