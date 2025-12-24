import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { userId, initData } = body

    if (!initData || !userId) {
      return NextResponse.json({ error: "Missing required data" }, { status: 400 })
    }

    // TODO: Validate initData with bot token
    // import { isValid } from '@telegram-apps/init-data-node/web'
    // const isDataValid = isValid(initData, process.env.BOT_TOKEN!)
    // if (!isDataValid) {
    //   return NextResponse.json({ error: "Invalid init data" }, { status: 401 })
    // }

    const backendUrl = process.env.BOT_BACKEND_URL || "http://localhost:8000"

    const response = await fetch(`${backendUrl}/api/user/access`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.BOT_TOKEN}`,
      },
      body: JSON.stringify({ user_id: userId }),
    })

    if (!response.ok) {
      return NextResponse.json({ error: "Backend error" }, { status: 500 })
    }

    const data = await response.json()

    // Expected response from backend:
    // {
    //   level: { id: "1", name: "Lector", priority: 1, color: "#5EAEE6", hasAccess: true },
    //   hasAccess: true,
    //   isAdmin: false
    // }

    return NextResponse.json({
      level: data.level,
      hasAccess: data.hasAccess,
      isAdmin: data.isAdmin,
    })
  } catch (error) {
    console.error("[v0] Access check error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
