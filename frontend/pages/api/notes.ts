import { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
  
  try {
    // Build the URL with query parameters for GET requests
    let url = `${BACKEND_URL}/api/notes/`
    if (req.method === 'GET' && req.query.unit) {
      url += `?unit=${req.query.unit}`
    }
    
    const response = await fetch(url, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        'Cookie': req.headers.cookie || '',
      },
      body: req.method === 'POST' ? JSON.stringify(req.body) : undefined,
    })

    // Check if response is JSON
    const contentType = response.headers.get('content-type')
    if (!contentType || !contentType.includes('application/json')) {
      const text = await response.text()
      console.error('Backend returned non-JSON response:', text.substring(0, 200))
      return res.status(500).json({ 
        error: 'Backend returned non-JSON response',
        details: text.substring(0, 200)
      })
    }

    const data = await response.json()
    
    if (!response.ok) {
      return res.status(response.status).json(data)
    }
    
    return res.status(response.status).json(data)
  } catch (error) {
    console.error('Error in notes API:', error)
    return res.status(500).json({ error: 'Internal server error' })
  }
} 