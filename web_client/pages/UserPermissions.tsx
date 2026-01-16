import React from 'react';
import { 
  ArrowLeft, 
  ChevronRight, 
  AtSign, 
  Fingerprint, 
  MessageSquare, 
  HelpCircle, 
  AlertTriangle, 
  Save, 
  History,
  Layers,
  ChevronDown
} from 'lucide-react';

interface UserPermissionsProps {
  onBack: () => void;
}

export const UserPermissions: React.FC<UserPermissionsProps> = ({ onBack }) => {
  return (
    <div className="flex-1 p-4 sm:p-6 lg:p-8 rounded-tl-2xl animate-in fade-in duration-300">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <button 
            onClick={onBack}
            className="p-2 -ml-2 rounded-full hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-6 h-6" />
          </button>
          <div>
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <span>Gestión de Usuarios</span>
              <ChevronRight className="w-4 h-4" />
              <span>Editor de Permisos</span>
            </div>
            <h1 className="text-2xl font-bold text-white">Editar Permisos de Usuario</h1>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* User Header Card */}
            <div className="glass-panel rounded-2xl border border-white/5 p-6 flex items-start sm:items-center gap-5 shadow-lg">
              <div className="relative">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-400 to-cyan-300 p-1">
                  <img alt="Avatar de Usuario" className="w-full h-full rounded-full border-2 border-[#121212] object-cover" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBqCVR3MrJiyoFag8XGuCgMbNarapu_VxgeDQsoaB9VDZuVUJMV9Q944ClsA9RjLw2j4LbtrKMVxPgtT1Q8lkigZrhrBbJkJlSduQZTIlHJHh4f5CveQ9loNSwANXWnhL2xC4iIcRLd0axpZ8tXv2ESzzdjVMPsuBSKBr4tbhjR7WKUYh3muaKDpwWGlaA8MziFkrnpVNMR3yd59NAvbYKpoLSQQicgCMl5msxKkdyeIOcQy_fzuR34HF6Zr7AQEBCufKSbZ2yCs94"/>
                </div>
                <div className="absolute bottom-0 right-0 w-6 h-6 bg-green-500 border-4 border-[#121212] rounded-full"></div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-1">
                  <h2 className="text-xl font-bold text-white truncate">Alex Reader</h2>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-blue-900/30 text-blue-300 border border-blue-500/20">
                    Premium
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-400">
                  <span className="flex items-center gap-1">
                    <AtSign className="w-4 h-4" />
                    alex_reads_alot
                  </span>
                  <span className="flex items-center gap-1 font-mono">
                    <Fingerprint className="w-4 h-4" />
                    ID: 8849102
                  </span>
                </div>
              </div>
              <button className="hidden sm:flex items-center gap-1 px-3 py-1.5 rounded-lg border border-white/10 text-sm font-medium hover:bg-white/5 transition-colors text-gray-300">
                <MessageSquare className="w-4 h-4" />
                Mensaje
              </button>
            </div>

            {/* Access Control */}
            <div className="glass-panel rounded-2xl border border-white/5 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-white/5 bg-white/5">
                <h3 className="font-bold text-white uppercase tracking-wider text-xs">Control de Acceso</h3>
                <p className="text-xs text-gray-400 mt-1">Gestiona qué puede hacer este usuario dentro del bot.</p>
              </div>
              <div className="divide-y divide-white/5">
                
                {/* Tier Selection */}
                <div className="px-6 py-4 flex items-center justify-between gap-4 hover:bg-white/5 transition-colors">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white">Nivel de Usuario</span>
                      <Layers className="w-4 h-4 text-gray-400" />
                    </div>
                    <p className="text-sm text-gray-400">Determina límites de descarga y características.</p>
                  </div>
                  <div className="relative">
                    <select className="appearance-none bg-black/20 border border-white/10 text-white text-sm rounded-lg focus:ring-primary focus:border-primary block w-40 p-2.5 pr-8 cursor-pointer">
                      <option value="basic">Básico (Gratis)</option>
                      <option value="supporter">Supporter</option>
                      <option value="vip" selected>VIP</option>
                      <option value="legend">Leyenda</option>
                    </select>
                    <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none text-gray-500">
                      <ChevronDown className="w-4 h-4" />
                    </div>
                  </div>
                </div>

                {/* Can Report */}
                <div className="px-6 py-4 flex items-center justify-between gap-4 hover:bg-white/5 transition-colors">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white">Puede Reportar</span>
                    </div>
                    <p className="text-sm text-gray-400">Permitir al usuario marcar contenido o reportar errores.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input defaultChecked type="checkbox" className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                {/* Bypass Download Limits */}
                <div className="px-6 py-4 flex items-center justify-between gap-4 hover:bg-white/5 transition-colors">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white">Ignorar Límites de Descarga</span>
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-900/30 text-amber-400 border border-amber-500/20">PREMIUM</span>
                    </div>
                    <p className="text-sm text-gray-400">El usuario no se ve afectado por cuotas diarias.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                {/* Beta Tester Tags */}
                <div className="px-6 py-4 flex items-center justify-between gap-4 hover:bg-white/5 transition-colors">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white">Etiquetas Beta Tester</span>
                    </div>
                    <p className="text-sm text-gray-400">Acceso a funciones experimentales e info de depuración.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input defaultChecked type="checkbox" className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                {/* Admin Access - Red Zone */}
                <div className="px-6 py-4 flex items-center justify-between gap-4 bg-red-900/10 border-l-4 border-l-red-500">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-red-400">Acceso Admin</span>
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                    </div>
                    <p className="text-sm text-red-300/60">Acceso total a ajustes del bot y datos de usuarios.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-red-900 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
              </div>
              
              <div className="px-6 py-4 bg-white/5 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
                <span className="text-xs text-gray-500">Último guardado hace 2 minutos</span>
                <div className="flex items-center gap-3 w-full sm:w-auto">
                  <button onClick={onBack} className="flex-1 sm:flex-none px-4 py-2 rounded-lg text-gray-300 hover:bg-white/10 border border-transparent hover:border-white/10 transition-all text-sm font-medium">
                    Cancelar
                  </button>
                  <button className="flex-1 sm:flex-none px-6 py-2 rounded-lg bg-primary hover:bg-primary-dark text-white shadow-lg shadow-primary/25 transition-all text-sm font-bold flex items-center justify-center gap-2">
                    <Save className="w-4 h-4" />
                    Guardar Cambios
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Logs */}
          <div className="lg:col-span-1">
            <div className="glass-panel rounded-2xl border border-white/5 shadow-sm h-full flex flex-col">
              <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
                <h3 className="font-bold text-white flex items-center gap-2 text-sm uppercase tracking-wider">
                  <History className="w-4 h-4 text-gray-400" />
                  Registro de Cambios
                </h3>
                <button className="text-xs text-primary hover:underline">Ver Todo</button>
              </div>
              <div className="p-4 overflow-y-auto max-h-[600px]">
                <div className="relative pl-4 border-l-2 border-white/10 space-y-6">
                  {/* Log 1 */}
                  <div className="relative">
                    <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-primary ring-4 ring-[#121212]"></div>
                    <p className="text-xs text-gray-500 mb-0.5 font-mono">Hoy, 10:42 AM</p>
                    <p className="text-sm text-gray-200 mb-1">
                      Activado <span className="font-bold text-white">Etiquetas Beta Tester</span>
                    </p>
                    <div className="flex items-center gap-1.5">
                      <div className="w-4 h-4 rounded-full bg-purple-500 flex items-center justify-center text-[8px] text-white font-bold">DV</div>
                      <span className="text-xs text-gray-500">Admin User</span>
                    </div>
                  </div>
                  {/* Log 2 */}
                  <div className="relative">
                    <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-gray-600 ring-4 ring-[#121212]"></div>
                    <p className="text-xs text-gray-500 mb-0.5 font-mono">Ayer, 4:15 PM</p>
                    <p className="text-sm text-gray-200 mb-1">
                      Revocado <span className="font-bold text-white">Ignorar Límites</span>
                    </p>
                    <div className="flex items-center gap-1.5">
                      <div className="w-4 h-4 rounded-full bg-orange-500 flex items-center justify-center text-[8px] text-white font-bold">SYS</div>
                      <span className="text-xs text-gray-500">Auto-Mod Sistema</span>
                    </div>
                  </div>
                  {/* Log 3 */}
                  <div className="relative">
                    <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-gray-600 ring-4 ring-[#121212]"></div>
                    <p className="text-xs text-gray-500 mb-0.5 font-mono">Oct 24, 09:30 AM</p>
                    <p className="text-sm text-gray-200 mb-1">
                      Cambio Nivel a <span className="font-bold text-white">VIP</span>
                    </p>
                    <div className="flex items-center gap-1.5">
                      <div className="w-4 h-4 rounded-full bg-purple-500 flex items-center justify-center text-[8px] text-white font-bold">DV</div>
                      <span className="text-xs text-gray-500">Admin User</span>
                    </div>
                  </div>
                  {/* Log 4 */}
                  <div className="relative">
                    <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-gray-600 ring-4 ring-[#121212]"></div>
                    <p className="text-xs text-gray-500 mb-0.5 font-mono">Oct 12, 11:20 AM</p>
                    <p className="text-sm text-gray-200 mb-1">
                       Usuario Unido
                    </p>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs text-gray-500">ZeepubBot</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};