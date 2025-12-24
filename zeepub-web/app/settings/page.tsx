"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Shield, ChevronRight } from "lucide-react"
import Link from "next/link"
import { AccessGuard } from "@/components/access-guard"
import { useAccessControl } from "@/hooks/use-access-control"

export default function SettingsPage() {
  const [businessMode, setBusinessMode] = useState(true)
  const [allowGroups, setAllowGroups] = useState(true)
  const [groupPrivacy, setGroupPrivacy] = useState(true)
  const { isAdmin } = useAccessControl()

  return (
    <AccessGuard>
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
          <div className="max-w-2xl mx-auto px-4 py-3">
            <h1 className="text-lg font-semibold text-center">Configuración</h1>
          </div>
        </header>

        <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
          {isAdmin && (
            <div>
              <h2 className="text-xl font-bold mb-4">Administración</h2>
              <Link href="/admin/levels">
                <Card className="p-4 border-border hover:bg-secondary/50 transition-colors cursor-pointer">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <Shield className="w-6 h-6 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-foreground mb-1">Control de Acceso</h3>
                      <p className="text-sm text-muted-foreground">Gestionar permisos de niveles de usuario</p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                  </div>
                </Card>
              </Link>
            </div>
          )}

          {/* Mode Settings */}
          <div>
            <h2 className="text-xl font-bold mb-4">Configuración de Modo</h2>

            <Card className="p-4 border-border mb-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-foreground">Modo Inline</h3>
                </div>
                <span className="text-sm text-muted-foreground">Off</span>
              </div>
            </Card>

            <Card className="p-4 border-border">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-foreground">Business Mode</h3>
                </div>
                <Switch
                  checked={businessMode}
                  onCheckedChange={setBusinessMode}
                  className="data-[state=checked]:bg-destructive"
                />
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Permite a los bots manejar mensajes y automatizar flujos de trabajo en cuentas de usuario.{" "}
                <button className="text-primary hover:underline">Leer más →</button>
              </p>
            </Card>
          </div>

          {/* Groups and Channels */}
          <div>
            <h2 className="text-xl font-bold mb-4">Grupos y Canales</h2>

            <Card className="p-4 border-border mb-3">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="font-semibold text-foreground">Permitir Grupos</h3>
                </div>
                <Switch checked={allowGroups} onCheckedChange={setAllowGroups} />
              </div>
              <p className="text-sm text-muted-foreground">
                Habilita bots en grupos para tareas como publicar anuncios o celebrar cumpleaños.
              </p>
            </Card>

            <Card className="p-4 border-border mb-3">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="font-semibold text-foreground">Privacidad de Grupo</h3>
                </div>
                <Switch checked={groupPrivacy} onCheckedChange={setGroupPrivacy} />
              </div>
              <p className="text-sm text-muted-foreground">
                Recibe solo mensajes que mencionen o respondan a tu bot, o contengan /comandos.
              </p>
            </Card>

            <Card className="p-4 border-border mb-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-foreground">Derechos de Admin de Grupo</h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">0/10</span>
                  <Switch checked={false} disabled />
                </div>
              </div>
            </Card>

            <Card className="p-4 border-border">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-foreground">Derechos de Admin de Canal</h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">0/9</span>
                  <Switch checked={false} disabled />
                </div>
              </div>
            </Card>

            <p className="text-sm text-muted-foreground mt-4 leading-relaxed">
              Puedes elegir qué derechos solicitará el bot por defecto cuando se agregue como administrador de
              grupo/canal.
            </p>
            <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
              Si el bot no soporta la gestión de grupos o canales, desactiva los switches de grupo o canal.{" "}
              <button className="text-primary hover:underline">Leer más →</button>
            </p>
          </div>

          {/* Web Login */}
          <div>
            <h2 className="text-xl font-bold mb-4">Web Login</h2>

            <Card className="p-4 border-border">
              <Input placeholder="Ingresar URL" className="mb-3 bg-background border-border" />
              <p className="text-sm text-muted-foreground leading-relaxed">
                Vincula tu sitio web con tu bot para usar el Widget de Telegram Login.{" "}
                <button className="text-primary hover:underline">Leer más →</button>
              </p>
            </Card>
          </div>

          {/* Privacy Policy */}
          <div>
            <h2 className="text-xl font-bold mb-4">Política de Privacidad</h2>

            <Card className="p-4 border-border">
              <Input placeholder="Ingresar URL" className="mb-3 bg-background border-border" />
              <p className="text-sm text-muted-foreground leading-relaxed">
                Si no especificas una Política de Privacidad, la{" "}
                <button className="text-primary hover:underline">
                  Política de Privacidad Estándar para Bots y Mini Apps
                </button>{" "}
                se aplicará.
              </p>
            </Card>
          </div>
        </div>
      </div>
    </AccessGuard>
  )
}
