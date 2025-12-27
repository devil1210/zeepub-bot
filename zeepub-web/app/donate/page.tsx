"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Heart, Star, Zap, Crown, CheckCircle } from "lucide-react"

interface Tier {
  name: string
  icon: any
  price: string
  downloads: string
  features: string[]
  color: string
  popular?: boolean
}

import { AccessGuard } from "@/components/access-guard"
import { TransparentHeader } from "@/components/transparent-header"
import { useStrings } from "@/components/strings-provider"

export default function DonatePage() {
  const { t } = useStrings()
  const tiers: Tier[] = [
    {
      name: "Lector",
      icon: Star,
      price: "Gratis",
      downloads: "5 al día",
      features: ["Búsqueda básica", "Descargas limitadas", "Soporte por email"],
      color: "text-muted-foreground",
    },
    {
      name: "VIP",
      icon: Zap,
      price: "$5/mes",
      downloads: "20 al día",
      features: ["Búsqueda avanzada", "20 descargas diarias", "Sin anuncios", "Soporte prioritario"],
      color: "text-primary",
      popular: true,
    },
    {
      name: "Premium",
      icon: Crown,
      price: "$10/mes",
      downloads: "Ilimitado",
      features: [
        "Búsqueda ilimitada",
        "Descargas ilimitadas",
        "Acceso a bibliotecas premium",
        "Sin anuncios",
        "Soporte 24/7",
      ],
      color: "text-yellow-500",
    },
  ]

  return (
    <AccessGuard>
      <div className="min-h-screen bg-background pt-safe">
        <TransparentHeader />


        <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
          {/* Hero Section */}
          <Card className="p-6 border-border bg-gradient-to-br from-primary/10 to-primary/5">
            <div className="text-center">
              <Heart className="w-16 h-16 text-primary mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-foreground mb-2">{t("donate_hero_title")}</h2>
              <p className="text-muted-foreground leading-relaxed">
                {t("donate_hero_desc")}
              </p>
            </div>
          </Card>

          {/* Tiers */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">{t("donate_tier_title")}</h3>

            {tiers.map((tier, index) => {
              const Icon = tier.icon
              return (
                <Card
                  key={index}
                  className={`p-5 border-border relative ${tier.popular ? "border-primary border-2" : ""}`}
                >
                  {tier.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="bg-primary text-primary-foreground text-xs font-semibold px-3 py-1 rounded-full">
                        Más Popular
                      </span>
                    </div>
                  )}

                  <div className="flex items-start gap-4 mb-4">
                    <div
                      className={`w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0 ${tier.color}`}
                    >
                      <Icon className="w-6 h-6" />
                    </div>
                    <div className="flex-1">
                      <h4 className="text-xl font-bold text-foreground mb-1">{tier.name}</h4>
                      <p className="text-2xl font-bold text-primary mb-1">{tier.price}</p>
                      <p className="text-sm text-muted-foreground">{tier.downloads}</p>
                    </div>
                  </div>

                  <ul className="space-y-2 mb-4">
                    {tier.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm">
                        <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                        <span className="text-foreground">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <Button
                    className={`w-full ${tier.popular ? "bg-primary hover:bg-primary/90" : "bg-secondary hover:bg-secondary/90"}`}
                    disabled={tier.price === "Gratis"}
                  >
                    {tier.price === "Gratis" ? "Tu Plan Actual" : `Mejorar a ${tier.name}`}
                  </Button>
                </Card>
              )
            })}
          </div>

          {/* Info Card */}
          <Card className="p-5 border-border bg-secondary/30">
            <h4 className="font-semibold text-foreground mb-2">{t("donate_why_title")}</h4>
            <p className="text-sm text-muted-foreground leading-relaxed mb-3">
              {t("donate_why_desc")}
            </p>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                <span>{t("donate_benefit_1")}</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                <span>{t("donate_benefit_2")}</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                <span>{t("donate_benefit_3")}</span>
              </li>
            </ul>
          </Card>
        </div>
      </div>
    </AccessGuard>
  )
}
