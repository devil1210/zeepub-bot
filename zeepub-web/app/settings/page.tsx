"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"

export default function SettingsPage() {
  const [businessMode, setBusinessMode] = useState(true)
  const [allowGroups, setAllowGroups] = useState(true)
  const [groupPrivacy, setGroupPrivacy] = useState(true)

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-4">
          <Link href="/">
            <button className="text-foreground/60 hover:text-foreground">
              <ArrowLeft className="w-6 h-6" />
            </button>
          </Link>
          <h1 className="text-lg font-semibold">Configuración</h1>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
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
  )
}
