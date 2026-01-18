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
  Eye
} from 'lucide-react';
import { ReportIssueModal } from '../components/ReportIssueModal';
import { RequestBookModal } from '../components/RequestBookModal';

interface SettingsProps {
  onNavigate?: (tab: string) => void;
}

export const Settings: React.FC<SettingsProps> = ({ onNavigate }) => {
  const { settings, updateSettings, resetSettings } = useTheme();
  const { user: tgUser, isAdmin, status, customThemes, simulatedLevel, setSimulatedLevel, showRecommendations, setShowRecommendations } = useTelegram();
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const [availableLevels, setAvailableLevels] = useState<Array<{ id: number, name: string, color: string }>>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

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
    if (isAdmin) {
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
  }, [isAdmin]);

  return (
    <div className="max-w-6xl mx-auto pb-32 md:pb-12 p-4 md:p-8 animate-in fade-in duration-300 font-sans text-gray-900 dark:text-gray-100">
      <ReportIssueModal isOpen={isReportModalOpen} onClose={() => setIsReportModalOpen(false)} />
      <RequestBookModal isOpen={isRequestModalOpen} onClose={() => setIsRequestModalOpen(false)} />

      {/* Admin Level Simulation Banner */}
      {isAdmin && (
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
                    {status?.user?.status_label || 'Miembro VIP'}
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

        {/* Right Column: Settings */}
        <div className="lg:col-span-8 space-y-6">

          {/* Appearance Section */}
          <div className="glass-panel p-8 rounded-2xl border border-white/5 shadow-xl">
            <h3 className="text-lg font-black text-white flex items-center gap-2 mb-6 uppercase tracking-tight">
              <Palette className="text-primary w-5 h-5" />
              Apariencia
            </h3>

            <div className="space-y-8">
              {/* Theme Preference */}
              <div>
                <label className="block text-xs font-black text-gray-400 mb-3 uppercase tracking-widest">Preferencia de Tema</label>
                <div className="grid grid-cols-3 gap-4">
                  <label className="cursor-pointer group">
                    <input
                      type="radio"
                      name="theme"
                      className="hidden peer"
                      checked={settings.theme === 'dark'}
                      onChange={() => updateSettings({ theme: 'dark' })}
                    />
                    <div className="h-28 rounded-xl border-2 border-white/10 bg-[#1a1a1e] flex flex-col items-center justify-center gap-2 peer-checked:border-primary peer-checked:ring-1 peer-checked:ring-primary transition-all relative overflow-hidden hover:bg-[#202025]">
                      <div className="absolute inset-0 bg-black/20"></div>
                      <Moon className="text-gray-400 z-10 w-6 h-6" />
                      <span className="text-xs font-bold text-gray-300 z-10 uppercase tracking-wider">Noche</span>
                    </div>
                  </label>
                  <label className="cursor-pointer group">
                    <input
                      type="radio"
                      name="theme"
                      className="hidden peer"
                      checked={settings.theme === 'amoled'}
                      onChange={() => updateSettings({ theme: 'amoled' })}
                    />
                    <div className="h-28 rounded-xl border-2 border-white/10 bg-black flex flex-col items-center justify-center gap-2 peer-checked:border-primary peer-checked:ring-1 peer-checked:ring-primary transition-all hover:border-white/20">
                      <Contrast className="text-white w-6 h-6" />
                      <span className="text-xs font-bold text-white uppercase tracking-wider">AMOLED</span>
                    </div>
                  </label>
                  <label className="cursor-pointer group">
                    <input
                      type="radio"
                      name="theme"
                      className="hidden peer"
                      checked={settings.theme === 'light'}
                      onChange={() => updateSettings({ theme: 'light' })}
                    />
                    <div className="h-28 rounded-xl border-2 border-white/10 bg-white flex flex-col items-center justify-center gap-2 peer-checked:border-primary peer-checked:ring-1 peer-checked:ring-primary transition-all opacity-100 hover:border-gray-300">
                      <Sun className="text-gray-600 w-6 h-6" />
                      <span className="text-xs font-bold text-gray-800 uppercase tracking-wider">Claro</span>
                    </div>
                  </label>
                </div>
              </div>

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
            </div>
          </div>

          {/* User Specific UI Personalization (Visible if tier has customThemes enabled or is Admin) */}
          {(customThemes || isAdmin) && (
            <div className="glass-panel p-8 rounded-2xl border-l-4 border-primary relative overflow-hidden animate-in slide-in-from-bottom-4 duration-500 shadow-xl">
              <h3 className="text-lg font-black text-white flex items-center gap-2 mb-6 uppercase tracking-tight">
                <PenTool className="text-primary w-5 h-5" />
                Personalización de Interfaz
              </h3>

              <div className="space-y-8">
                <div>
                  <label className="block text-[10px] font-black text-gray-500 uppercase tracking-wider mb-2.5">Color de Acento Personal</label>
                  <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                      <input
                        className="w-full pl-10 pr-3 py-2 text-sm font-mono bg-black/20 border-white/10 rounded-lg text-white focus:ring-primary focus:border-primary transition-all uppercase"
                        type="text"
                        value={settings.primaryColor}
                        onChange={(e) => handleColorChange(e.target.value)}
                      />
                      <div className="absolute left-3 top-2.5 w-4 h-4 rounded shadow-sm border border-white/20" style={{ backgroundColor: settings.primaryColor }}></div>
                    </div>
                    <div className="relative overflow-hidden rounded-lg w-10 h-10 border border-white/10">
                      <input
                        className="absolute -top-2 -left-2 w-16 h-16 p-0 border-none bg-transparent cursor-pointer"
                        type="color"
                        value={settings.primaryColor}
                        onChange={(e) => handleColorChange(e.target.value)}
                      />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div>
                    <label className="block text-[10px] font-black text-gray-500 uppercase tracking-wider mb-2.5">Nivel de Glassmorphism (Blur)</label>
                    <div className="pt-2 flex flex-col gap-2">
                      <input
                        className="w-full h-1.5 rounded-lg appearance-none cursor-pointer bg-gray-700 accent-primary"
                        max="40"
                        min="0"
                        type="range"
                        value={settings.glassBlur}
                        onChange={(e) => updateSettings({ glassBlur: parseInt(e.target.value) })}
                      />
                      <div className="flex justify-between text-[10px] text-gray-400 font-medium px-0.5">
                        <span>0px</span>
                        <span className="text-primary font-bold">{settings.glassBlur}px</span>
                        <span>40px</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] font-black text-gray-500 uppercase tracking-wider mb-2.5">Transparencia de Paneles</label>
                    <div className="pt-2 flex flex-col gap-2">
                      <input
                        className="w-full h-1.5 rounded-lg appearance-none cursor-pointer bg-gray-700 accent-primary"
                        max="100"
                        min="10"
                        type="range"
                        value={settings.glassOpacity * 100}
                        onChange={(e) => updateSettings({ glassOpacity: parseInt(e.target.value) / 100 })}
                      />
                      <div className="flex justify-between text-[10px] text-gray-400 font-medium px-0.5">
                        <span>10%</span>
                        <span className="text-primary font-bold">{Math.round(settings.glassOpacity * 100)}%</span>
                        <span>100%</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] font-black text-gray-500 uppercase tracking-wider mb-2.5">Opacidad de Navegación</label>
                    <div className="pt-2 flex flex-col gap-2">
                      <input
                        className="w-full h-1.5 rounded-lg appearance-none cursor-pointer bg-gray-700 accent-primary"
                        max="100"
                        min="10"
                        type="range"
                        value={settings.navOpacity * 100}
                        onChange={(e) => updateSettings({ navOpacity: parseInt(e.target.value) / 100 })}
                      />
                      <div className="flex justify-between text-[10px] text-gray-400 font-medium px-0.5">
                        <span>10%</span>
                        <span className="text-primary font-bold">{Math.round(settings.navOpacity * 100)}%</span>
                        <span>100%</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] font-black text-gray-500 uppercase tracking-wider mb-2.5">Ancho de Portadas (px)</label>
                    <div className="pt-2 flex flex-col gap-2">
                      <input
                        className="w-full h-1.5 rounded-lg appearance-none cursor-pointer bg-gray-700 accent-primary"
                        max="200"
                        min="80"
                        type="range"
                        value={settings.coverWidth}
                        onChange={(e) => updateSettings({ coverWidth: parseInt(e.target.value) })}
                      />
                      <div className="flex justify-between text-[10px] text-gray-400 font-medium px-0.5">
                        <span>80px</span>
                        <span className="text-primary font-bold">{settings.coverWidth}px</span>
                        <span>200px</span>
                      </div>
                    </div>
                  </div>

                  {/* Show Recommendations Toggle - Only for users with custom themes permission */}
                  {customThemes && (
                    <div>
                      <label className="block text-[10px] font-black text-gray-500 uppercase tracking-wider mb-2.5">Mostrar Recomendaciones</label>
                      <div className="flex items-center gap-3">
                        <button
                          onClick={async () => {
                            const newValue = !showRecommendations;
                            try {
                              const { api } = await import('../src/services/api');
                              // Save to backend with consistent camelCase key
                              await api.rpc('update_user_setting', { key: 'showRecommendations', value: newValue });
                              // Update local state via context immediately
                              setShowRecommendations(newValue);
                            } catch (e) {
                              console.error('Failed to update show recommendations setting', e);
                            }
                          }}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${showRecommendations ? 'bg-primary' : 'bg-gray-600'
                            }`}
                        >
                          <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${showRecommendations ? 'translate-x-6' : 'translate-x-1'
                            }`} />
                        </button>
                        <span className="text-xs text-gray-400">
                          {showRecommendations ? 'Visible' : 'Oculto'}
                        </span>
                      </div>
                      <p className="text-[10px] text-gray-500 mt-2">Controla si la sección de recomendaciones aparece en el inicio</p>
                    </div>
                  )}
                </div>
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
                <p className="text-xs text-red-400 mt-1">Si experimentas problemas de visualización, intenta limpiar la caché.</p>
              </div>
              <button
                onClick={handleClearCache}
                className="flex-shrink-0 px-4 py-2 bg-red-900/30 hover:bg-red-900/50 text-red-200 text-[10px] font-black uppercase tracking-widest rounded-lg border border-red-800 transition-colors flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Limpiar Caché
              </button>
            </div>
          </div>

          {/* Action Buttons (Desktop Only - Hidden on Mobile) */}
          <div className="hidden md:flex items-center justify-end gap-3 pt-4">
            <button
              onClick={resetSettings}
              className="px-6 py-3 text-gray-300 hover:bg-white/5 rounded-xl text-xs font-black uppercase tracking-widest transition-colors flex items-center gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              Restaurar
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-6 py-3 bg-primary hover:bg-primary-dark text-white rounded-xl text-xs font-black uppercase tracking-widest shadow-lg shadow-primary/30 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? <RotateCcw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {isSaving ? 'Guardando...' : 'Guardar Cambios'}
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Bottom Floating Action Bar for Settings */}
      <div className="md:hidden fixed bottom-6 left-8 right-8 z-50 animate-in slide-in-from-bottom-4 duration-300">
        <div
          className="glass-panel rounded-3xl p-1 border border-black/10 dark:border-white/10 shadow-2xl flex items-center justify-between overflow-hidden"
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