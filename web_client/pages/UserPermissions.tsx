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
  BookOpen,
  Upload,
  Palette,
  Download,
  Activity,
  Shield
} from 'lucide-react';
import { api } from '../src/services/api';
import { useTheme } from '../contexts/ThemeContext';

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
  level: string;
  role: string;
  nickname: string;
  name: string;
  username: string;
  insignias: string[];
  expiresAt: string | null;
  hasLibraryAccess: boolean;
  canRequestBooks: boolean;
  canUploadEpub: boolean;
  allowThemeTemplates: boolean;
  photoUrl?: string;
  settings?: any;
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
  const { settings } = useTheme();
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
  const [allThemes, setAllThemes] = useState<any[]>([]);
  const [initialPermissions, setInitialPermissions] = useState<PermissionsState | null>(null);

  const [permissions, setPermissions] = useState<PermissionsState>({
    levelId: null,
    levelName: userData?.level || 'Básico',
    canReport: true,
    bypassLimits: false,
    betaTester: false,
    isAdmin: false,
    level: userData?.level === 'Administrador' ? 'admin' : 'free',
    nickname: '',
    name: '',
    username: '',
    insignias: [],
    expiresAt: null,
    role: '',
    hasLibraryAccess: true,
    canRequestBooks: true,
    canUploadEpub: false,
    allowThemeTemplates: false,
    photoUrl: userData?.avatar || '',
    settings: {},
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

        // Fetch all available themes
        try {
          const themesRes = await api.getAvailableThemes();
          if (themesRes.success && Array.isArray(themesRes.themes)) {
            setAllThemes(themesRes.themes);
          }
        } catch (e) {
          console.error('Error loading themes:', e);
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
                level: res.user.level || 'free',
                nickname: res.user.nickname || '',
                name: res.user.name || '',
                username: res.user.username || '',
                insignias: Array.isArray(res.user.insignias) ? res.user.insignias : [],
                expiresAt: res.user.expiresAt || null,
                role: res.user.role || '',
                hasLibraryAccess: res.user.hasLibraryAccess ?? true,
                canRequestBooks: res.user.canRequestBooks ?? true,
                canUploadEpub: res.user.canUploadEpub ?? false,
                allowThemeTemplates: res.user.allowThemeTemplates ?? false,
                photoUrl: res.user.photo_url || '',
                settings: res.user.settings || {},
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
          level: tier.name.toLowerCase() === 'administrador' ? 'admin' : (prev.level === 'admin' ? 'admin' : 'free'),
          isAdmin: tier.name.toLowerCase() === 'administrador' || prev.isAdmin,
          bypassLimits: tier.dailyDownloads === -1,
          betaTester: tier.earlyAccess || false,
          hasLibraryAccess: tier.name.toLowerCase() !== 'lector', // For example
          canRequestBooks: true,
          canUploadEpub: tier.canUploadEpub || false,
          allowThemeTemplates: tier.allowThemeTemplates || false
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
          level: tier.name.toLowerCase() === 'administrador' ? 'admin' : 'free',
          role: '',
          canUploadEpub: tier.canUploadEpub || false,
          allowThemeTemplates: tier.allowThemeTemplates || false,
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
        level: permissions.level,
        role: permissions.role,
        nickname: permissions.nickname,
        name: permissions.name,
        username: permissions.username,
        insignias: permissions.insignias,
        expiresAt: permissions.expiresAt,
        canUploadEpub: permissions.canUploadEpub,
        allowThemeTemplates: permissions.allowThemeTemplates,
        settings: permissions.settings,
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
      <div className="max-w-[1800px] mx-auto">
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
            {/* User Header Card (Pro Max) */}
            <div className="relative group mb-8">
              <div
                className="absolute -inset-1 bg-gradient-to-r from-primary/30 to-purple-600/30 rounded-[3rem] blur-2xl opacity-20 group-hover:opacity-40 transition-opacity duration-1000"
                style={{ backgroundColor: `${displayColor}30` }}
              ></div>
              <div className="glass-panel p-10 rounded-[3rem] relative overflow-hidden shadow-premium border-white/10 group-hover:border-white/20 transition-all duration-700">
                <div
                  className="absolute top-0 left-0 w-full h-40 opacity-20"
                  style={{ background: `linear-gradient(135deg, ${displayColor}, transparent)` }}
                ></div>

                <div className="relative flex flex-col md:flex-row items-center gap-10 md:text-left text-center">
                  <div className="relative group/avatar">
                    <div
                      className="absolute -inset-4 rounded-full blur-2xl opacity-20 animate-pulse"
                      style={{ backgroundColor: displayColor }}
                    ></div>
                    <div className="relative w-32 h-32 rounded-[2.5rem] p-1.5 bg-white/10 overflow-hidden shadow-2xl">
                      <div className="w-full h-full rounded-[2.2rem] bg-[#0a0a0c] flex items-center justify-center overflow-hidden">
                        {permissions.photoUrl ? (
                          <img
                            src={permissions.photoUrl.startsWith('http') || permissions.photoUrl.startsWith('/') ? permissions.photoUrl : `/api/profiles/${permissions.photoUrl}`}
                            alt={permissions.name}
                            className="w-full h-full object-cover transition-transform duration-1000 group-hover/avatar:scale-110"
                            onError={(e) => {
                              const target = e.target as HTMLImageElement;
                              target.style.display = 'none';
                              if (target.parentElement) {
                                const span = document.createElement('span');
                                span.className = "text-5xl font-black text-white";
                                span.innerText = permissions.name?.charAt(0).toUpperCase() || permissions.username?.charAt(0).toUpperCase() || 'U';
                                target.parentElement.appendChild(span);
                              }
                            }}
                          />
                        ) : (
                          <span className="text-5xl font-black text-white">
                            {permissions.name?.charAt(0).toUpperCase() || permissions.username?.charAt(0).toUpperCase() || 'U'}
                          </span>
                        )}
                      </div>
                      <div
                        className="absolute bottom-1 right-1 w-8 h-8 border-4 border-[#0a0a0c] rounded-full shadow-lg z-20"
                        style={{ backgroundColor: displayColor }}
                      ></div>
                    </div>
                  </div>

                  <div className="flex-1 min-w-0 space-y-4">
                    <div className="flex flex-col md:flex-row md:items-center gap-4">
                      <h2 className="text-4xl font-black text-white tracking-tighter drop-shadow-2xl">
                        {permissions.name || permissions.username || 'Lector'}
                      </h2>
                      <div
                        className="inline-flex self-center md:self-auto items-center px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-[0.25em] border border-white/10 shadow-xl backdrop-blur-md"
                        style={{
                          backgroundColor: `${displayColor}20`,
                          color: displayColor,
                          borderColor: `${displayColor}30`
                        }}
                      >
                        {displayLevel}
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center justify-center md:justify-start gap-8 text-[11px] font-black text-gray-500 uppercase tracking-widest">
                      <span className="flex items-center gap-2 group/info">
                        <AtSign className="w-4 h-4 text-primary group-hover/info:scale-110 transition-transform" />
                        <span className="group-hover/info:text-gray-300 transition-colors">@{permissions.username || 'usuario'}</span>
                      </span>
                      <span className="flex items-center gap-2 font-mono tabular-nums opacity-60 hover:opacity-100 transition-opacity">
                        <Fingerprint className="w-4 h-4" />
                        ID: {displayId}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-3">
                    <button className="px-8 py-3.5 rounded-2xl bg-white/[0.03] hover:bg-white/10 text-[10px] font-black uppercase tracking-widest transition-all border border-white/5 active:scale-95 shadow-xl flex items-center justify-center gap-2">
                      <MessageSquare className="w-4 h-4" />
                      Chat
                    </button>
                    {(saving || (initialPermissions && JSON.stringify(permissions) !== JSON.stringify(initialPermissions))) && (
                      <button
                        onClick={handleSave}
                        disabled={saving}
                        className="px-8 py-3.5 rounded-2xl bg-primary text-white text-[10px] font-black uppercase tracking-widest transition-all shadow-xl shadow-primary/30 active:scale-95 flex items-center justify-center gap-2"
                      >
                        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        {saving ? 'Aplicando...' : 'Guardar'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
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

            {/* Access Control (Pro Max) */}
            <div className="glass-panel rounded-[3rem] border border-white/5 shadow-premium overflow-hidden relative group/access transition-all duration-700 hover:border-white/10">
              <div
                className="absolute -top-20 -right-20 w-64 h-64 rounded-full blur-[100px] pointer-events-none transition-all duration-1000 opacity-20 group-hover/access:opacity-40"
                style={{ backgroundColor: displayColor, opacity: (settings.cardGlowIntensity || 0.5) * 0.4 }}
              ></div>

              <div className="px-10 py-8 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
                <div>
                  <h3 className="font-black text-white uppercase tracking-[0.4em] text-[11px]">Matriz de Privilegios</h3>
                  <p className="text-[10px] text-gray-500 mt-2 font-black uppercase tracking-widest opacity-60">Control de seguridad y accesos</p>
                </div>
                <div className="p-3 bg-primary/10 rounded-2xl border border-primary/20 text-primary">
                  <Fingerprint className="w-5 h-5" strokeWidth={2.5} />
                </div>
              </div>

              <div className="p-2 space-y-1 relative z-10">
                {/* Tier Selection - Redesigned */}
                <div className="px-8 py-6 flex flex-col md:flex-row md:items-center justify-between gap-6 rounded-[2.5rem] hover:bg-white/[0.03] transition-all group/item">
                  <div className="flex items-center gap-5">
                    <div className="p-4 bg-indigo-500/10 rounded-2xl text-indigo-400 border border-indigo-500/10 group-hover/item:scale-110 group-hover/item:rotate-3 transition-all duration-500">
                      <Layers className="w-6 h-6" strokeWidth={2.5} />
                    </div>
                    <div>
                      <span className="block font-black text-white text-[13px] uppercase tracking-tight">Estatus del Usuario</span>
                      <p className="text-[10px] text-gray-500 mt-1 uppercase font-bold tracking-widest opacity-60">Define el techo de capacidades</p>
                    </div>
                  </div>
                  <div className="relative group/select">
                    <select
                      value={permissions.levelId !== null && permissions.levelId !== undefined ? permissions.levelId : ''}
                      onChange={(e) => handleLevelChange(parseInt(e.target.value))}
                      className="appearance-none bg-white/[0.03] hover:bg-white/[0.07] border border-white/10 text-white text-[11px] font-black uppercase tracking-widest rounded-2xl block w-full md:w-56 px-6 py-4 cursor-pointer focus:ring-2 focus:ring-primary/40 focus:border-primary/40 transition-all outline-none"
                    >
                      <option value="" disabled className="bg-[#121212]">Seleccionar...</option>
                      {allLevels.map((level) => (
                        <option key={level.id} value={level.id} className="bg-[#121212]">
                          {level.name}
                        </option>
                      ))}
                    </select>
                    <div className="absolute inset-y-0 right-0 flex items-center pr-5 pointer-events-none text-gray-500 group-hover/select:text-primary transition-colors">
                      <ChevronDown className="w-4 h-4" />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {[
                    { key: 'canReport', label: 'Reportar Errores', desc: 'Alertar sobre contenido', icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10' },
                    { key: 'bypassLimits', label: 'Sin Límites', desc: 'Descargas infinitas', icon: Download, color: 'text-primary', bg: 'bg-primary/10', badge: 'PREMIUM' },
                    { key: 'betaTester', label: 'Beta Engine', desc: 'Acceso a nuevas funciones', icon: History, color: 'text-blue-400', bg: 'bg-blue-500/10', badge: 'NEW UI' },
                    { key: 'hasLibraryAccess', label: 'Mi Biblioteca', desc: 'Panel de libros locales', icon: Library, color: 'text-purple-400', bg: 'bg-purple-500/10' },
                    { key: 'canRequestBooks', label: 'Pedidos Web', desc: 'Solicitud de contenido', icon: BookOpen, color: 'text-green-400', bg: 'bg-green-500/10' },
                    { key: 'canUploadEpub', label: 'Socio de Datos', desc: 'Subida directa de archivos', icon: Upload, color: 'text-orange-400', bg: 'bg-orange-500/10' },
                    { key: 'allowThemeTemplates', label: 'Estética Libre', desc: 'Uso de temas de autor', icon: Palette, color: 'text-pink-400', bg: 'bg-pink-500/10' },
                  ].map((opt) => (
                    <div
                      key={opt.key}
                      onClick={() => setPermissions({ ...permissions, [opt.key]: !(permissions as any)[opt.key] })}
                      className={`px-6 py-5 flex items-center justify-between rounded-[2.5rem] border transition-all cursor-pointer group/toggle relative overflow-hidden ${(permissions as any)[opt.key]
                        ? 'bg-white/[0.04] border-white/10 shadow-lg'
                        : 'bg-transparent border-transparent opacity-60 hover:opacity-100 hover:bg-white/[0.02]'
                        }`}
                    >
                      <div className="flex items-center gap-4 relative z-10">
                        <div className={`p-3 rounded-2xl transition-all duration-500 ${opt.bg} ${opt.color} border border-white/5 group-hover/toggle:scale-110 group-hover/toggle:rotate-3`}>
                          {opt.icon === Download ? <Download className="w-4.5 h-4.5" /> : opt.icon === History ? <History className="w-4.5 h-4.5" /> : <opt.icon className="w-4.5 h-4.5" />}
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-black text-white text-[11px] uppercase tracking-tight">{opt.label}</span>
                            {opt.badge && (
                              <span className="px-1.5 py-0.5 rounded-md text-[7px] font-black bg-white/10 text-gray-400 border border-white/10">{opt.badge}</span>
                            )}
                          </div>
                          <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest mt-0.5 truncate">{opt.desc}</p>
                        </div>
                      </div>
                      <div className={`
                        w-10 h-6 rounded-full transition-all duration-500 relative flex items-center px-1
                        ${(permissions as any)[opt.key] ? 'bg-primary shadow-lg shadow-primary/20' : 'bg-white/10 border border-white/5'}
                      `}>
                        <div className={`w-4 h-4 rounded-full bg-white transition-all duration-500 shadow-xl ${(permissions as any)[opt.key] ? 'translate-x-4' : 'translate-x-0'}`} />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Admin Access - Red Zone Reimagined */}
                <div className="mx-4 my-4 p-8 rounded-[2.8rem] bg-red-500/5 hover:bg-red-500/[0.08] border border-red-500/20 transition-all group/admin relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover/admin:opacity-10 transition-opacity">
                    <Fingerprint className="w-24 h-24" />
                  </div>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative z-10">
                    <div className="flex items-center gap-5">
                      <div className="p-4 bg-red-500/20 rounded-[1.5rem] text-red-500 border border-red-500/20 group-hover/admin:scale-110 group-hover/admin:-rotate-3 transition-all duration-500 shadow-xl shadow-red-500/10">
                        <AlertTriangle className="w-7 h-7" strokeWidth={2.5} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-black text-white text-base tracking-tight uppercase">Privilegios Root</span>
                          <span className="px-2 py-0.5 bg-red-500 text-white rounded text-[8px] font-black tracking-widest animate-pulse">PELIGRO</span>
                        </div>
                        <p className="text-[10px] text-red-400/60 mt-1 font-black uppercase tracking-widest">Acceso total e irreversible al núcleo</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer group/switch">
                      <input
                        type="checkbox"
                        checked={permissions.isAdmin}
                        onChange={(e) => setPermissions({ ...permissions, isAdmin: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-16 h-8 bg-black/40 border border-white/10 rounded-full peer peer-checked:bg-red-600 peer-checked:border-red-500 transition-all duration-500 flex items-center px-1.5 peer-checked:shadow-[0_0_25px_rgba(239,68,68,0.4)]">
                        <div className="w-5 h-5 bg-gray-500 rounded-full transition-all duration-500 peer-checked:translate-x-8 peer-checked:bg-white shadow-xl" />
                      </div>
                    </label>
                  </div>
                </div>
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

                {/* Functional Role */}
                <div>
                  <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider mb-1">Rol / Etiqueta</label>
                  <input
                    type="text"
                    value={permissions.role}
                    onChange={(e) => setPermissions({ ...permissions, role: e.target.value })}
                    placeholder="Ej: Publicador, Maquetador"
                    className="w-full bg-white/5 border border-white/10 rounded-lg p-2.5 text-sm text-white focus:ring-primary focus:border-primary"
                  />
                </div>

                {/* Name (Telegram) */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1 px-1">Nombre (Real/Telegram)</label>
                  <input
                    type="text"
                    value={permissions.name}
                    readOnly
                    className="w-full bg-white/[0.03] border border-white/5 rounded-xl p-3 text-sm text-gray-400 cursor-not-allowed italic"
                  />
                </div>

                {/* Username (Telegram) */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-1 px-1">Username (Telegram)</label>
                  <input
                    type="text"
                    value={permissions.username}
                    readOnly
                    className="w-full bg-white/[0.03] border border-white/5 rounded-xl p-3 text-sm text-gray-400 cursor-not-allowed italic"
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

              {/* Theme Selector Section */}
              <div className="mt-8 border-t border-white/5 pt-6">
                <div className="flex items-center gap-2 mb-4">
                  <Palette className="w-4 h-4 text-primary" />
                  <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Plantilla Visual (Personalizada)</h4>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="relative">
                    <select
                      onChange={(e) => {
                        const theme = allThemes.find(t => String(t.id) === e.target.value);
                        if (theme) {
                          setPermissions(prev => ({
                            ...prev,
                            settings: {
                              ...prev.settings,
                              theme: theme.theme_type,
                              primaryColor: theme.primaryColor || theme.primary_color,
                              backgroundColor: theme.backgroundColor || theme.background_color,
                              cardColor: theme.cardColor || theme.card_color,
                              glassBlur: theme.glassBlur || theme.glass_blur,
                              glassOpacity: theme.glassOpacity || theme.glass_opacity,
                              navOpacity: theme.navOpacity || theme.nav_opacity,
                              accentOpacity: theme.accentOpacity || theme.accent_opacity,
                              cardGlowIntensity: theme.cardGlowIntensity || theme.card_glow_intensity || 0.5,
                            }
                          }));
                        }
                      }}
                      className="appearance-none w-full bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-white focus:ring-primary focus:border-primary pr-10"
                      defaultValue=""
                    >
                      <option value="" disabled>Aplicar tema guardado...</option>
                      {allThemes.map(t => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 pointer-events-none" />
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-primary/5 border border-primary/20 rounded-xl">
                    <div className="w-8 h-8 rounded-lg" style={{ backgroundColor: permissions.settings?.primaryColor || '#3b82f6' }}></div>
                    <div>
                      <p className="text-[9px] font-black text-primary uppercase tracking-widest">Color Activo</p>
                      <p className="text-[10px] text-gray-400 font-mono">{permissions.settings?.primaryColor || 'N/A'}</p>
                    </div>
                  </div>
                </div>
                <p className="mt-3 text-[9px] text-gray-500 italic">Aplicar una plantilla sobreescribirá los ajustes visuales actuales de este usuario.</p>
              </div>
            </div>

            <div className="px-6 py-4 bg-white/5 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
              <span className="text-xs text-gray-500">Los cambios se aplicarán inmediatamente tras pulsar Aplicar</span>
            </div>
          </div>
        </div>

        {/* Right Column - Logs */}
        <div className="lg:col-span-1">
          <div className="glass-panel rounded-[2rem] border border-white/5 shadow-2xl h-full flex flex-col relative overflow-hidden group/logs">
            <div
              className="absolute -top-10 -right-10 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl pointer-events-none transition-all duration-700 group-hover/logs:bg-opacity-20"
              style={{ opacity: settings.cardGlowIntensity }}
            ></div>

            <div className="px-6 py-5 border-b border-white/5 flex items-center justify-between relative z-10">
              <h3 className="font-black text-white flex items-center gap-2 text-[10px] uppercase tracking-[0.2em]">
                <History className="w-4 h-4 text-gray-500" />
                Registro de Cambios
              </h3>
              <button className="text-[10px] font-black text-primary hover:text-white uppercase tracking-widest transition-colors">Ver Todo</button>
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
    const fromVal = typeof changes.from === 'object' ? (changes.from.name || JSON.stringify(changes.from)) : String(changes.from || '?');
    const toVal = typeof changes.to === 'object' ? (changes.to.name || JSON.stringify(changes.to)) : String(changes.to || '?');
    return `Nivel cambiado: ${fromVal} → ${toVal}`;
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