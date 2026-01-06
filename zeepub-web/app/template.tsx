"use client"

import { useTheme } from "@/components/theme-provider"
// Note: Although I previously thought about using framer-motion, 
// since I don't have it installed and the user wants "system base" performance,
// I'll stick to a CSS-based approach or conditional rendering.
// BUT, the most "fluid" way for page transitions in Next.js is `template.tsx` + Framer Motion.
// Since I can't install packages easily without user input, I will use Tailwind CSS animations
// controlled by the `animations-enabled` class on the <html> tag.
//
// However, `app/template.tsx` is a React component. We can just check the context.

import { useEffect, useState } from "react"
import { usePathname } from "next/navigation"

export default function Template({ children }: { children: React.ReactNode }) {
    // We can't easily use context here because Template might sit outside some providers 
    // depending on strict nesting, but usually it's inside Layout. 
    // Let's rely on the "animations-enabled" class on documentElement for pure CSS,
    // OR we can try to use standard React state if we are sure ThemeProvider wraps Template.
    // In Next.js app dir: RootLayout -> Template -> Page.
    // ThemeProvider is in RootLayout, so we CAN use useTheme().

    // BUT, to keep it simple and performance-focused:
    // We'll standardly render children. The "Fluidity" will be handled by
    // CSS transitions on the router-outlet if possible, or just individual mounting animations.

    // Actually, let's make a simple mount animation wrapper.
    const { enableAnimations } = useTheme()

    if (!enableAnimations) {
        return <>{children}</>
    }

    return (
        <div className="animate-in fade-in slide-in-from-bottom-1 duration-200 ease-out">
            {children}
        </div>
    )
}
