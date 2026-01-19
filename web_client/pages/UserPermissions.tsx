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
  Loader2,
  Undo2,
  CheckCircle,
  Home,
  Library,
  BookOpen
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
  // Callbacks for parent navigation control
  onSavingChange?: (saving: boolean) => void;
  onCanUndoChange?: (canUndo: boolean) => void;
  onCanApplyChange?: (canApply: boolean) => void;
  onUndoRef?: (undoFn: () => void) => void;
  onSaveRef?: (saveFn: () => Promise<void>) => void;
  onSaveSuccess?: () => void;
}

interface PermissionsState {
  levelId: number | null;
  levelName: string;
  canReport: boolean;
  bypassLimits: boolean;
  betaTester: boolean;
  isAdmin: boolean;
  role: string;
  nickname: string;
  name: string;
  username: string;
  insignias: string[];
  expiresAt: string | null;
  customStatus: string;
}

interface Level {
  id: number;
  name: string;
  color: string;
}

export const UserPermissions: React.FC<UserPermissionsProps> = ({
  onBack,
  userId,
  userData,
  onSavingChange,
  onCanUndoChange,
  onCanApplyChange,
  onUndoRef,
  onSaveRef,
  onSaveSuccess
}) => {
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
  const [initialPermissions, setInitialPermissions] = useState<PermissionsState | null>(null);

  const [permissions, setPermissions] = useState<PermissionsState>({
    levelId: null,
    levelName: userData?.level || 'Básico',
    canReport: true,
    bypassLimits: false,
    betaTester: false,
    isAdmin: false,
    role: userData?.level === 'Administrador' ? 'admin' : 'free',
    nickname: '',
    name: '',
    username: '',
    insignias: [],
    expiresAt: null,
    customStatus: '',
  });

  // Audit history state
  const [auditHistory, setAuditHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Load all available levels and user permissions from API
  useEffect(() => {
    console.log('[UserPermissions] Component mounted, loading data for:', userId, userData?.id);
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
            console.log('[UserPermissions] API Response:', res);
            if (res.success && res.user) {
              console.log('[UserPermissions] Setting user data:', res.user);
              console.log('[UserPermissions] levelId from API:', res.user.levelId, typeof res.user.levelId);
              if (res.user.username) setDisplayName(res.user.username);
              if (res.user.levelName) setDisplayLevel(res.user.levelName);
              if (res.user.levelColor) setDisplayColor(res.user.levelColor);

              const newPerms = {
                levelId: res.user.levelId ?? null,
                levelName: res.user.levelName || 'Básico',
                canReport: res.user.canReport ?? true,
                bypassLimits: res.user.bypassLimits ?? false,
                betaTester: res.user.betaTester ?? false,
                isAdmin: res.user.isAdmin ?? false,
                role: res.user.role || 'free',
                nickname: res.user.nickname || '',
                name: res.user.name || '',
                username: res.user.username || '',
                insignias: Array.isArray(res.user.insignias) ? res.user.insignias : [],
                expiresAt: res.user.expiresAt || null,
                customStatus: res.user.customStatus || '',
                hasLibraryAccess: res.user.hasLibraryAccess ?? true,
                canRequestBooks: res.user.canRequestBooks ?? true,
              };
              console.log('[UserPermissions] Setting permissions to:', newPerms);
              setPermissions(newPerms);
              setInitialPermissions(newPerms);
            } else {
              console.warn('[UserPermissions] API returned success=false or no user data');
            }
          } catch (err: any) {
            console.error('Error loading user permissions:', err);
          }
        }
      } catch (err: any) {
        console.error('Error loading data:', err);
      } finally {
        setLoading(false);
      }
    };

    const loadAuditHistory = async () => {
      const userIdToFetch = userId || userData?.id;
      if (!userIdToFetch) return;

      try {
        setLoadingHistory(true);
        const res = await api.getUserAuditHistory(userIdToFetch, 50, 0);
        if (res.success && res.history) {
          setAuditHistory(res.history);
        }
      } catch (err) {
        console.error('Error loading audit history:', err);
      } finally {
        setLoadingHistory(false);
      }
    };

    loadData();
    loadAuditHistory();
  }, [userId, userData?.id]);

  // Update level color when level changes
  useEffect(() => {
    const selectedLevel = allLevels.find(l => l.id === permissions.levelId);
    if (selectedLevel) {
      setDisplayLevel(selectedLevel.name);
      setDisplayColor(selectedLevel.color);
    }
  }, [permissions.levelId, allLevels]);

  // Notify parent of saving state changes
  useEffect(() => {
    onSavingChange?.(saving);
  }, [saving, onSavingChange]);

  // Notify parent of canUndo/canApply changes
  useEffect(() => {
    const hasChanges = initialPermissions && JSON.stringify(permissions) !== JSON.stringify(initialPermissions);
    onCanUndoChange?.(!!hasChanges);
    onCanApplyChange?.(!!hasChanges);
  }, [permissions, initialPermissions, onCanUndoChange, onCanApplyChange]);

  // Expose undo and save functions to parent
  useEffect(() => {
    onUndoRef?.(handleUndo);
    onSaveRef?.(handleSave);
  }, [onUndoRef, onSaveRef]);

  const handleLevelChange = async (levelId: number) => {
    const level = allLevels.find(l => l.id === levelId);

    // Update basic info immediately
    setPermissions(prev => ({
      ...prev,
      levelId,
      levelName: level?.name || 'Básico'
    }));

    // Notify user of loading defaults
    setLoading(true);

    try {
      const tierConfig = await api.getTierConfig(level?.name || '');
      if (tierConfig.success && tierConfig.tier) {
        const tier = tierConfig.tier;
        console.log('[UserPermissions] Auto-loading tier defaults for:', tier.name);

        // Load role, bypassLimits, betaTester etc based on level defaults
        setPermissions(prev => ({
          ...prev,
          role: tier.name.toLowerCase() === 'administrador' ? 'admin' : (prev.role === 'admin' ? 'admin' : 'free'),
          isAdmin: tier.name.toLowerCase() === 'administrador' || prev.isAdmin,
          bypassLimits: tier.dailyDownloads === -1,
          betaTester: tier.earlyAccess || false,
          hasLibraryAccess: tier.name.toLowerCase() !== 'lector', // For example
          canRequestBooks: true
        }));
      }
    } catch (err) {
      console.error('Error auto-loading tier config:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUndo = async () => {
    // Reset to the default permissions of the currently selected level
    const currentLevel = allLevels.find(l => l.id === permissions.levelId);
    if (!currentLevel) {
      // Fallback to initial permissions if no level selected
      if (initialPermissions) {
        setPermissions(initialPermissions);
      }
      return;
    }

    try {
      const tierConfig = await api.getTierConfig(currentLevel.name);
      if (tierConfig.success && tierConfig.tier) {
        const tier = tierConfig.tier;

        // Reset permissions to tier defaults
        setPermissions({
          ...permissions,
          levelId: tier.id,
          levelName: tier.name,
          canReport: true,
          bypassLimits: tier.dailyDownloads === -1,
          betaTester: tier.earlyAccess || false,
          isAdmin: tier.name.toLowerCase() === 'administrador',
          role: tier.name.toLowerCase() === 'administrador' ? 'admin' : 'free',
        });
      }
    } catch (err) {
      console.error('Error resetting to tier defaults:', err);
      // Fallback to initial permissions
      if (initialPermissions) {
        setPermissions(initialPermissions);
      }
    }
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
        role: permissions.role,
        nickname: permissions.nickname,
        name: permissions.name,
        username: permissions.username,
        insignias: permissions.insignias,
        expiresAt: permissions.expiresAt,
        customStatus: permissions.customStatus,
      });

      if (res.success) {
        setSuccess(true);
        onSaveSuccess?.();
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
                    className="w-full h-full rounded-full border-2 border-white/20 dark:border-[#121212] flex items-center justify-center text-2xl font-black text-white"
                    style={{ background: `linear-gradient(135deg, ${displayColor}40, ${displayColor}20)` }}
                  >
                    {displayName.charAt(0).toUpperCase()}
                  </div>
                </div>
                <div className="absolute bottom-0 right-0 w-6 h-6 bg-green-500 border-4 border-white dark:border-[#121212] rounded-full"></div>
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

            {/* Action Buttons - Desktop/Tablet */}
            <div className="hidden md:flex items-center justify-end gap-3 mb-6">
              <button
                onClick={handleUndo}
                disabled={!initialPermissions || JSON.stringify(permissions) === JSON.stringify(initialPermissions)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-white/10 text-sm font-bold hover:bg-white/5 transition-all disabled:opacity-30 disabled:cursor-not-allowed text-gray-300"
              >
                <Undo2 className="w-4 h-4" />
                Restablecer
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !initialPermissions || JSON.stringify(permissions) === JSON.stringify(initialPermissions)}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-white text-sm font-bold transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-lg shadow-primary/20"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Guardando...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Guardar Cambios
                  </>
                )}
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
                      value={permissions.levelId !== null && permissions.levelId !== undefined ? permissions.levelId : ''}
                      onChange={(e) => handleLevelChange(parseInt(e.target.value))}
                      className="appearance-none bg-white/5 dark:bg-black/20 border border-black/10 dark:border-white/10 text-gray-900 dark:text-white text-sm rounded-lg focus:ring-primary focus:border-primary block w-48 p-2.5 pr-8 cursor-pointer"
                    >
                      <option value="" disabled className="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">Seleccionar nivel...</option>
                      {allLevels.map((level) => (
                        <option key={level.id} value={level.id} className="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
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
                    <div className="w-11 h-6 bg-gray-200 dark:bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-200 dark:after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
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
                    <div className="w-11 h-6 bg-gray-200 dark:bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-200 dark:after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
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
                    <div className="w-11 h-6 bg-gray-200 dark:bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-200 dark:after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                {/* Library Access Toggle */}
                <div className="px-6 py-4 flex items-center justify-between gap-4 hover:bg-white/5 transition-colors">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white">Acceso a Mi Biblioteca</span>
                      <Library className="w-4 h-4 text-purple-400" />
                    </div>
                    <p className="text-sm text-gray-400">Muestra u oculta la tarjeta "Mi Biblioteca" en el inicio.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={permissions.hasLibraryAccess}
                      onChange={(e) => setPermissions({ ...permissions, hasLibraryAccess: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 dark:bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-200 dark:after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>

                {/* Request Books Toggle */}
                <div className="px-6 py-4 flex items-center justify-between gap-4 hover:bg-white/5 transition-colors">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white">Solicitar Libros</span>
                      <BookOpen className="w-4 h-4 text-green-400" />
                    </div>
                    <p className="text-sm text-gray-400">Permite al usuario solicitar libros y ver la tarjeta en el inicio.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={permissions.canRequestBooks}
                      onChange={(e) => setPermissions({ ...permissions, canRequestBooks: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 dark:bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-200 dark:after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
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
                    <div className="w-11 h-6 bg-gray-200 dark:bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-red-900 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-200 dark:after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
              </div>

              <div className="px-6 py-4 bg-white/5 border-t border-white/5">
                <h3 className="font-bold text-white uppercase tracking-wider text-xs mb-4">Información Estética y Roles</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Nickname / Apodo */}
                  <div>
                    <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Apodo (Elegido por el usuario)</label>
                    <input
                      type="text"
                      value={permissions.nickname}
                      onChange={(e) => setPermissions({ ...permissions, nickname: e.target.value })}
                      placeholder="Ej: El Bibliotecario"
                      className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-sm text-white focus:ring-primary focus:border-primary"
                    />
                  </div>

                  {/* Custom Status */}
                  <div>
                    <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Estado Personalizado</label>
                    <input
                      type="text"
                      value={permissions.customStatus}
                      onChange={(e) => setPermissions({ ...permissions, customStatus: e.target.value })}
                      placeholder="Ej: Miembro Fundador"
                      className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-sm text-white focus:ring-primary focus:border-primary"
                    />
                  </div>

                  {/* Name (Telegram) */}
                  <div>
                    <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Nombre (Real/Telegram)</label>
                    <input
                      type="text"
                      value={permissions.name}
                      onChange={(e) => setPermissions({ ...permissions, name: e.target.value })}
                      className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-sm text-white focus:ring-primary focus:border-primary"
                    />
                  </div>

                  {/* Username (Telegram) */}
                  <div>
                    <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Username (Telegram)</label>
                    <input
                      type="text"
                      value={permissions.username}
                      onChange={(e) => setPermissions({ ...permissions, username: e.target.value })}
                      className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-sm text-white focus:ring-primary focus:border-primary"
                    />
                  </div>

                  {/* Expiration Date */}
                  <div>
                    <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Vence el</label>
                    <input
                      type="date"
                      value={permissions.expiresAt ? permissions.expiresAt.split('T')[0] : ''}
                      onChange={(e) => setPermissions({ ...permissions, expiresAt: e.target.value ? e.target.value + 'T23:59:59' : null })}
                      className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-sm text-white focus:ring-primary focus:border-primary"
                    />
                  </div>

                  {/* Insignias (Multi-select) */}
                  <div>
                    <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Insignias Especiales</label>
                    <div className="flex flex-wrap gap-2 p-2.5 bg-white/5 border border-white/10 rounded-lg min-h-[42px]">
                      {['⭐ Fundador', '🚀 Beta', '🎨 Maquetador', '✍️ Autor', '💎 VIP', '🔥 Top'].map(badge => (
                        <button
                          key={badge}
                          onClick={() => {
                            const newInsignias = permissions.insignias.includes(badge)
                              ? permissions.insignias.filter(b => b !== badge)
                              : [...permissions.insignias, badge];
                            setPermissions({ ...permissions, insignias: newInsignias });
                          }}
                          className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${permissions.insignias.includes(badge)
                            ? 'bg-primary text-white scale-105 shadow-md shadow-primary/20'
                            : 'bg-white/10 text-gray-400 hover:bg-white/20'
                            }`}
                        >
                          {badge}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="px-6 py-4 bg-white/5 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
                <span className="text-xs text-gray-500">Los cambios se aplicarán inmediatamente tras pulsar Aplicar</span>
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
                {loadingHistory ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                  </div>
                ) : auditHistory.length === 0 ? (
                  <div className="relative pl-4 border-l-2 border-white/10 space-y-6">
                    <div className="relative">
                      <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-primary ring-4 ring-white dark:ring-[#121212]"></div>
                      <p className="text-xs text-gray-500 mb-0.5 font-mono">Ahora</p>
                      <p className="text-sm text-gray-200 mb-1">
                        Sin actividad reciente
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="relative pl-4 border-l-2 border-white/10 space-y-6">
                    {auditHistory.map((log, index) => {
                      const isRecent = index === 0;
                      const date = new Date(log.created_at);
                      const timeAgo = getTimeAgo(date);

                      return (
                        <div key={log.id || index} className="relative">
                          <div className={`absolute -left-[21px] top-1 w-3 h-3 rounded-full ${isRecent ? 'bg-primary shadow-[0_0_8px_rgba(43,108,238,0.5)]' : 'bg-gray-600'} ring-4 ring-white dark:ring-[#121212]`}></div>
                          <p className="text-xs text-gray-500 mb-0.5 font-mono">{timeAgo}</p>
                          <p className="text-sm text-gray-200 mb-1">
                            {getChangeDescription(log)}
                          </p>
                          <div className="flex items-center gap-1.5">
                            <div className="w-4 h-4 rounded-full bg-purple-500 flex items-center justify-center text-[8px] text-white font-bold">
                              {log.changed_by_username?.charAt(0).toUpperCase() || 'A'}
                            </div>
                            <span className="text-xs text-gray-500">{log.changed_by_username || 'Admin'}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper function to get time ago
function getTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Ahora';
  if (diffMins < 60) return `Hace ${diffMins}m`;
  if (diffHours < 24) return `Hace ${diffHours}h`;
  if (diffDays < 7) return `Hace ${diffDays}d`;
  return date.toLocaleDateString();
}

// Helper function to get change description
function getChangeDescription(log: any): string {
  const changes = log.changes_summary || {};

  if (log.action === 'update_level' && (changes.from || changes.to)) {
    return `Nivel cambiado: ${changes.from || '?'} → ${changes.to || '?'}`;
  }

  if (log.action === 'update_permissions') {
    const changeKeys = Object.keys(changes);
    if (changeKeys.length === 1) {
      const key = changeKeys[0];
      const change = changes[key];
      return `${formatFieldName(key)}: ${formatValue(change.old)} → ${formatValue(change.new)}`;
    }
    return `${changeKeys.length} permisos actualizados`;
  }

  if (log.action === 'update_profile') {
    const changeKeys = Object.keys(changes);
    if (changeKeys.length === 1) {
      const key = changeKeys[0];
      const change = changes[key];
      return `${formatFieldName(key)}: ${formatValue(change.old)} → ${formatValue(change.new)}`;
    }
    return `Perfil actualizado (${changeKeys.length} campos)`;
  }

  return log.action || 'Cambio realizado';
}

// Helper function to format field names
function formatFieldName(field: string): string {
  const names: Record<string, string> = {
    'level': 'Nivel',
    'role': 'Rol',
    'custom_status': 'Estado',
    'nickname': 'Apodo',
    'name': 'Nombre',
    'username': 'Usuario',
    'beta_tester': 'Beta Tester',
    'expires_at': 'Vencimiento',
    'insignias': 'Insignias',
    'can_report': 'Reportar',
    'bypass_limits': 'Sin Límites'
  };
  return names[field] || field;
}

// Helper function to format values
function formatValue(value: any): string {
  if (value === null || value === undefined) return 'N/A';
  if (typeof value === 'boolean') return value ? 'Sí' : 'No';
  if (Array.isArray(value)) return value.join(', ') || 'Ninguno';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}