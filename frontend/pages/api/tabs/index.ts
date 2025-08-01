import { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
  
  try {
    console.log('Tabs index API called with method:', req.method)
    console.log('Request body:', req.body)
    console.log('Request query:', req.query)
    
    const url = `${BACKEND_URL}/api/tabs/`
    console.log('Calling backend URL:', url)
    
    const response = await fetch(url, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Cookie': req.headers.cookie || '',
      },
      body: req.method === 'POST' ? JSON.stringify(req.body) : undefined,
    })

    console.log('Backend response status:', response.status)
    console.log('Backend response headers:', Object.fromEntries(response.headers.entries()))

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
    console.log('Backend response data:', data)
    
    if (!response.ok) {
      return res.status(response.status).json(data)
    }
    
    return res.status(response.status).json(data)
  } catch (error: any) {
    console.error('Error in tabs index API:', error)
    return res.status(500).json({ error: 'Internal server error', details: error.message })
  }
} 