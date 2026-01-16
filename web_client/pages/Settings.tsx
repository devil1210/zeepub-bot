import React, { useState } from 'react';
import { useTheme, adjustBrightness } from '../contexts/ThemeContext';
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
  ShieldCheck
} from 'lucide-react';
import { ReportIssueModal } from '../components/ReportIssueModal';

interface SettingsProps {
  onNavigate?: (tab: string) => void;
}

export const Settings: React.FC<SettingsProps> = ({ onNavigate }) => {
  const { settings, updateSettings, resetSettings } = useTheme();
  const [isAdmin, setIsAdmin] = useState(true); // Simulation toggle
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  const handleColorChange = (color: string) => {
    updateSettings({
      primaryColor: color,
      primaryColorDark: adjustBrightness(color, -20)
    });
  };

  const handleBack = () => {
    if (onNavigate) {
      onNavigate('dashboard');
    }
  };

  return (
    <div className="max-w-6xl mx-auto pb-32 md:pb-12 p-4 md:p-8 animate-in fade-in duration-300 font-sans text-gray-100">
      <ReportIssueModal isOpen={isReportModalOpen} onClose={() => setIsReportModalOpen(false)} />
      
      {/* Simulation Toggle for Demo */}
      <div className="mb-6 flex justify-end">
        <button 
           onClick={() => setIsAdmin(!isAdmin)} 
           className="text-[10px] uppercase font-bold tracking-widest bg-white/5 px-4 py-2 rounded-lg border border-white/10 hover:bg-white/10 text-gray-400 transition-colors"
        >
          {isAdmin ? 'Simulando: Admin' : 'Simulando: Usuario'}
        </button>
      </div>

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
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuB4k5u3hJ-stj856Bvv__7CQz0Oynqfc4SX4g2PgE825IwIx0nNowP9TzRSjkIDDcA7GwSCgn-oZ_2NTFtopYKSXGpfH4AIHKu57ENJCuaJ4MPydF7uAB_dGFJFsnhhczBJX4I1T2igBXRb8HnhCjflxVCan3rSeljiKNXrDK-tU83AANxLXst6PrRelgTnArgn3vvH88AyJrMPrKjxhPGHyxvLqe-Xz4Po9X6G90nxaYRmNkUbVj9l6r7CP8J3rxfdySsH17xgfBs"
                />
                <div className="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <PenTool className="text-white w-5 h-5" />
                </div>
              </div>
              <h2 className="text-xl font-bold text-white mt-4">Alex Doe</h2>
              <p className="text-sm text-gray-400">@alex_doe</p>
              <div className="mt-3 flex gap-2">
                {isAdmin ? (
                   <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-widest bg-primary/10 text-primary border border-primary/20">
                     Administrador
                   </span>
                ) : (
                   <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-widest bg-purple-500/10 text-purple-400 border border-purple-500/20">
                     Miembro VIP
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
                onClick={() => onNavigate && onNavigate('requests')}
                className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors group cursor-pointer text-left"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/10">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-white">Solicitudes de Libros</p>
                    <p className="text-xs text-gray-400">Gestionar peticiones pendientes</p>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-primary transition-colors" />
              </button>
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

          {/* Admin Only: Tier-Based UI Customization */}
          {isAdmin && (
            <div className="glass-panel p-8 rounded-2xl border-l-4 border-primary relative overflow-hidden animate-in slide-in-from-bottom-4 duration-500 shadow-xl">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <h3 className="text-lg font-black text-white flex items-center gap-2 uppercase tracking-tight">
                  <PenTool className="text-primary w-5 h-5" />
                  Personalización UI por Nivel
                </h3>
                <div className="flex items-center gap-3">
                  <label className="text-xs font-medium text-gray-400 whitespace-nowrap">Editando UI para:</label>
                  <div className="relative">
                    <select className="block w-full pl-3 pr-8 py-1.5 text-xs font-bold border-white/10 bg-black/20 text-white focus:outline-none focus:ring-primary focus:border-primary rounded-lg transition-all shadow-sm">
                      <option>Global (Por Defecto)</option>
                      <option>Nivel Gratuito</option>
                      <option selected>Nivel VIP</option>
                      <option>Administrador</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="space-y-8">
                {/* Theme Visuals & Colors */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <label className="block text-xs font-black text-gray-400 uppercase tracking-widest">Colores y Marca</label>
                      <p className="text-[10px] text-gray-500 mt-1">Define la identidad visual personalizada para este nivel.</p>
                    </div>
                    <span className="text-[9px] bg-primary/10 text-primary px-2.5 py-1 rounded-full flex items-center gap-1.5 border border-primary/20 font-black uppercase tracking-widest">
                       Sincronización Activada
                    </span>
                  </div>

                  <div className="flex flex-col md:flex-row gap-6 p-5 bg-black/20 rounded-xl border border-white/5">
                    <div className="flex flex-col items-center gap-2">
                      <div className="relative w-24 h-24 rounded-xl shadow-lg border-2 border-white/10 overflow-hidden" 
                           style={{ 
                               background: `linear-gradient(45deg, #222 25%, transparent 25%, transparent 75%, #222 75%, #222), linear-gradient(45deg, #222 25%, transparent 25%, transparent 75%, #222 75%, #222)`,
                               backgroundSize: '10px 10px',
                               backgroundPosition: '0 0, 5px 5px'
                           }}>
                        <div className="absolute inset-0 flex items-center justify-center text-center text-[10px] font-black text-white uppercase tracking-widest drop-shadow-md z-10 p-1">Vista Previa</div>
                        <div className="w-full h-full transition-colors duration-200" style={{ backgroundColor: settings.primaryColor, opacity: settings.glassOpacity }}></div>
                      </div>
                      <div className="flex flex-col items-center">
                        <span className="text-[10px] font-mono text-gray-500 uppercase">{settings.primaryColor}</span>
                        <span className="text-[9px] font-bold text-primary uppercase">{Math.round(settings.glassOpacity * 100)}% Opacidad</span>
                      </div>
                    </div>

                    <div className="flex-1 space-y-6">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-[10px] font-black text-gray-500 uppercase tracking-wider mb-2.5">Color de Acento Primario</label>
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
                        <div>
                          <label className="block text-[10px] font-black text-gray-500 uppercase tracking-wider mb-2.5">Transparencia (Alpha)</label>
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
                      </div>
                    </div>
                  </div>
                </div>

                <div className="border-t border-white/5 my-2"></div>

                {/* Glass Intensity */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <div>
                        <label className="text-xs font-black text-gray-400 uppercase tracking-widest">Intensidad Glassmorphism (Blur)</label>
                        <p className="text-[10px] text-gray-500 mt-1">Cantidad de desenfoque de fondo en píxeles</p>
                      </div>
                      <span className="text-xs font-bold text-primary">{settings.glassBlur}px</span>
                    </div>
                    <input 
                        className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-primary" 
                        max="40" 
                        min="0" 
                        type="range" 
                        value={settings.glassBlur}
                        onChange={(e) => updateSettings({ glassBlur: parseInt(e.target.value) })}
                    />
                    <div className="mt-2 flex justify-between text-[10px] text-gray-400 font-medium">
                      <span>Ninguno</span>
                      <span>Medio</span>
                      <span>Alto</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/10 relative overflow-hidden group hover:border-primary/50 transition-colors">
                    <div className="absolute inset-y-0 left-0 w-1 bg-primary"></div>
                    <div>
                      <p className="text-sm font-bold text-white">Inyección CSS Personalizada</p>
                      <p className="text-[10px] text-gray-500 mt-0.5">Aplicar estilos avanzados para VIPs</p>
                    </div>
                    <div className="cursor-pointer relative">
                      <input defaultChecked className="sr-only peer" type="checkbox"/>
                      <div className="w-11 h-6 bg-gray-700 rounded-full peer-checked:bg-primary transition-colors"></div>
                      <div className="absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                    </div>
                  </div>
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
              <button className="flex-shrink-0 px-4 py-2 bg-red-900/30 hover:bg-red-900/50 text-red-200 text-[10px] font-black uppercase tracking-widest rounded-lg border border-red-800 transition-colors flex items-center gap-2">
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
                className="px-6 py-3 bg-primary hover:bg-primary-dark text-white rounded-xl text-xs font-black uppercase tracking-widest shadow-lg shadow-primary/30 transition-colors flex items-center gap-2"
            >
                <Save className="w-4 h-4" />
                Guardar Cambios
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Bottom Floating Action Bar for Settings */}
      <div className="md:hidden fixed bottom-6 left-4 right-4 z-50 animate-in slide-in-from-bottom-4 duration-300">
        <div className="glass-panel rounded-full p-1.5 border border-white/10 shadow-2xl bg-[#0f1115]/95 backdrop-blur-xl flex items-center justify-between gap-1 ring-1 ring-black/5">
          
          <button onClick={handleBack} className="flex-1 flex items-center justify-center gap-2 py-2.5 px-3 hover:bg-white/5 rounded-full transition-colors group text-gray-400 active:text-white">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-[10px] font-black uppercase tracking-widest">Volver</span>
          </button>
          
          <div className="w-px h-6 bg-white/10"></div>

          <button onClick={resetSettings} className="flex-1 flex items-center justify-center gap-2 py-2.5 px-3 hover:bg-white/5 rounded-full transition-colors group text-gray-400 active:text-white">
            <RotateCcw className="w-4 h-4" />
            <span className="text-[10px] font-black uppercase tracking-widest">Restaurar</span>
          </button>

          <button className="flex-[1.4] flex items-center justify-center gap-2 py-2.5 px-4 bg-[#2AABEE] text-white rounded-full shadow-lg shadow-blue-500/20 active:scale-95 transition-all ml-1 hover:bg-[#2AABEE]/90">
            <Save className="w-4 h-4" />
            <span className="text-[10px] font-black uppercase tracking-widest">Guardar</span>
          </button>

        </div>
      </div>

    </div>
  );
};