"use client"

import { Card } from "@/components/ui/card"
import { HelpCircle, BookOpen, Download, Settings, Link2, MessageCircle } from "lucide-react"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Button } from "@/components/ui/button"
import { TransparentHeader } from "@/components/transparent-header"
import { useStrings } from "@/components/strings-provider"

interface Command {
  command: string
  description: string
}

export default function HelpPage() {
  const { t } = useStrings()
  const commands: Command[] = [
    { command: "/start", description: "Inicia el bot y muestra el menú principal" },
    { command: "/help", description: "Muestra esta ayuda" },
    { command: "/search <texto>", description: "Busca libros por título o autor" },
    { command: "/status", description: "Muestra tu estado y límites de descarga" },
    { command: "/latest", description: "Muestra los últimos libros añadidos" },
    { command: "/donar", description: "Información sobre cómo apoyar el proyecto" },
    { command: "/niveles", description: "Muestra los niveles disponibles y sus beneficios" },
  ]

  const faqs = [
    {
      question: "¿Cómo busco un libro?",
      answer:
        "Puedes buscar libros usando el comando /search seguido del título o autor, o simplemente usa la sección de Búsqueda en la mini app.",
    },
    {
      question: "¿Cuántos libros puedo descargar al día?",
      answer:
        "Dependiendo de tu nivel: Lector (5/día), VIP (20/día), Premium (ilimitado). Consulta /status para ver tu límite.",
    },
    {
      question: "¿Cómo funciona el reset de descargas?",
      answer: "El contador de descargas se reinicia automáticamente todos los días a medianoche (00:00).",
    },
    {
      question: "¿El bot funciona en grupos?",
      answer: "Sí, el bot funciona en grupos y canales. Asegúrate de que tenga los permisos necesarios.",
    },
    {
      question: "¿Cómo puedo aumentar mi límite de descargas?",
      answer: "Puedes mejorar tu nivel mediante donaciones. Visita la sección Donar para más información.",
    },
    {
      question: "¿El contenido es legal?",
      answer:
        "ZeePubBot solo enlaza a catálogos OPDS públicos. Es responsabilidad del usuario asegurarse de que el contenido descargado cumple con las leyes de su país.",
    },
  ]

  return (
    <div className="min-h-screen bg-background pt-safe">
      <TransparentHeader />

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* Welcome Card */}
        <Card className="p-6 border-border bg-gradient-to-br from-primary/10 to-primary/5">
          <div className="text-center">
            <HelpCircle className="w-16 h-16 text-primary mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-foreground mb-2">{t("help_hero_title")}</h2>
            <p className="text-muted-foreground leading-relaxed">
              {t("help_hero_desc")}
            </p>
          </div>
        </Card>

        {/* Quick Links */}
        <div className="grid grid-cols-2 gap-3">
          <Card className="p-4 border-border hover:bg-secondary/50 transition-colors cursor-pointer">
            <BookOpen className="w-8 h-8 text-primary mb-2" />
            <h4 className="font-semibold text-sm">Guía Rápida</h4>
          </Card>
          <Card className="p-4 border-border hover:bg-secondary/50 transition-colors cursor-pointer">
            <Download className="w-8 h-8 text-primary mb-2" />
            <h4 className="font-semibold text-sm">Descargar Libros</h4>
          </Card>
          <Card className="p-4 border-border hover:bg-secondary/50 transition-colors cursor-pointer">
            <Settings className="w-8 h-8 text-primary mb-2" />
            <h4 className="font-semibold text-sm">Configuración</h4>
          </Card>
          <Card className="p-4 border-border hover:bg-secondary/50 transition-colors cursor-pointer">
            <Link2 className="w-8 h-8 text-primary mb-2" />
            <h4 className="font-semibold text-sm">Enlaces</h4>
          </Card>
        </div>

        {/* Commands */}
        <div>
          <h3 className="text-lg font-semibold mb-4">{t("help_commands_title")}</h3>
          <Card className="p-4 border-border">
            <div className="space-y-3">
              {commands.map((cmd, index) => (
                <div key={index} className="flex items-start gap-3 py-2">
                  <code className="bg-secondary px-2 py-1 rounded text-xs font-mono text-primary flex-shrink-0">
                    {cmd.command}
                  </code>
                  <p className="text-sm text-muted-foreground">{cmd.description}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* FAQs */}
        <div>
          <h3 className="text-lg font-semibold mb-4">{t("help_faq_title")}</h3>
          <Card className="border-border overflow-hidden">
            <Accordion type="single" collapsible className="w-full">
              {faqs.map((faq, index) => (
                <AccordionItem key={index} value={`item-${index}`} className="border-border px-4">
                  <AccordionTrigger className="text-sm font-semibold text-foreground hover:text-primary">
                    {faq.question}
                  </AccordionTrigger>
                  <AccordionContent className="text-sm text-muted-foreground leading-relaxed">
                    {faq.answer}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </Card>
        </div>

        {/* Contact Support */}
        <Card className="p-6 border-border text-center">
          <MessageCircle className="w-12 h-12 text-primary mx-auto mb-3" />
          <h4 className="font-semibold text-foreground mb-2">{t("help_support_title")}</h4>
          <p className="text-sm text-muted-foreground mb-4">{t("help_support_desc")}</p>
          <Button className="w-full bg-primary hover:bg-primary/90">{t("help_support_btn")}</Button>
        </Card>
      </div>
    </div>
  )
}
