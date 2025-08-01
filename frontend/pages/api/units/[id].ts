import { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
  const { id } = req.query
  
  try {
    const url = `${BACKEND_URL}/api/units/${id}/`
    
    const response = await fetch(url, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Cookie': req.headers.cookie || '',
      },
      body: req.method === 'PUT' || req.method === 'PATCH' ? JSON.stringify(req.body) : undefined,
    })



    if (req.method === 'DELETE') {
      if (response.ok) {
        return res.status(204).end()
      } else {
        return res.status(response.status).json({ error: 'Failed to delete unit' })
      }
    }
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
  } catch (error: any) {
    console.error('Error in units API:', error)
    return res.status(500).json({ error: 'Internal server error', details: error.message })
  }
} 