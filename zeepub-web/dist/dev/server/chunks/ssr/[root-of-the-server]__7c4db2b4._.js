module.exports = [
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/action-async-storage.external.js [external] (next/dist/server/app-render/action-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/action-async-storage.external.js", () => require("next/dist/server/app-render/action-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}),
"[project]/lib/telegram.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

// Telegram Web App utilities
__turbopack_context__.s([
    "closeTelegramWebApp",
    ()=>closeTelegramWebApp,
    "getTelegramInitData",
    ()=>getTelegramInitData,
    "getTelegramUser",
    ()=>getTelegramUser,
    "getTelegramWebApp",
    ()=>getTelegramWebApp,
    "initTelegramWebApp",
    ()=>initTelegramWebApp
]);
function getTelegramWebApp() {
    if ("TURBOPACK compile-time truthy", 1) return null;
    //TURBOPACK unreachable
    ;
}
function initTelegramWebApp() {
    const webApp = getTelegramWebApp();
    if (!webApp) return null;
    // Expand to full height
    webApp.expand();
    // Set header color to match theme
    webApp.setHeaderColor("#1C2733");
    webApp.setBackgroundColor("#0E1621");
    return webApp;
}
function getTelegramUser() {
    const webApp = getTelegramWebApp();
    return webApp?.initDataUnsafe?.user || null;
}
function closeTelegramWebApp() {
    const webApp = getTelegramWebApp();
    webApp?.close();
}
function getTelegramInitData() {
    const webApp = getTelegramWebApp();
    return webApp?.initData || "";
}
}),
"[project]/hooks/use-telegram.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "useTelegram",
    ()=>useTelegram
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$telegram$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/telegram.ts [app-ssr] (ecmascript)");
"use client";
;
;
function useTelegram() {
    const [webApp, setWebApp] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(null);
    const [user, setUser] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(null);
    const [isReady, setIsReady] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(false);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        const app = (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$telegram$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["initTelegramWebApp"])();
        if (app) {
            setWebApp(app);
            setUser((0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$telegram$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["getTelegramUser"])());
            setIsReady(true);
            // Set ready when the app is loaded
            app.ready();
        }
    }, []);
    return {
        webApp,
        user,
        isReady
    };
}
}),
"[project]/lib/api.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "callBotAPI",
    ()=>callBotAPI,
    "checkAccess",
    ()=>checkAccess,
    "fetchBotFeed",
    ()=>fetchBotFeed,
    "getUserLevel",
    ()=>getUserLevel
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$telegram$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/telegram.ts [app-ssr] (ecmascript)");
;
async function callBotAPI(action, data) {
    const initData = (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$telegram$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["getTelegramInitData"])();
    const response = await fetch("/api/bot", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-telegram-init-data": initData
        },
        body: JSON.stringify({
            action,
            data
        })
    });
    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
}
async function fetchBotFeed(url) {
    const initData = (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$telegram$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["getTelegramInitData"])();
    const queryParam = url ? `?url=${encodeURIComponent(url)}` : "";
    const response = await fetch(`/api/feed${queryParam}`, {
        method: "GET",
        headers: {
            "X-Telegram-Data": initData
        }
    });
    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
}
async function checkAccess(userId) {
    const initData = (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$telegram$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["getTelegramInitData"])();
    const response = await fetch("/api/user/access", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-telegram-init-data": initData
        },
        body: JSON.stringify({
            user_id: userId
        })
    });
    if (!response.ok) {
        throw new Error(`Access check error: ${response.statusText}`);
    }
    return response.json();
}
async function getUserLevel(userId) {
    const initData = (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$telegram$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["getTelegramInitData"])();
    const response = await fetch("/api/user/access", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-telegram-init-data": initData
        },
        body: JSON.stringify({
            user_id: userId
        })
    });
    if (!response.ok) {
        throw new Error(`User level error: ${response.statusText}`);
    }
    const data = await response.json();
    return data.level // Retorna solo la información del nivel
    ;
}
}),
"[project]/components/telegram-provider.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "TelegramProvider",
    ()=>TelegramProvider,
    "useTelegramContext",
    ()=>useTelegramContext
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$hooks$2f$use$2d$telegram$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/hooks/use-telegram.ts [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$api$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/api.ts [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/navigation.js [app-ssr] (ecmascript)");
"use client";
;
;
;
;
;
const TelegramContext = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["createContext"])({
    webApp: null,
    user: null,
    isReady: false,
    hasAccess: null,
    isAdmin: null,
    isAdminMode: false,
    setIsAdminMode: ()=>{}
});
function TelegramProvider({ children }) {
    const telegram = (0, __TURBOPACK__imported__module__$5b$project$5d2f$hooks$2f$use$2d$telegram$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useTelegram"])();
    // Cache expiration time: 5 minutes
    const CACHE_TTL = 5 * 60 * 1000 // 5 minutes in milliseconds
    ;
    const [hasAccess, setHasAccess] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(()=>{
        if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
        ;
        return null;
    });
    const [isAdmin, setIsAdmin] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(()=>{
        if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
        ;
        return null;
    });
    const [isAdminMode, setIsAdminMode] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(()=>{
        if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
        ;
        return false;
    });
    const router = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useRouter"])();
    const pathname = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$navigation$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["usePathname"])();
    const toggleAdminMode = (val)=>{
        setIsAdminMode(val);
        localStorage.setItem('admin_mode', val.toString());
    };
    // Configurar botón de retroceso nativo de Telegram
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        if (telegram.webApp && telegram.isReady) {
            const webApp = telegram.webApp;
            // Configurar el handler del botón de retroceso
            const handleBackButton = ()=>{
                router.back();
            };
            // Mostrar u ocultar el botón según la ruta
            if (pathname === '/') {
                // Ocultar en la página principal
                webApp.BackButton.hide();
            } else {
                // Mostrar en páginas secundarias
                webApp.BackButton.show();
            }
            // Configurar el evento click
            webApp.BackButton.onClick(handleBackButton);
            // Cleanup: remover el listener al desmontar
            return ()=>{
                webApp.BackButton.offClick(handleBackButton);
            };
        }
    }, [
        telegram.webApp,
        telegram.isReady,
        pathname,
        router
    ]);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        async function verify() {
            if (telegram.isReady && telegram.user) {
                // Check if we should use cached data or fetch fresh
                let shouldFetch = true;
                if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
                ;
                if (shouldFetch) {
                    try {
                        const result = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$api$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["checkAccess"])(telegram.user.id);
                        const accessValue = result.hasAccess || result.isAdmin;
                        setHasAccess(accessValue);
                        setIsAdmin(result.isAdmin);
                        localStorage.setItem('access_status', JSON.stringify({
                            hasAccess: accessValue,
                            isAdmin: result.isAdmin,
                            timestamp: Date.now()
                        }));
                        if (!accessValue && pathname !== "/no-access") {
                            router.push("/no-access");
                        }
                    } catch (error) {
                        console.error("Failed to check access:", error);
                        if (pathname !== "/no-access" && hasAccess === null) {
                            router.push("/no-access");
                        }
                    }
                }
            }
        }
        verify();
    }, [
        telegram.isReady,
        telegram.user,
        pathname,
        router
    ]);
    // Security: If user is strictly NOT admin, force admin mode off
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        if (isAdmin === false && isAdminMode) {
            setIsAdminMode(false);
            if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
            ;
        }
    }, [
        isAdmin,
        isAdminMode
    ]);
    const value = {
        ...telegram,
        hasAccess,
        isAdmin,
        isAdminMode,
        setIsAdminMode: toggleAdminMode
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(TelegramContext.Provider, {
        value: value,
        children: children
    }, void 0, false, {
        fileName: "[project]/components/telegram-provider.tsx",
        lineNumber: 174,
        columnNumber: 10
    }, this);
}
function useTelegramContext() {
    return (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useContext"])(TelegramContext);
}
}),
"[project]/components/theme-provider.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "ThemeProvider",
    ()=>ThemeProvider,
    "useTheme",
    ()=>useTheme
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
"use client";
;
;
const ThemeContext = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["createContext"])({
    isDarkMode: true,
    setIsDarkMode: ()=>{},
    primaryColor: "#3b82f6",
    setPrimaryColor: ()=>{},
    uiScale: 1,
    setUiScale: ()=>{},
    avatarScale: 1,
    setAvatarScale: ()=>{}
});
function useTheme() {
    return (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useContext"])(ThemeContext);
}
// Color presets matching interface-config
const colorPresets = [
    {
        name: "Azul",
        value: "#3b82f6",
        dark: "#60a5fa"
    },
    {
        name: "Verde",
        value: "#22c55e",
        dark: "#4ade80"
    },
    {
        name: "Morado",
        value: "#a855f7",
        dark: "#c084fc"
    },
    {
        name: "Rosa",
        value: "#ec4899",
        dark: "#f472b6"
    },
    {
        name: "Naranja",
        value: "#f97316",
        dark: "#fb923c"
    },
    {
        name: "Rojo",
        value: "#ef4444",
        dark: "#f87171"
    },
    {
        name: "Cyan",
        value: "#06b6d4",
        dark: "#22d3ee"
    }
];
// Convert hex to OKLCH for Tailwind compatibility
function hexToOklch(hex) {
    hex = hex.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16) / 255;
    const g = parseInt(hex.substring(2, 4), 16) / 255;
    const b = parseInt(hex.substring(4, 6), 16) / 255;
    const toLinear = (c)=>{
        return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    };
    const rL = toLinear(r);
    const gL = toLinear(g);
    const bL = toLinear(b);
    const x = 0.4124564 * rL + 0.3575761 * gL + 0.1804375 * bL;
    const y = 0.2126729 * rL + 0.7151522 * gL + 0.0721750 * bL;
    const z = 0.0193339 * rL + 0.1191920 * gL + 0.9503041 * bL;
    const xn = 0.95047;
    const yn = 1.00000;
    const zn = 1.08883;
    const fx = x / xn > 0.008856 ? Math.pow(x / xn, 1 / 3) : (903.3 * x / xn + 16) / 116;
    const fy = y / yn > 0.008856 ? Math.pow(y / yn, 1 / 3) : (903.3 * y / yn + 16) / 116;
    const fz = z / zn > 0.008856 ? Math.pow(z / zn, 1 / 3) : (903.3 * z / zn + 16) / 116;
    const L = 116 * fy - 16;
    const a = 500 * (fx - fy);
    const bVal = 200 * (fy - fz);
    const C = Math.sqrt(a * a + bVal * bVal);
    let H = Math.atan2(bVal, a) * 180 / Math.PI;
    if (H < 0) H += 360;
    const l = L / 100;
    const c = C / 150;
    return `${l.toFixed(3)} ${c.toFixed(3)} ${H.toFixed(1)}`;
}
function ThemeProvider({ children }) {
    const [isDarkMode, setIsDarkMode] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(true);
    const [primaryColor, setPrimaryColor] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])("#3b82f6");
    const [uiScale, setUiScale] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(1);
    const [avatarScale, setAvatarScale] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(1);
    const [isLoaded, setIsLoaded] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(false);
    // Load saved settings from localStorage on mount
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        if ("TURBOPACK compile-time truthy", 1) return;
        //TURBOPACK unreachable
        ;
        const savedTheme = undefined;
        const savedColor = undefined;
        const savedScale = undefined;
        const savedAvatarScale = undefined;
    }, []);
    // Apply dark mode class to html element
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        if (!isLoaded) return;
        const html = document.documentElement;
        if (isDarkMode) {
            html.classList.add("dark");
        } else {
            html.classList.remove("dark");
        }
        localStorage.setItem("ui-theme", isDarkMode ? "dark" : "light");
    }, [
        isDarkMode,
        isLoaded
    ]);
    // Apply primary color as CSS variables - use hex directly for accuracy
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        if (!isLoaded) return;
        // Find the correct color variant based on mode
        const selectedPreset = colorPresets.find((c)=>c.value === primaryColor || c.dark === primaryColor);
        const colorToUse = isDarkMode ? selectedPreset?.dark || primaryColor : selectedPreset?.value || primaryColor;
        // Calculate if color is light or dark to set contrasting text
        const getContrastColor = (hex)=>{
            const cleanHex = hex.replace('#', '');
            const r = parseInt(cleanHex.substring(0, 2), 16);
            const g = parseInt(cleanHex.substring(2, 4), 16);
            const b = parseInt(cleanHex.substring(4, 6), 16);
            // Calculate relative luminance
            const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
            return luminance > 0.5 ? '#000000' : '#ffffff';
        };
        const contrastColor = getContrastColor(colorToUse);
        // Create or update dynamic style tag - use hex directly for accurate colors
        let styleTag = document.getElementById("dynamic-theme-colors");
        if (!styleTag) {
            styleTag = document.createElement("style");
            styleTag.id = "dynamic-theme-colors";
            document.head.appendChild(styleTag);
        }
        // Apply primary color and contrasting text color
        styleTag.textContent = `
      :root {
        --primary: ${colorToUse} !important;
        --primary-foreground: ${contrastColor} !important;
        --ring: ${colorToUse} !important;
        --accent: ${colorToUse} !important;
        --accent-foreground: ${contrastColor} !important;
      }
      .dark {
        --primary: ${colorToUse} !important;
        --primary-foreground: ${contrastColor} !important;
        --ring: ${colorToUse} !important;
        --accent: ${colorToUse} !important;
        --accent-foreground: ${contrastColor} !important;
      }
      /* Ensure button and link colors use the primary with contrast text */
      .bg-primary { background-color: ${colorToUse} !important; color: ${contrastColor} !important; }
      .text-primary { color: ${colorToUse} !important; }
      .border-primary { border-color: ${colorToUse} !important; }
    `;
        localStorage.setItem("ui-primary-color", primaryColor);
    }, [
        primaryColor,
        isDarkMode,
        isLoaded
    ]);
    // Apply UI scale
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        if (!isLoaded) return;
        document.documentElement.style.setProperty("--font-scale", uiScale.toString());
        document.documentElement.style.fontSize = `${uiScale * 100}%`;
        localStorage.setItem("ui-scale", uiScale.toString());
    }, [
        uiScale,
        isLoaded
    ]);
    // Save avatar scale
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        if (!isLoaded) return;
        localStorage.setItem("ui-avatar-scale", avatarScale.toString());
    }, [
        avatarScale,
        isLoaded
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(ThemeContext.Provider, {
        value: {
            isDarkMode,
            setIsDarkMode,
            primaryColor,
            setPrimaryColor,
            uiScale,
            setUiScale,
            avatarScale,
            setAvatarScale
        },
        children: children
    }, void 0, false, {
        fileName: "[project]/components/theme-provider.tsx",
        lineNumber: 203,
        columnNumber: 5
    }, this);
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__7c4db2b4._.js.map