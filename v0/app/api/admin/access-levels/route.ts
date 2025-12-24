import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  try {
    const backendUrl = process.env.BOT_BACKEND_URL || "http://localhost:8000"

    const response = await fetch(`${backendUrl}/api/admin/levels`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.BOT_TOKEN}`,
      },
    })

    if (!response.ok) {
      return NextResponse.json({ error: "Backend error" }, { status: 500 })
    }

    const data = await response.json()

    // Expected response from backend:
    // {
    //   levels: [
    //     { id: "1", name: "Lector", priority: 1, color: "#5EAEE6", hasAccess: true },
    //     { id: "2", name: "Premium", priority: 2, color: "#4CAF50", hasAccess: true },
    //     ...
    //   ]
    // }

    return NextResponse.json({ levels: data.levels })
  } catch (error) {
    console.error("[v0] Fetch levels error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { levels, initData } = body

    if (!initData || !levels) {
      return NextResponse.json({ error: "Missing required data" }, { status: 400 })
    }

    // TODO: Validate initData and check if user is admin
    // import { isValid } from '@telegram-apps/init-data-node/web'
    // const isDataValid = isValid(initData, process.env.BOT_TOKEN!)
    // if (!isDataValid) {
    //   return NextResponse.json({ error: "Invalid init data" }, { status: 401 })
    // }

    const backendUrl = process.env.BOT_BACKEND_URL || "http://localhost:8000"

    const response = await fetch(`${backendUrl}/api/admin/levels`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.BOT_TOKEN}`,
      },
      body: JSON.stringify({ levels }),
    })

    if (!response.ok) {
      return NextResponse.json({ error: "Backend error" }, { status: 500 })
    }

    const data = await response.json()

    return NextResponse.json({ success: true, message: data.message })
  } catch (error) {
    console.error("[v0] Update levels error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
