
import { useState, useEffect } from 'react'

type Tab = {
  id: string;
  name: string;
  color: string;
  units_count: number;
}

type Unit = {
  id: string;
  tab: string;
  name: string;
  description: string;
  order: number;
  notes_count: number;
  created_at: string;
}

type Note = {
  id: string;
  unit: string;
  unit_name: string;
  title: string;
  content: string;
  summary: string;
  file: string;
  created_at: string;
  extraction_method?: string;
}

type ChatHistory = { [unitId: string]: string[]; }

export default function Home() {
  const [tabs, setTabs] = useState<Tab[]>([])
  const [activeTab, setActiveTab] = useState<string | null>(null)
  const [units, setUnits] = useState<Unit[]>([])
  const [activeUnit, setActiveUnit] = useState<string | null>(null)
  const [notes, setNotes] = useState<Note[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [message, setMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<ChatHistory>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showNewTabForm, setShowNewTabForm] = useState(false)
  const [newTabName, setNewTabName] = useState('')
  const [newTabColor, setNewTabColor] = useState('#007bff')
  const [showNewUnitForm, setShowNewUnitForm] = useState(false)
  const [newUnitName, setNewUnitName] = useState('')
  const [newUnitDescription, setNewUnitDescription] = useState('')

  useEffect(() => { fetchTabs() }, [])
  useEffect(() => { 
    if (activeTab) { 
      fetchUnits(activeTab) 
    } else {
      setUnits([])
      setActiveUnit(null)
    }
  }, [activeTab])
  useEffect(() => { 
    if (activeUnit) { 
      setNotes([])
      fetchNotes(activeUnit) 
    } else {
      setNotes([])
    }
  }, [activeUnit])
  useEffect(() => {
    if (activeUnit && !chatHistory[activeUnit]) {
      setChatHistory(prev => ({ ...prev, [activeUnit]: [] }))
    }
  }, [activeUnit, chatHistory])

  const fetchTabs = async () => {
    try {
      const res = await fetch('/api/tabs')
      if (res.ok) {
        const data = await res.json()
        setTabs(data)
        if (data.length > 0 && !activeTab) {
          setActiveTab(data[0].id)
        }
      }
    } catch (err) {
      console.error('Error fetching tabs:', err)
    }
  }

  const fetchUnits = async (tabId: string) => {
    try {
      const res = await fetch(`/api/units?tab=${tabId}`)
      if (res.ok) {
        const data = await res.json()
        setUnits(data)
        if (data.length > 0 && !activeUnit) {
          setActiveUnit(data[0].id)
        } else if (data.length === 0) {
          setActiveUnit(null)
          setNotes([])
        }
      } else {
        console.error('Failed to fetch units:', res.status, res.statusText)
      }
    } catch (err) {
      console.error('Error fetching units:', err)
    }
  }

  const fetchNotes = async (unitId: string) => {
    try {
      const res = await fetch(`/api/notes?unit=${unitId}`)
      if (res.ok) {
        const data = await res.json()
        setNotes(data)
      }
    } catch (err) {
      console.error('Error fetching notes:', err)
    }
  }

  const createTab = async () => {
    if (!newTabName.trim()) return
    
    try {
      const res = await fetch('/api/tabs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newTabName, color: newTabColor })
      })
      
      if (res.ok) {
        const newTab = await res.json()
        setTabs(prev => [...prev, newTab])
        setActiveTab(newTab.id)
        setUnits([])
        setActiveUnit(null)
        setNotes([])
        setNewTabName('')
        setNewTabColor('#007bff')
        setShowNewTabForm(false)
      }
    } catch (err) {
      console.error('Error creating tab:', err)
    }
  }

  const createUnit = async () => {
    if (!newUnitName.trim() || !activeTab) return
    
    try {
      const res = await fetch('/api/units', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          tab: activeTab, 
          name: newUnitName, 
          description: newUnitDescription 
        })
      })
      
      if (res.ok) {
        const newUnit = await res.json()
        setUnits(prev => [...prev, newUnit])
        setActiveUnit(newUnit.id)
        setChatHistory(prev => ({ ...prev, [newUnit.id]: [] }))
        setNewUnitName('')
        setNewUnitDescription('')
        setShowNewUnitForm(false)
      } else {
        const errorData = await res.json()
        let errorMessage = 'Failed to create unit'
        
        if (errorData.non_field_errors && errorData.non_field_errors.length > 0) {
          errorMessage = errorData.non_field_errors[0]
        } else if (errorData.name && errorData.name.length > 0) {
          errorMessage = errorData.name[0]
        }
        
        alert(errorMessage)
      }
    } catch (err) {
      console.error('Error creating unit:', err)
      alert('Failed to create unit. Please try again.')
    }
  }

  const deleteTab = async (tabId: string) => {
    if (!confirm('Are you sure you want to delete this tab? This will also delete all units and notes in this tab.')) {
      return
    }
    
    try {
      const res = await fetch(`/api/tabs/${tabId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (res.ok) {
        setTabs(prev => prev.filter(tab => tab.id !== tabId))
        
        setChatHistory(prev => {
          const newHistory = { ...prev }
          units.forEach(unit => {
            if (unit.tab === tabId) {
              delete newHistory[unit.id]
            }
          })
          return newHistory
        })
        
        if (activeTab === tabId) {
          const remainingTabs = tabs.filter(tab => tab.id !== tabId)
          if (remainingTabs.length > 0) {
            setActiveTab(remainingTabs[0].id)
          } else {
            setActiveTab(null)
            setUnits([])
            setActiveUnit(null)
            setNotes([])
          }
        }
      }
    } catch (err) {
      console.error('Error deleting tab:', err)
    }
  }

  const deleteUnit = async (unitId: string) => {
    if (!confirm('Are you sure you want to delete this unit? This will also delete all notes in this unit.')) {
      return
    }
    
    try {
      const res = await fetch(`/api/units/${unitId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (res.ok) {
        setUnits(prev => prev.filter(unit => unit.id !== unitId))
        
        setChatHistory(prev => {
          const newHistory = { ...prev }
          delete newHistory[unitId]
          return newHistory
        })
        
        if (activeUnit === unitId) {
          const remainingUnits = units.filter(unit => unit.id !== unitId)
          if (remainingUnits.length > 0) {
            setActiveUnit(remainingUnits[0].id)
          } else {
            setActiveUnit(null)
            setNotes([])
          }
        }
      } else {
        console.error('Failed to delete unit:', res.status, res.statusText)
        const errorData = await res.json().catch(() => ({}))
        console.error('Error details:', errorData)
        
        if (activeTab) {
          console.log('Refreshing units list due to deletion error')
          fetchUnits(activeTab)
        }
        
        alert('Failed to delete unit. The unit may have already been deleted or no longer exists.')
      }
    } catch (err) {
      console.error('Error deleting unit:', err)
    }
  }

  const handleUpload = async () => {
    if (!file || !activeUnit) {
      setError('Please select a file and a unit first')
      return
    }

    setLoading(true)
    setError(null)

    const form = new FormData()
    form.append('file', file)
    form.append('unit', activeUnit)

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: form
      })

      const data = await res.json()

      if (data.success) {
        await fetchNotes(activeUnit)
        setFile(null)
      } else {
        setError(data.error || 'Upload failed')
      }
    } catch (err) {
      setError('Upload failed: ' + (err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const handleSend = async () => {
    if (!activeUnit) {
      setError('Please select a unit first')
      return
    }

    if (!message.trim()) return

    const currentChat = chatHistory[activeUnit] || []
    const updatedChat = [...currentChat, `You: ${message}`]
    setChatHistory(prev => ({ ...prev, [activeUnit]: updatedChat }))

    const userMessage = message
    setMessage('')

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, documentCategory: activeUnit }),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.error || 'Chat failed')
        setChatHistory(prev => ({ 
          ...prev, 
          [activeUnit]: prev[activeUnit].slice(0, -1) 
        }))
      } else {
        const aiResponse = data.answer || data.reply || 'No response received'
        setChatHistory(prev => ({ 
          ...prev, 
          [activeUnit]: [...(prev[activeUnit] || []), `AI: ${aiResponse}`] 
        }))
      }
    } catch (err) {
      setError('Chat failed: ' + (err as Error).message)
      setChatHistory(prev => ({ 
        ...prev, 
        [activeUnit]: prev[activeUnit].slice(0, -1) 
      }))
    }
  }

  const currentChatLog = activeUnit ? (chatHistory[activeUnit] || []) : []

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#0f0f23', 
      color: '#e6e6e6',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ 
          marginBottom: '2rem', 
          textAlign: 'center',
          borderBottom: '1px solid #2d2d44',
          paddingBottom: '1rem'
        }}>
          <h1 style={{ 
            margin: 0, 
            fontSize: '2.5rem', 
            fontWeight: 'bold',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            Notes Summarizer
          </h1>
          <p style={{ margin: '0.5rem 0 0 0', color: '#a0a0a0', fontSize: '1.1rem' }}>
            Smart PDF processing with AI-powered insights
          </p>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '1rem'
          }}>
            <h2 style={{ margin: 0, color: '#e6e6e6' }}>Your Tabs</h2>
            <button
              onClick={() => setShowNewTabForm(!showNewTabForm)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#667eea',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: '500',
                transition: 'background-color 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#5a6fd8'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#667eea'}
            >
              {showNewTabForm ? 'Cancel' : '+ New Tab'}
            </button>
          </div>

          {showNewTabForm && (
            <div style={{ 
              padding: '1rem', 
              backgroundColor: '#1a1a2e', 
              borderRadius: '8px',
              marginBottom: '1rem',
              border: '1px solid #2d2d44'
            }}>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                <input
                  type="text"
                  placeholder="Tab name"
                  value={newTabName}
                  onChange={(e) => setNewTabName(e.target.value)}
                  style={{
                    flex: 1,
                    padding: '0.5rem',
                    backgroundColor: '#2d2d44',
                    border: '1px solid #3d3d54',
                    borderRadius: '4px',
                    color: '#e6e6e6',
                    fontSize: '0.9rem'
                  }}
                />
                <input
                  type="color"
                  value={newTabColor}
                  onChange={(e) => setNewTabColor(e.target.value)}
                  style={{
                    width: '40px',
                    height: '40px',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                />
                <button
                  onClick={createTab}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    fontWeight: '500'
                  }}
                >
                  Create
                </button>
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {tabs.map(tab => (
              <div key={tab.id} style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem', 
                backgroundColor: activeTab === tab.id ? tab.color : '#1a1a2e',
                color: activeTab === tab.id ? 'white' : '#e6e6e6',
                border: `1px solid ${activeTab === tab.id ? tab.color : '#2d2d44'}`,
                borderRadius: '8px',
                padding: '0.75rem 1.5rem',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: '500',
                transition: 'all 0.2s',
                minWidth: '100px',
                textAlign: 'center',
                position: 'relative'
              }}
              onMouseOver={(e) => {
                if (activeTab !== tab.id) {
                  e.currentTarget.style.backgroundColor = '#2d2d44'
                }
              }}
              onMouseOut={(e) => {
                if (activeTab !== tab.id) {
                  e.currentTarget.style.backgroundColor = '#1a1a2e'
                }
              }}
            >
              <span 
                onClick={() => setActiveTab(tab.id)}
                style={{ cursor: 'pointer', flex: 1 }}
              >
                {tab.name}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  deleteTab(tab.id)
                }}
                style={{
                  padding: '0.25rem 0.5rem',
                  backgroundColor: '#dc3545',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.75rem',
                  fontWeight: 'bold',
                  opacity: '0.7',
                  transition: 'opacity 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#c82333'
                  e.currentTarget.style.opacity = '1'
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = '#dc3545'
                  e.currentTarget.style.opacity = '0.7'
                }}
                title="Delete tab"
              >
                ×
              </button>
            </div>
            ))}
          </div>
        </div>

        {activeTab && (
          <>
            <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem' }}>
              <div style={{ 
                width: '250px', 
                flexShrink: 0,
                backgroundColor: '#1a1a2e',
                borderRadius: '12px',
                border: '1px solid #2d2d44',
                padding: '1.5rem',
                height: 'fit-content'
              }}>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  marginBottom: '1rem'
                }}>
                  <h3 style={{ margin: 0, color: '#e6e6e6', fontSize: '1.1rem' }}>
                    Units in "{tabs.find(t => t.id === activeTab)?.name}"
                  </h3>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      onClick={() => activeTab && fetchUnits(activeTab)}
                      style={{
                        padding: '0.25rem 0.5rem',
                        backgroundColor: '#6c757d',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.75rem',
                        fontWeight: '500',
                        transition: 'background-color 0.2s'
                      }}
                      onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#5a6268'}
                      onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#6c757d'}
                      title="Refresh units"
                    >
                      ↻
                    </button>
                    <button
                      onClick={() => setShowNewUnitForm(!showNewUnitForm)}
                      style={{
                        padding: '0.25rem 0.5rem',
                        backgroundColor: '#667eea',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.75rem',
                        fontWeight: '500',
                        transition: 'background-color 0.2s'
                      }}
                      onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#5a6fd8'}
                      onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#667eea'}
                    >
                      {showNewUnitForm ? '×' : '+'}
                    </button>
                  </div>
                </div>

                {showNewUnitForm && (
                  <div style={{ 
                    padding: '1rem', 
                    backgroundColor: '#2d2d44', 
                    borderRadius: '8px',
                    marginBottom: '1rem',
                    border: '1px solid #3d3d54'
                  }}>
                    <input
                      type="text"
                      placeholder="Unit name"
                      value={newUnitName}
                      onChange={(e) => setNewUnitName(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        backgroundColor: '#1a1a2e',
                        border: '1px solid #3d3d54',
                        borderRadius: '4px',
                        color: '#e6e6e6',
                        fontSize: '0.85rem',
                        marginBottom: '0.5rem'
                      }}
                    />
                    <input
                      type="text"
                      placeholder="Description (optional)"
                      value={newUnitDescription}
                      onChange={(e) => setNewUnitDescription(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        backgroundColor: '#1a1a2e',
                        border: '1px solid #3d3d54',
                        borderRadius: '4px',
                        color: '#e6e6e6',
                        fontSize: '0.85rem',
                        marginBottom: '0.5rem'
                      }}
                    />
                    <button
                      onClick={createUnit}
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        backgroundColor: '#28a745',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.85rem',
                        fontWeight: '500'
                      }}
                    >
                      Create Unit
                    </button>
                  </div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {units.map(unit => (
                    <div key={unit.id} style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '0.5rem', 
                      backgroundColor: activeUnit === unit.id ? '#667eea' : '#2d2d44',
                      color: activeUnit === unit.id ? 'white' : '#e6e6e6',
                      border: `1px solid ${activeUnit === unit.id ? '#667eea' : '#3d3d54'}`,
                      borderRadius: '8px',
                      padding: '0.75rem 1rem',
                      cursor: 'pointer',
                      fontSize: '0.9rem',
                      fontWeight: '500',
                      transition: 'all 0.2s',
                      position: 'relative'
                    }}
                    onMouseOver={(e) => {
                      if (activeUnit !== unit.id) {
                        e.currentTarget.style.backgroundColor = '#3d3d54'
                      }
                    }}
                    onMouseOut={(e) => {
                      if (activeUnit !== unit.id) {
                        e.currentTarget.style.backgroundColor = '#2d2d44'
                      }
                    }}
                  >
                    <span 
                      onClick={() => setActiveUnit(unit.id)}
                      style={{ cursor: 'pointer', flex: 1, fontSize: '0.85rem' }}
                    >
                      {unit.name}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteUnit(unit.id)
                      }}
                      style={{
                        padding: '0.25rem 0.5rem',
                        backgroundColor: '#dc3545',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.75rem',
                        fontWeight: 'bold',
                        opacity: '0.7',
                        transition: 'opacity 0.2s'
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.backgroundColor = '#c82333'
                        e.currentTarget.style.opacity = '1'
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.backgroundColor = '#dc3545'
                        e.currentTarget.style.opacity = '0.7'
                      }}
                      title="Delete unit"
                    >
                      ×
                    </button>
                  </div>
                  ))}
                </div>
              </div>

              <div style={{ flex: 1 }}>

            <div style={{ 
              marginBottom: '2rem',
              padding: '1.5rem',
              backgroundColor: '#1a1a2e',
              borderRadius: '12px',
              border: '1px solid #2d2d44'
            }}>
              <h3 style={{ margin: '0 0 1rem 0', color: '#e6e6e6' }}>
                Upload PDF to "{units.find(u => u.id === activeUnit)?.name}"
              </h3>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  style={{
                    flex: 1,
                    padding: '0.5rem',
                    backgroundColor: '#2d2d44',
                    border: '1px solid #3d3d54',
                    borderRadius: '6px',
                    color: '#e6e6e6',
                    fontSize: '0.9rem'
                  }}
                />
                <button
                  onClick={handleUpload}
                  disabled={!file || loading}
                  style={{
                    padding: '0.75rem 1.5rem',
                    backgroundColor: file && !loading ? '#667eea' : '#4a4a6a',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: file && !loading ? 'pointer' : 'not-allowed',
                    fontSize: '0.9rem',
                    fontWeight: '500',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseOver={(e) => {
                    if (file && !loading) {
                      e.currentTarget.style.backgroundColor = '#5a6fd8'
                    }
                  }}
                  onMouseOut={(e) => {
                    if (file && !loading) {
                      e.currentTarget.style.backgroundColor = '#667eea'
                    }
                  }}
                >
                  {loading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
              {error && (
                <div style={{ 
                  marginTop: '1rem', 
                  padding: '0.75rem', 
                  backgroundColor: '#2d1b1b', 
                  border: '1px solid #5a2a2a',
                  borderRadius: '6px',
                  color: '#ff6b6b'
                }}>
                  {error}
                </div>
              )}
            </div>

            {notes.length > 0 && (
              <div style={{ marginBottom: '2rem' }}>
                <h3 style={{ margin: '0 0 1rem 0', color: '#e6e6e6' }}>
                  Notes in "{units.find(u => u.id === activeUnit)?.name}"
                </h3>
                <div style={{ display: 'grid', gap: '1rem' }}>
                  {notes.map(note => (
                    <div key={note.id} style={{ 
                      padding: '1.5rem', 
                      backgroundColor: '#1a1a2e',
                      border: '1px solid #2d2d44',
                      borderRadius: '12px',
                      transition: 'transform 0.2s, box-shadow 0.2s'
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.transform = 'translateY(-2px)'
                      e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.3)'
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)'
                      e.currentTarget.style.boxShadow = 'none'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                        <h4 style={{ margin: 0, color: '#e6e6e6', fontSize: '1.1rem' }}>{note.title}</h4>
                        <span style={{
                          padding: '0.25rem 0.75rem',
                          borderRadius: '20px',
                          fontSize: '0.75rem',
                          fontWeight: 'bold',
                          backgroundColor: note.extraction_method === 'Text Layer (Fast)' ? '#1b4332' : '#4a2c1b',
                          color: note.extraction_method === 'Text Layer (Fast)' ? '#52c41a' : '#faad14',
                          border: `1px solid ${note.extraction_method === 'Text Layer (Fast)' ? '#2d5a3d' : '#6b3f2a'}`
                        }}>
                          {note.extraction_method === 'Text Layer (Fast)' ? '⚡ Fast' : '🔍 OCR'}
                        </span>
                      </div>
                      <p style={{ color: '#a0a0a0', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
                        {new Date(note.created_at).toLocaleDateString()}
                      </p>
                      {note.summary && (
                        <p style={{ marginTop: '0.75rem', color: '#c0c0c0', lineHeight: '1.5' }}>
                          <strong style={{ color: '#e6e6e6' }}>Summary:</strong> {note.summary}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div style={{ 
              marginBottom: '2rem',
              padding: '1.5rem',
              backgroundColor: '#1a1a2e',
              borderRadius: '12px',
              border: '1px solid #2d2d44'
            }}>
              <h3 style={{ margin: '0 0 1rem 0', color: '#e6e6e6' }}>
                Chat about "{units.find(u => u.id === activeUnit)?.name}"
              </h3>
              <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Ask a question about your documents..."
                  style={{
                    flex: 1,
                    padding: '0.75rem',
                    backgroundColor: '#2d2d44',
                    border: '1px solid #3d3d54',
                    borderRadius: '8px',
                    color: '#e6e6e6',
                    fontSize: '0.9rem'
                  }}
                />
                <button
                  onClick={handleSend}
                  disabled={!message.trim()}
                  style={{
                    padding: '0.75rem 1.5rem',
                    backgroundColor: message.trim() ? '#667eea' : '#4a4a6a',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: message.trim() ? 'pointer' : 'not-allowed',
                    fontSize: '0.9rem',
                    fontWeight: '500',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseOver={(e) => {
                    if (message.trim()) {
                      e.currentTarget.style.backgroundColor = '#5a6fd8'
                    }
                  }}
                  onMouseOut={(e) => {
                    if (message.trim()) {
                      e.currentTarget.style.backgroundColor = '#667eea'
                    }
                  }}
                >
                  Send
                </button>
              </div>
              <div style={{ 
                maxHeight: '400px', 
                overflowY: 'auto',
                padding: '1rem',
                backgroundColor: '#0f0f23',
                borderRadius: '8px',
                border: '1px solid #2d2d44'
              }}>
                {currentChatLog.length === 0 && (
                  <div style={{ textAlign: 'center', color: '#6c757d', marginTop: '2rem' }}>
                    Start asking questions about the documents in this unit...
                  </div>
                )}
                {currentChatLog.map((line, i) => (
                  <div key={i} style={{ 
                    marginBottom: '1rem',
                    padding: '0.75rem',
                    backgroundColor: line.startsWith('You:') ? '#1a1a2e' : '#2d2d44',
                    borderRadius: '8px',
                    border: `1px solid ${line.startsWith('You:') ? '#3d3d54' : '#4d4d64'}`
                  }}>
                    <div style={{ 
                      fontWeight: 'bold', 
                      marginBottom: '0.5rem',
                      color: line.startsWith('You:') ? '#667eea' : '#52c41a'
                    }}>
                      {line.startsWith('You:') ? 'You' : 'AI Assistant'}
                    </div>
                    <div style={{ color: '#e6e6e6', lineHeight: '1.5' }}>
                      {line.replace(/^(You|AI): /, '')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          </div>
          </>
        )}

        {!activeTab && tabs.length === 0 && (
          <div style={{ 
            textAlign: 'center', 
            padding: '4rem 2rem', 
            color: '#a0a0a0',
            backgroundColor: '#1a1a2e',
            borderRadius: '12px',
            border: '1px solid #2d2d44'
          }}>
            <h3 style={{ color: '#e6e6e6', marginBottom: '1rem' }}>Welcome to Notes Summarizer!</h3>
            <p style={{ fontSize: '1.1rem', margin: 0 }}>Create your first tab to get started organizing your notes.</p>
          </div>
        )}
      </div>
    </div>
  )
}

