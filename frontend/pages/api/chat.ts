// File: pages/api/chat.ts

import { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  console.log('=== CHAT API CALLED ===');
  console.log('Method:', req.method);
  console.log('Body:', req.body);
  
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST')
    return res.status(405).json({ error: 'Method Not Allowed' })
  }

  const { message, documentCategory } = req.body
  console.log('Message:', message);
  console.log('Document category:', documentCategory);
  
  if (!message || typeof message !== 'string') {
    return res.status(400).json({ error: 'Missing or invalid "message" in request body' })
  }

  try {
    // Change this to your actual backend URL if different
    const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
    console.log('Sending to backend:', `${BACKEND_URL}/api/summarize/`);
    console.log('Request body:', JSON.stringify({ 
      question: message,
      namespace: documentCategory,
      top_k: 5
    }));
    
    const response = await fetch(`${BACKEND_URL}/api/summarize/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // If you're using cookie-based auth, forward cookies:
        cookie: req.headers.cookie ?? '',
      },
      body: JSON.stringify({ 
        question: message,
        namespace: documentCategory, // Use the document category as namespace
        top_k: 5
      }),
    })

    console.log('Backend response status:', response.status);
    console.log('Backend response headers:', Object.fromEntries(response.headers.entries()));

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
    console.log('Backend response data:', data);

    if (!response.ok) {
      // Forward backend errors
      return res.status(response.status).json({ error: data })
    }

    // Return the answer from the backend
    return res.status(200).json({ answer: data.answer })
  } catch (err) {
    console.error('Error in /api/chat:', err)
    return res.status(500).json({ error: 'Internal server error' })
  }
}
