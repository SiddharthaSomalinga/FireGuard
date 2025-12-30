// Vercel serverless function: proxies POST /api/prolog/classify -> PROLOG_API_URL/classify
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  const PROLOG_API_URL = process.env.PROLOG_API_URL;
  if (!PROLOG_API_URL) return res.status(500).json({ error: 'PROLOG_API_URL not set' });

  try {
    const body = req.body || null;

    const forward = await fetch(`${PROLOG_API_URL}/classify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // forward optional API key if provided by client
        ...(req.headers['x-api-key'] ? { 'X-API-KEY': req.headers['x-api-key'] } : {}),
      },
      body: body ? JSON.stringify(body) : null,
    });

    const text = await forward.text();
    // mirror status and content-type
    res.status(forward.status);
    const ct = forward.headers.get('content-type');
    if (ct) res.setHeader('Content-Type', ct);
    res.send(text);
  } catch (err) {
    res.status(500).json({ error: String(err) });
  }
}
