// pages/api/upload.ts
import type { NextApiRequest, NextApiResponse } from 'next';
import formidable from 'formidable';
import fs from 'fs/promises';

export const config = {
  api: { bodyParser: false },
};

type UploadResponse = { success: boolean; data?: any; error?: string };

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<UploadResponse>
) {
  console.log('=== UPLOAD API CALLED ===');
  console.log('Method:', req.method);
  console.log('Headers:', req.headers);
  
  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, error: 'Only POST allowed' });
  }

  const form = formidable({ multiples: false });

  form.parse(req, async (err, fields, files) => {
    console.log('=== FORM PARSED ===');
    console.log('Parse error:', err);
    console.log('FORM FIELDS:', fields);
    console.log('FORM FILES:', files);
    console.log('Files type:', typeof files);
    console.log('Files keys:', Object.keys(files));

    if (err) {
      console.error('Parse error:', err);
      return res.status(500).json({ success: false, error: 'Form parse error: ' + err.message });
    }

    // pick the first file field:
    const fileEntry = files.file ?? Object.values(files)[0];
    console.log('File entry:', fileEntry);
    console.log('File entry type:', typeof fileEntry);
    console.log('Is array:', Array.isArray(fileEntry));
    
    // Handle case where file is in an array
    const actualFile = Array.isArray(fileEntry) ? fileEntry[0] : fileEntry;
    
    if (!actualFile) {
      console.log('No file uploaded');
      return res.status(400).json({ success: false, error: 'No file uploaded' });
    }

    // Get unit ID from fields
    const unitId = fields.unit?.[0] || fields.unit;
    if (!unitId) {
      return res.status(400).json({ success: false, error: 'Unit ID is required' });
    }

    try {
      const buffer = await fs.readFile(actualFile.filepath);
      console.log('File size:', buffer.length, 'bytes');
      console.log('File name:', actualFile.originalFilename);
      console.log('File type:', actualFile.mimetype);

      // Test if the backend is reachable first
      const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
      console.log('Testing backend connection to:', BACKEND_URL);
      
      try {
        const testRes = await fetch(`${BACKEND_URL}/api/extract/`);
        console.log('Backend test response status:', testRes.status);
      } catch (testErr) {
        console.error('Backend connection test failed:', testErr);
        return res.status(500).json({ 
          success: false, 
          error: 'Cannot connect to backend: ' + (testErr as Error).message 
        });
      }

      // Create a proper file object for the Django backend
      const file = new File([buffer], actualFile.originalFilename || 'document.pdf', {
        type: actualFile.mimetype || 'application/pdf'
      });

      const upstreamForm = new FormData();
      upstreamForm.append('file', file);

      console.log('Sending to:', `${BACKEND_URL}/api/extract/`);
      console.log('FormData entries:');
      for (const [key, value] of upstreamForm.entries()) {
        console.log(`  ${key}:`, value instanceof File ? `File(${value.name}, ${value.size} bytes)` : value);
      }
      
      const upstreamRes = await fetch(`${BACKEND_URL}/api/extract/`, {
        method: 'POST',
        body: upstreamForm,
      });

      console.log('Backend response status:', upstreamRes.status);
      console.log('Backend response headers:', Object.fromEntries(upstreamRes.headers.entries()));

      // Get the response as JSON
      const responseData = await upstreamRes.json();
      console.log('Backend response data:', responseData);

      if (!upstreamRes.ok) {
        console.error('Backend error response:', responseData);
        return res.status(upstreamRes.status).json({ 
          success: false, 
          error: `Backend error (${upstreamRes.status}): ${responseData.error || 'Unknown error'}` 
        });
      }

      const responseText = responseData.text || '';
      const extractionMethod = responseData.extraction_method || 'OCR';
      
      console.log('Extracted text length:', responseText.length);
      console.log('Extraction method:', extractionMethod);
      
      // Also ingest the text into Pinecone for chat functionality
      if (responseText.trim()) {
        try {
          console.log('Ingesting text into Pinecone...');
          const ingestRes = await fetch(`${BACKEND_URL}/api/ingest/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              text: responseText,
              category: unitId, // Use unit ID as category
              chunk_size: 1000,
              chunk_overlap: 200
            }),
          });

          if (ingestRes.ok) {
            const ingestData = await ingestRes.json();
            console.log('Pinecone ingestion successful:', ingestData);
          } else {
            console.warn('Pinecone ingestion failed:', await ingestRes.text());
          }
        } catch (ingestErr) {
          console.warn('Pinecone ingestion error:', ingestErr);
        }
      } else {
        console.warn('No text extracted, skipping Pinecone ingestion');
      }

      // Create a note in the database
      try {
        console.log('Creating note in database...');
        
        const noteRes = await fetch(`${BACKEND_URL}/api/notes/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            unit: unitId,
            title: actualFile.originalFilename || 'Uploaded Document',
            content: responseText,
            summary: responseText.substring(0, 200) + '...', // Simple summary
            file: actualFile.originalFilename || 'document.pdf',
            extraction_method: extractionMethod
          }),
        });

        if (noteRes.ok) {
          const noteData = await noteRes.json();
          console.log('Note created successfully:', noteData);
        } else {
          console.warn('Note creation failed:', await noteRes.text());
        }
      } catch (noteErr) {
        console.warn('Note creation error:', noteErr);
      }
      
      return res.status(200).json({ 
        success: true, 
        data: { 
          text: responseText,
          filename: actualFile.originalFilename,
          unitId: unitId,
          extraction_method: extractionMethod
        } 
      });
    } catch (uploadErr) {
      console.error('Upload-forward error:', uploadErr);
      return res
        .status(500)
        .json({ success: false, error: 'Failed to process file: ' + (uploadErr as Error).message });
    }
  });
}
