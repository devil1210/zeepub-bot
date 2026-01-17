import React, { useState } from 'react';
import {
    ArrowLeft,
    Save,
    Info,
    Gauge,
    Stars,
    Palette,
    History,
    Eye
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

interface TierConfigurationProps {
    tierName: string;
    tierColor: string;
    onBack: () => void;
    onSave?: (config: TierConfig) => void;
}

interface TierConfig {
    name: string;
    icon: string;
    color: string;
    dailyDownloads: number;
    maxConcurrent: number;
    priorityRequests: boolean;
    earlyAccess: boolean;
    customThemes: boolean;
    uiPrimaryColor: string;
    panelTransparency: number;
}

export const TierConfiguration: React.FC<TierConfigurationProps> = ({
    tierName,
    tierColor,
    onBack,
    onSave
}) => {
    const { settings } = useTheme();

    const [config, setConfig] = useState<TierConfig>({
        name: tierName,
        icon: 'verified',
        color: tierColor,
        dailyDownloads: 50,
        maxConcurrent: 3,
        priorityRequests: true,
        earlyAccess: true,
        customThemes: false,
        uiPrimaryColor: settings.primaryColor,
        panelTransparency: 70,
    });

    const handleSave = () => {
        onSave?.(config);
        onBack();
    };

    const Toggle: React.FC<{ checked: boolean; onChange: (val: boolean) => void }> = ({ checked, onChange }) => (
        <button
            type="button"
            onClick={() => onChange(!checked)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${checked ? 'bg-primary' : 'bg-gray-700'
                }`}
        >
            <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'
                    }`}
            />
        </button>
    );

    return (
        <div className="max-w-[1200px] mx-auto w-full flex flex-col gap-8 animate-in fade-in duration-300 px-1">
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                    <button
                        onClick={onBack}
                        className="flex items-center justify-center size-10 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors group"
                    >
                        <ArrowLeft className="w-5 h-5 text-gray-400 group-hover:text-white" />
                    </button>
                    <div className="flex flex-col">
                        <h1 className="text-white text-3xl font-black leading-tight tracking-tight flex items-center gap-3">
                            Configurar Nivel: <span style={{ color: tierColor }}>{tierName}</span>
                            <span className="px-2 py-0.5 rounded-full bg-primary/20 border border-primary/30 text-[10px] font-bold uppercase tracking-widest text-primary">
                                Edit Mode
                            </span>
                        </h1>
                        <p className="text-gray-400 text-sm">Ajusta los permisos y límites específicos para los usuarios {tierName}.</p>
                    </div>
                </div>
                <button
                    onClick={handleSave}
                    className="flex min-w-[140px] cursor-pointer items-center justify-center gap-2 rounded-lg h-11 px-6 bg-primary text-white text-sm font-bold shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all"
                >
                    <Save className="w-5 h-5" />
                    <span>Save Changes</span>
                </button>
            </div>

            {/* Config Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* General Info */}
                <div className="glass-panel p-6 rounded-xl flex flex-col gap-6 border border-white/5">
                    <div className="flex items-center gap-3 border-b border-white/5 pb-4">
                        <Info className="w-5 h-5 text-primary" />
                        <h3 className="text-lg font-bold text-white">General Info</h3>
                    </div>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Tier Name</label>
                            <input
                                type="text"
                                value={config.name}
                                onChange={(e) => setConfig({ ...config, name: e.target.value })}
                                className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:ring-1 focus:ring-primary focus:border-primary transition-all placeholder:text-gray-600"
                                placeholder="e.g. Diamond"
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Icon Name</label>
                                <input
                                    type="text"
                                    value={config.icon}
                                    onChange={(e) => setConfig({ ...config, icon: e.target.value })}
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:ring-1 focus:ring-primary focus:border-primary transition-all"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Badge Color</label>
                                <div className="flex items-center gap-2">
                                    <input
                                        type="color"
                                        value={config.color}
                                        onChange={(e) => setConfig({ ...config, color: e.target.value })}
                                        className="size-10 bg-transparent border-none p-0 cursor-pointer rounded"
                                    />
                                    <span className="text-xs text-gray-400 font-mono uppercase">{config.color}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Limits */}
                <div className="glass-panel p-6 rounded-xl flex flex-col gap-6 border border-white/5">
                    <div className="flex items-center gap-3 border-b border-white/5 pb-4">
                        <Gauge className="w-5 h-5 text-primary" />
                        <h3 className="text-lg font-bold text-white">Limits</h3>
                    </div>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Daily ePub Downloads</label>
                            <input
                                type="number"
                                value={config.dailyDownloads}
                                onChange={(e) => setConfig({ ...config, dailyDownloads: parseInt(e.target.value) || 0 })}
                                className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:ring-1 focus:ring-primary focus:border-primary transition-all"
                            />
                            <p className="mt-1 text-[10px] text-gray-500 italic">Set to -1 for unlimited</p>
                        </div>
                        <div>
                            <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Max Concurrent Downloads</label>
                            <div className="flex items-center gap-4">
                                <input
                                    type="range"
                                    min="1"
                                    max="10"
                                    value={config.maxConcurrent}
                                    onChange={(e) => setConfig({ ...config, maxConcurrent: parseInt(e.target.value) })}
                                    className="flex-1 accent-primary h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
                                />
                                <span className="bg-primary/20 text-primary font-bold px-3 py-1 rounded text-sm min-w-[40px] text-center">
                                    {config.maxConcurrent}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Privileges */}
                <div className="glass-panel p-6 rounded-xl flex flex-col gap-6 border border-white/5">
                    <div className="flex items-center gap-3 border-b border-white/5 pb-4">
                        <Stars className="w-5 h-5 text-primary" />
                        <h3 className="text-lg font-bold text-white">Privileges</h3>
                    </div>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
                            <div className="flex flex-col">
                                <span className="text-sm font-medium text-white">Priority in Requests</span>
                                <span className="text-[10px] text-gray-400 uppercase">Skip the queue processing</span>
                            </div>
                            <Toggle
                                checked={config.priorityRequests}
                                onChange={(val) => setConfig({ ...config, priorityRequests: val })}
                            />
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
                            <div className="flex flex-col">
                                <span className="text-sm font-medium text-white">Early Access</span>
                                <span className="text-[10px] text-gray-400 uppercase">Beta features testing</span>
                            </div>
                            <Toggle
                                checked={config.earlyAccess}
                                onChange={(val) => setConfig({ ...config, earlyAccess: val })}
                            />
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
                            <div className="flex flex-col">
                                <span className="text-sm font-medium text-white">Custom Themes Toggle</span>
                                <span className="text-[10px] text-gray-400 uppercase">Allow UI personalization</span>
                            </div>
                            <Toggle
                                checked={config.customThemes}
                                onChange={(val) => setConfig({ ...config, customThemes: val })}
                            />
                        </div>
                    </div>
                </div>

                {/* Appearance */}
                <div className="glass-panel p-6 rounded-xl flex flex-col gap-6 border border-white/5">
                    <div className="flex items-center gap-3 border-b border-white/5 pb-4">
                        <Palette className="w-5 h-5 text-primary" />
                        <h3 className="text-lg font-bold text-white">Appearance Customization</h3>
                    </div>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">User UI Primary Color</label>
                            <div className="flex items-center gap-3">
                                <div className="flex-1 flex items-center gap-2 p-1.5 bg-black/40 border border-white/10 rounded-lg">
                                    <div
                                        className="size-7 rounded"
                                        style={{ backgroundColor: config.uiPrimaryColor }}
                                    />
                                    <span className="text-xs font-mono text-gray-300 uppercase">{config.uiPrimaryColor}</span>
                                </div>
                                <label className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-medium transition-colors cursor-pointer">
                                    Pick Color
                                    <input
                                        type="color"
                                        value={config.uiPrimaryColor}
                                        onChange={(e) => setConfig({ ...config, uiPrimaryColor: e.target.value })}
                                        className="hidden"
                                    />
                                </label>
                            </div>
                        </div>
                        <div>
                            <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Panel Transparency (Alpha)</label>
                            <div className="flex items-center gap-4">
                                <span className="text-xs text-gray-500 w-8">0%</span>
                                <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    value={config.panelTransparency}
                                    onChange={(e) => setConfig({ ...config, panelTransparency: parseInt(e.target.value) })}
                                    className="flex-1 accent-primary h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
                                />
                                <span className="text-xs text-gray-300 w-10 text-right">{config.panelTransparency}%</span>
                            </div>
                        </div>
                        <div className="mt-2 p-4 rounded-lg bg-primary/5 border border-primary/20 flex items-center gap-3">
                            <Eye className="w-5 h-5 text-primary" />
                            <span className="text-xs text-gray-400">Live preview shown in the TMA dashboard will adapt based on these values.</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="mt-4 pt-6 border-t border-white/10 flex flex-col sm:flex-row justify-between items-center gap-4">
                <div className="flex items-center gap-2 text-gray-500">
                    <History className="w-4 h-4" />
                    <span className="text-xs">Last updated by Admin on {new Date().toLocaleDateString()}</span>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={onBack}
                        className="px-6 py-2 rounded-lg bg-white/5 border border-white/10 text-gray-300 text-sm font-medium hover:bg-white/10 transition-colors"
                    >
                        Discard
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-6 py-2 rounded-lg bg-primary text-white text-sm font-bold shadow-lg shadow-primary/20 hover:bg-primary/90 transition-all"
                    >
                        Apply to All Users
                    </button>
                </div>
            </div>
        </div>
    );
};
