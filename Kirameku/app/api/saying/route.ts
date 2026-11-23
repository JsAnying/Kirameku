import { NextResponse } from "next/server";

export async function GET() {
  const key = process.env.UAPI_KEY?.trim();
  if (key && !key.startsWith("uapi-")) {
    return NextResponse.json({ error: "一言服务密钥格式不正确" }, { status: 500 });
  }

  try {
    const response = await fetch("https://uapis.cn/api/v1/saying", {
      headers: key ? { Authorization: `Bearer ${key}` } : {},
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });

    if (!response.ok) {
      const message = response.status === 429
        ? "请求过于频繁，请稍后再试"
        : response.status === 500
          ? "一言服务暂时不可用，请稍后再试"
          : "一言获取失败，请稍后再试";
      return NextResponse.json({ error: message }, { status: response.status === 429 ? 429 : 502 });
    }

    const data: unknown = await response.json();
    if (!data || typeof data !== "object" || !("text" in data) || typeof data.text !== "string" || !data.text.trim()) {
      return NextResponse.json({ error: "一言服务返回了无效内容" }, { status: 502 });
    }
    return NextResponse.json({ text: data.text }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    const message = error instanceof Error && error.name === "TimeoutError"
      ? "请求超时，请稍后重试"
      : "一言获取失败，请检查网络后重试";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
