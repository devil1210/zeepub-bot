import type React from "react"
import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { TelegramProvider } from "@/components/telegram-provider"
import { ThemeProvider } from "@/components/theme-provider"
import { StringsProvider } from "@/components/strings-provider"
import { BottomNav } from "@/components/bottom-nav"
import Script from "next/script"
import "./globals.css"

const _geist = Geist({ subsets: ["latin"] })
const _geistMono = Geist_Mono({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "ZeePubBot Mini App",
  description: "Gestiona tu bot de libros ePub directamente desde Telegram",
  generator: "v0.app",
  icons: {
    icon: [
      {
        url: "/icon-light-32x32.png",
        media: "(prefers-color-scheme: light)",
      },
      {
        url: "/icon-dark-32x32.png",
        media: "(prefers-color-scheme: dark)",
      },
      {
        url: "/icon.svg",
        type: "image/svg+xml",
      },
    ],
    apple: "/apple-icon.png",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="es" className="dark" style={{ backgroundColor: '#1a1a1a' }} suppressHydrationWarning>
      <head>
        <meta name="theme-color" content="#1a1a1a" />
        <meta name="color-scheme" content="dark" />
        <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var savedTheme = localStorage.getItem("theme");
                  var savedColor = localStorage.getItem("primaryColor") || "#3b82f6";
                  var savedScale = localStorage.getItem("uiScale") || "1";
                  var savedAvatarScale = localStorage.getItem("avatarScale") || "1";
                  
                  // Apply Theme
                  var html = document.documentElement;
                  if (savedTheme === 'light') {
                    html.classList.remove('dark');
                    html.style.backgroundColor = '#ffffff';
                  } else {
                    html.classList.add('dark');
                    html.style.backgroundColor = '#1a1a1a';
                  }

                  // Apply Scale
                  html.style.setProperty("--font-scale", savedScale);
                  html.style.fontSize = (parseFloat(savedScale) * 100) + "%";

                  // Apply Animations
                  var savedAnimations = localStorage.getItem("enableAnimations");
                  if (savedAnimations === "true") {
                    html.classList.add("animations-enabled");
                  } else {
                    html.classList.remove("animations-enabled");
                  }

                  // Color Utils
                  function getContrastColor(hex) {
                    var r = parseInt(hex.substr(1, 2), 16);
                    var g = parseInt(hex.substr(3, 2), 16);
                    var b = parseInt(hex.substr(5, 2), 16);
                    var yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
                    return (yiq >= 128) ? '#000000' : '#ffffff';
                  }

                  // Apply Colors
                  var contrast = getContrastColor(savedColor);
                  var style = document.createElement('style');
                  style.id = 'dynamic-theme-colors';
                  style.textContent = 
                    ":root { " +
                    "--primary: " + savedColor + " !important; " +
                    "--primary-foreground: " + contrast + " !important; " +
                    "--ring: " + savedColor + " !important; " +
                    "--accent: " + savedColor + " !important; " +
                    "--accent-foreground: " + contrast + " !important; " +
                    "} " +
                    ".dark { " +
                    "--primary: " + savedColor + " !important; " +
                    "--primary-foreground: " + contrast + " !important; " +
                    "--ring: " + savedColor + " !important; " +
                    "--accent: " + savedColor + " !important; " +
                    "--accent-foreground: " + contrast + " !important; " +
                    "} " +
                    ".bg-primary { background-color: " + savedColor + " !important; color: " + contrast + " !important; } " +
                    ".text-primary { color: " + savedColor + " !important; } " +
                    ".border-primary { border-color: " + savedColor + " !important; }";
                  document.head.appendChild(style);

                } catch (e) {
                  console.error("Error applying immediate theme:", e);
                }
              })();
            `,
          }}
        />
      </head>
      <body className={`font-sans antialiased`}>
        <ThemeProvider>
          <TelegramProvider>
            <StringsProvider>
              <div className="pb-20">{children}</div>
              <BottomNav />
            </StringsProvider>
          </TelegramProvider>
        </ThemeProvider>
        <Analytics />
      </body>
    </html>
  )
}
