"use client"

import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import { Layout, X, Settings } from "lucide-react"

interface BookAdminPanelProps {
    show: boolean;
    onClose: () => void;
    badgePosTop: number;
    setBadgePosTop: (val: number) => void;
    badgePosRight: number;
    setBadgePosRight: (val: number) => void;
    badgePosMode: "relative" | "absolute";
    setBadgePosMode: (val: "relative" | "absolute") => void;
    showPosTool: boolean;
    setShowPosTool: (val: boolean) => void;
    isSaving: boolean;
    onSave: () => void;
}

export function BookAdminPanel({
    show,
    onClose,
    badgePosTop,
    setBadgePosTop,
    badgePosRight,
    setBadgePosRight,
    badgePosMode,
    setBadgePosMode,
    showPosTool,
    setShowPosTool,
    isSaving,
    onSave
}: BookAdminPanelProps) {
    if (!show) return null;

    return (
        <div className="fixed bottom-20 right-4 left-4 z-[60] bg-card/95 backdrop-blur-md border border-primary/20 rounded-2xl p-5 shadow-2xl animate-in fade-in slide-in-from-bottom duration-200">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2 text-primary">
                    <Layout className="w-4 h-4" />
                    <h3 className="text-sm font-bold uppercase tracking-wider">Ajustar Posición</h3>
                </div>
                <button
                    onClick={onClose}
                    className="p-1.5 rounded-full hover:bg-secondary transition-colors"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>

            <div className="space-y-6">
                <div className="flex bg-secondary/30 p-1 rounded-xl">
                    <button
                        onClick={() => setBadgePosMode("relative")}
                        className={`flex-1 py-1.5 text-[10px] font-bold rounded-lg transition-all ${badgePosMode === "relative" ? "bg-primary text-primary-foreground shadow-md" : "text-muted-foreground"}`}
                    >
                        RELATIVO A PORTADA
                    </button>
                    <button
                        onClick={() => setBadgePosMode("absolute")}
                        className={`flex-1 py-1.5 text-[10px] font-bold rounded-lg transition-all ${badgePosMode === "absolute" ? "bg-primary text-primary-foreground shadow-md" : "text-muted-foreground"}`}
                    >
                        ABSOLUTO A TARJETA
                    </button>
                </div>

                <div className="space-y-3">
                    <div className="flex justify-between items-center">
                        <Label className="text-xs font-bold opacity-70">Posición Superior (T)</Label>
                        <span className="text-[10px] font-mono bg-primary/10 text-primary px-2 py-0.5 rounded-full">{badgePosTop}px</span>
                    </div>
                    <Slider
                        value={[badgePosTop]}
                        onValueChange={(vals) => setBadgePosTop(vals[0])}
                        max={100}
                        step={1}
                        className="py-2"
                    />
                </div>

                <div className="space-y-3">
                    <div className="flex justify-between items-center">
                        <Label className="text-xs font-bold opacity-70">Posición Derecha (R)</Label>
                        <span className="text-[10px] font-mono bg-primary/10 text-primary px-2 py-0.5 rounded-full">{badgePosRight}px</span>
                    </div>
                    <Slider
                        value={[badgePosRight]}
                        onValueChange={(vals) => setBadgePosRight(vals[0])}
                        max={100}
                        step={1}
                        className="py-2"
                    />
                </div>

                <div className="pt-2">
                    <Button
                        onClick={onSave}
                        disabled={isSaving}
                        className="w-full h-11 rounded-full font-bold shadow-lg shadow-primary/20"
                    >
                        {isSaving ? "Guardando..." : "Guardar Configuración"}
                    </Button>
                </div>
            </div>
        </div>
    );
}
