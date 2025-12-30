// Vercel serverless function: proxies GET /api/prolog/health -> PROLOG_API_URL/health
export default async function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  const PROLOG_API_URL = process.env.PROLOG_API_URL;
  if (!PROLOG_API_URL) return res.status(500).json({ error: 'PROLOG_API_URL not set' });

  try {
    const forward = await fetch(`${PROLOG_API_URL}/health`);
    const text = await forward.text();
    res.status(forward.status);
    const ct = forward.headers.get('content-type');
    if (ct) res.setHeader('Content-Type', ct);
    res.send(text);
  } catch (err) {
    res.status(500).json({ error: String(err) });
  }
}
