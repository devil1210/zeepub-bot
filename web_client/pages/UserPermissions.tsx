import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  ChevronRight,
  AtSign,
  Fingerprint,
  MessageSquare,
  AlertTriangle,
  Save,
  History,
  Layers,
  ChevronDown,
  Loader2
} from 'lucide-react';
import { api } from '../src/services/api';

interface UserPermissionsProps {
  onBack: () => void;
  userId?: string;
  userData?: {
    username: string;
    id: string;
    level: string;
    avatar?: string;
  };
}

interface PermissionsState {
  levelId: number | null;
  levelName: string;
  canReport: boolean;
  bypassLimits: boolean;
  betaTester: boolean;
  isAdmin: boolean;
}

interface Level {
  id: number;
  name: string;
  color: string;
}

export const UserPermissions: React.FC<UserPermissionsProps> = ({ onBack, userId, userData }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Use passed userData immediately for display
  const [displayName, setDisplayName] = useState(userData?.username || 'Usuario');
  const [displayId] = useState(userData?.id || userId || '00000000');
  const [displayLevel, setDisplayLevel] = useState(userData?.level || 'Básico');
  const [displayColor, setDisplayColor] = useState('#6b7280');

  // Available levels from database
  const [allLevels, setAllLevels] = useState<Level[]>([]);

  const [permissions, setPermissions] = useState<PermissionsState>({
    levelId: null,
    levelName: userData?.level || 'Básico',
    canReport: true,
    bypassLimits: false,
    betaTester: false,
    isAdmin: false,
  });

  // Load all available levels and user permissions from API
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);

        // Fetch all available levels
        try {
          const levelsRes = await api.getAdminTiers();
          if (levelsRes.levels && Array.isArray(levelsRes.levels)) {
            setAllLevels(levelsRes.levels.map((l: any) => ({
              id: l.id,
              name: l.name,
              color: l.color || '#6b7280'
            })));
          }
        } catch (e) {
          console.error('Error loading levels:', e);
          // Fallback levels
          setAllLevels([
            { id: 1, name: 'Administrador', color: '#FF6B6B' },
            { id: 2, name: 'Staff', color: '#FF9800' },
            { id: 3, name: 'Premium', color: '#4CAF50' },
            { id: 4, name: 'VIP', color: '#9C27B0' },
            { id: 5, name: 'Patrocinador', color: '#2196F3' },
            { id: 6, name: 'Lector', color: '#9E9E9E' }
          ]);
        }

        // Fetch user permissions if userId is available
        const userIdToFetch = userId || userData?.id;
        if (userIdToFetch) {
          try {
            const res = await api.getUserPermissions(userIdToFetch);
            if (res.success && res.user) {
              if (res.user.username) setDisplayName(res.user.username);
              if (res.user.levelName) setDisplayLevel(res.user.levelName);
              if (res.user.levelColor) setDisplayColor(res.user.levelColor);
              setPermissions({
                levelId: res.user.levelId,
                levelName: res.user.levelName || 'Básico',
                canReport: res.user.canReport ?? true,
                bypassLimits: res.user.bypassLimits ?? false,
                betaTester: res.user.betaTester ?? false,
                isAdmin: res.user.isAdmin ?? false,
              });
            }
          } catch (err: any) {
            console.error('Error loading user permissions:', err);
            // Use userData if API fails
          }
        }
      } catch (err: any) {
        console.error('Error loading data:', err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [userId, userData?.id]);

  // Update level color when level changes
  useEffect(() => {
    const selectedLevel = allLevels.find(l => l.id === permissions.levelId);
    if (selectedLevel) {
      setDisplayLevel(selectedLevel.name);
      setDisplayColor(selectedLevel.color);
    }
  }, [permissions.levelId, allLevels]);

  const handleLevelChange = (levelId: number) => {
    const level = allLevels.find(l => l.id === levelId);
    setPermissions({
      ...permissions,
      levelId,
      levelName: level?.name || 'Básico'
    });
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      const res = await api.saveUserPermissions({
        userId: displayId,
        levelId: permissions.levelId ?? undefined,
        canReport: permissions.canReport,
        bypassLimits: permissions.bypassLimits,
        betaTester: permissions.betaTester,
        isAdmin: permissions.isAdmin,
      });

      if (res.success) {
        setSuccess(true);
        setTimeout(() => setSuccess(false), 3000);
      } else {
        setError(res.message || 'Error al guardar');
      }
    } catch (err: any) {
      setError(err.message || 'Error al guardar permisos');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-10 h-10 text-primary animate-spin" />
          <p className="text-gray-400 text-sm">Cargando permisos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-4 sm:p-6 lg:p-8 rounded-tl-2xl animate-in fade-in duration-300">
      <div className="max-w-6xl mx-auto">
        {/* Error/Success Alerts */}
        {error && (
          <div className="mb-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-green-400 text-sm">
            ✓ Permisos guardados correctamente
          </div>
        )}

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
                  <div
                    className="w-full h-full rounded-full border-2 border-[#121212] flex items-center justify-center text-2xl font-black text-white"
                    style={{ background: `linear-gradient(135deg, ${displayColor}40, ${displayColor}20)` }}
                  >
                    {displayName.charAt(0).toUpperCase()}
                  </div>
                </div>
                <div className="absolute bottom-0 right-0 w-6 h-6 bg-green-500 border-4 border-[#121212] rounded-full"></div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-1">
                  <h2 className="text-xl font-bold text-white truncate">{displayName}</h2>
                  <span
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider border"
                    style={{
                      backgroundColor: `${displayColor}20`,
                      color: displayColor,
                      borderColor: `${displayColor}40`
                    }}
                  >
                    {displayLevel}
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-400">
                  <span className="flex items-center gap-1">
                    <AtSign className="w-4 h-4" />
                    {displayName.toLowerCase().replace(/\s/g, '_')}
                  </span>
                  <span className="flex items-center gap-1 font-mono">
                    <Fingerprint className="w-4 h-4" />
                    ID: {displayId}
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
                    <select
                      value={permissions.levelId || ''}
                      onChange={(e) => handleLevelChange(parseInt(e.target.value))}
                      className="appearance-none bg-black/20 border border-white/10 text-white text-sm rounded-lg focus:ring-primary focus:border-primary block w-48 p-2.5 pr-8 cursor-pointer"
                    >
                      <option value="" disabled>Seleccionar nivel...</option>
                      {allLevels.map((level) => (
                        <option key={level.id} value={level.id} className="bg-gray-900">
                          {level.name}
                        </option>
                      ))}
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
                    <input
                      type="checkbox"
                      checked={permissions.canReport}
                      onChange={(e) => setPermissions({ ...permissions, canReport: e.target.checked })}
                      className="sr-only peer"
                    />
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
                    <input
                      type="checkbox"
                      checked={permissions.bypassLimits}
                      onChange={(e) => setPermissions({ ...permissions, bypassLimits: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                {/* Beta Tester Tags */}
                <div className="px-6 py-4 flex items-center justify-between gap-4 hover:bg-white/5 transition-colors">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white">Etiquetas Beta Tester</span>
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-900/30 text-blue-400 border border-blue-500/20">NEW UI</span>
                    </div>
                    <p className="text-sm text-gray-400">Acceso a la interfaz nueva y funciones experimentales.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={permissions.betaTester}
                      onChange={(e) => setPermissions({ ...permissions, betaTester: e.target.checked })}
                      className="sr-only peer"
                    />
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
                    <input
                      type="checkbox"
                      checked={permissions.isAdmin}
                      onChange={(e) => setPermissions({ ...permissions, isAdmin: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-red-900 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
              </div>

              <div className="px-6 py-4 bg-white/5 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
                <span className="text-xs text-gray-500">Los cambios se aplicarán inmediatamente</span>
                <div className="flex items-center gap-3 w-full sm:w-auto">
                  <button onClick={onBack} className="flex-1 sm:flex-none px-4 py-2 rounded-lg text-gray-300 hover:bg-white/10 border border-transparent hover:border-white/10 transition-all text-sm font-medium">
                    Cancelar
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex-1 sm:flex-none px-6 py-2 rounded-lg bg-primary hover:bg-primary-dark text-white shadow-lg shadow-primary/25 transition-all text-sm font-bold flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    {saving ? 'Guardando...' : 'Guardar Cambios'}
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
                  <div className="relative">
                    <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-primary ring-4 ring-[#121212]"></div>
                    <p className="text-xs text-gray-500 mb-0.5 font-mono">Ahora</p>
                    <p className="text-sm text-gray-200 mb-1">
                      Editando permisos de <span className="font-bold text-primary">{displayName}</span>
                    </p>
                    <div className="flex items-center gap-1.5">
                      <div className="w-4 h-4 rounded-full bg-purple-500 flex items-center justify-center text-[8px] text-white font-bold">A</div>
                      <span className="text-xs text-gray-500">Admin</span>
                    </div>
                  </div>
                  <div className="relative">
                    <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-gray-600 ring-4 ring-[#121212]"></div>
                    <p className="text-xs text-gray-500 mb-0.5 font-mono">Nivel Actual</p>
                    <p className="text-sm text-gray-200 mb-1">
                      <span style={{ color: displayColor }}>{displayLevel}</span>
                    </p>
                  </div>
                  <div className="relative">
                    <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-gray-600 ring-4 ring-[#121212]"></div>
                    <p className="text-xs text-gray-500 mb-0.5 font-mono">ID de Usuario</p>
                    <p className="text-sm text-gray-200 mb-1 font-mono">
                      {displayId}
                    </p>
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