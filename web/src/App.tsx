import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'

type BlurCheck = { grade: number; label: string; confidence: number; changed: boolean }
type Analysis = {
  analysis_id: string; grade: number; label: string; confidence: number;
  probabilities: number[]; review_required: boolean; review_reasons: string[];
  processed_image: string; heatmap_overlay: string; blur_check: BlurCheck; notice: string;
}
type Message = { role: 'user' | 'guide'; text: string }
const labels = ['No DR', 'Mild', 'Moderate', 'Severe', 'Proliferative DR']
const prompts = ['What does confidence mean?', 'Why is review flagged?', 'What does the heatmap show?', 'Did blur change the result?']

async function responseJSON<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || 'The request did not finish. Please retry.')
  return body as T
}

export default function App() {
  const [ready, setReady] = useState<boolean | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState('')
  const [result, setResult] = useState<Analysis | null>(null)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const chatEnd = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetch('/api/health').then(responseJSON<{ ready: boolean }>).then(x => setReady(x.ready)).catch(() => setReady(false))
  }, [])
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])
  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }) }, [messages])

  function choose(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null
    setError(''); setResult(null); setMessages([]); setFile(selected)
    setPreview(selected ? URL.createObjectURL(selected) : '')
  }

  async function analyze() {
    if (!file || working) return
    setWorking(true); setError(''); setResult(null); setMessages([])
    const form = new FormData(); form.append('file', file)
    try {
      const analysis = await responseJSON<Analysis>(await fetch('/api/analyze', { method: 'POST', body: form }))
      setResult(analysis)
      setMessages([{ role: 'guide', text: 'I can explain this displayed result, its review flag, Grad-CAM limits, and blur sensitivity. What would you like to know?' }])
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Analysis failed.') }
    finally { setWorking(false) }
  }

  async function ask(text: string) {
    const current = text.trim()
    if (!result || !current || asking) return
    setQuestion(''); setAsking(true)
    setMessages(previous => [...previous, { role: 'user', text: current }])
    try {
      const reply = await responseJSON<{ answer: string }>(await fetch('/api/ask', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analysis_id: result.analysis_id, question: current }),
      }))
      setMessages(previous => [...previous, { role: 'guide', text: reply.answer }])
    } catch (cause) {
      setMessages(previous => [...previous, { role: 'guide', text: cause instanceof Error ? cause.message : 'Could not answer.' }])
    } finally { setAsking(false) }
  }
  function submitQuestion(event: FormEvent) { event.preventDefault(); void ask(question) }

  return <div className="shell">
    <header className="topbar"><a className="brand" href="#top"><span className="brand-icon">◉</span><span>RetinaStage<small>RESEARCH WORKSPACE</small></span></a><span className="top-right"><span className="status-dot" /> COURSEWORK PROTOTYPE <span className="top-divider" /> FIVE GRADE MODEL</span></header>
    <main id="top">
      <section className="hero"><div><p className="eyebrow">FUNDUS IMAGE ANALYSIS <span> / </span> APTOS 2019</p><h1>Understand the prediction.<br /><em>Question its certainty.</em></h1><p className="lead">A research interface for a five grade retinal image model trained in the final Colab notebook. Explore the estimated stage, review signals, attention map and response to mild blur in one place.</p><div className="hero-meta"><span><b>01</b> Analyze an image</span><span><b>02</b> Inspect the evidence</span><span><b>03</b> Ask RetinaGuide</span></div></div><div className="hero-art" aria-hidden="true"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="orbit orbit-three" /><div className="iris"><div className="iris-inner" /></div><div className="hero-art-tag">FROM IMAGE TO INSIGHT <span>↗</span></div></div></section>
      {ready === false && <div className="setup-note" role="status"><b>Model setup required.</b> Add the saved Colab checkpoint and its calibration JSON to <code>models/</code>, then start the API. The interface does not simulate an analysis.</div>}
      <div className="workspace-grid"><section className="panel input-panel"><div className="panel-heading"><div><p className="eyebrow">STEP 01 / INPUT</p><h2>Choose a retinal image</h2></div><span className="panel-symbol">↗</span></div>
        <label className={`dropzone ${preview ? 'has-image' : ''}`}><input type="file" accept="image/jpeg,image/png" onChange={choose} />{preview ? <img src={preview} alt="Selected retinal photograph" /> : <div className="drop-prompt"><span className="upload-icon">↑</span><strong>Select a fundus photograph</strong><span>PNG or JPEG · up to 10 MB</span></div>}<span className="replace-label">{preview ? 'REPLACE IMAGE ↗' : 'BROWSE FILES ↗'}</span></label>
        {file && <div className="file-row"><span>SELECTED FILE</span><b>{file.name}</b><span>{(file.size / (1024 * 1024)).toFixed(2)} MB</span></div>}
        <button className="primary-button" onClick={() => void analyze()} disabled={!file || working || ready === false}>{working ? 'Analyzing image…' : 'Run analysis'} <span>↗</span></button>
        {error && <p className="error" role="alert">{error}</p>}
        <div className="input-foot"><span>◈</span> Image content is processed in memory for this request. Research use only.</div>
      </section>
      <section className="panel results-panel"><div className="panel-heading"><div><p className="eyebrow">STEP 02 / OUTPUT</p><h2>Model assessment</h2></div><span className="result-status">{result ? 'ANALYSIS READY' : 'AWAITING IMAGE'}</span></div>
        {!result ? <div className="empty-results"><div className="empty-rings"><span>◉</span></div><h3>Evidence appears here</h3><p>Upload an image to see calibrated grade estimates and exploratory checks from the saved notebook model.</p></div> : <>
          <div className="prediction"><div><span className="prediction-kicker">SELECTED OUTPUT · GRADE {result.grade}</span><h3>{result.label}</h3><span>Highest calibrated model estimate</span></div><div className="confidence"><b>{Math.round(result.confidence * 100)}%</b><small>CONFIDENCE</small></div></div>
          <div className={`review ${result.review_required ? 'review-flag' : ''}`}><span className="review-icon">{result.review_required ? '!' : '✓'}</span><div><b>{result.review_required ? 'Illustrative review flag' : 'No illustrative rule triggered'}</b><p>{result.review_required ? result.review_reasons.join('; ') : 'This does not establish that the result is correct or clinically safe.'}</p></div></div>
          <div className="subheading"><h3>Five grade estimates</h3><span>TEMPERATURE SCALED</span></div><div className="prob-list">{result.probabilities.map((value, index) => <div className="prob" key={index}><div className="prob-label"><span><i className={index === result.grade ? 'selected-grade' : ''}>{index}</i>{labels[index]}</span><strong>{(value * 100).toFixed(1)}%</strong></div><div className="track"><div className={index === result.grade ? 'fill selected-fill' : 'fill'} style={{ width: `${value * 100}%` }} /></div></div>)}</div>
        </>}
      </section></div>
      {result && <><section className="evidence-section"><div className="section-title"><div><p className="eyebrow">EXPLORE / MODEL BEHAVIOUR</p><h2>Evidence, with boundaries.</h2></div><p>These checks help inspect a model output. They do not establish a clinical diagnosis.</p></div><div className="evidence-grid"><article className="evidence-card"><div className="card-image"><img src={result.processed_image} alt="P2 processed model input" /></div><div className="card-copy"><span>01 / MODEL INPUT</span><h3>Processed retinal image</h3><p>Cropped, resized and contrast enhanced with the notebook’s P2 pipeline.</p></div></article><article className="evidence-card"><div className="card-image"><img src={result.heatmap_overlay} alt="Grad-CAM attention overlay for the selected grade" /></div><div className="card-copy"><span>02 / RETINAFOCUS</span><h3>Grad-CAM overlay</h3><p>Coarse regions associated with Grade {result.grade}. This cannot localize lesions or prove causality.</p></div></article><article className="evidence-card shift-card"><div className="shift-graphic"><span>ORIGINAL</span><b>G{result.grade}</b><i>→</i><span>MILD BLUR</span><b>G{result.blur_check.grade}</b></div><div className="card-copy"><span>03 / RETINASHIFT</span><h3>{result.blur_check.changed ? 'Grade changed under blur' : 'Grade stayed the same'}</h3><p>A single fixed blur check; the wider notebook stress test evaluates validation images. Stability here is not clinical robustness.</p></div></article></div></section>
        <section className="chat-section"><div className="chat-intro"><p className="eyebrow">STEP 03 / RETINAGUIDE</p><h2>Ask about this result.</h2><p>Answers use this displayed analysis and fixed explanations. RetinaGuide cannot diagnose disease or advise treatment.</p><div className="prompt-list">{prompts.map(prompt => <button key={prompt} onClick={() => void ask(prompt)} disabled={asking}>{prompt} <span>↗</span></button>)}</div></div><div className="chat-box"><div className="chat-header"><span className="chat-avatar">✳</span><div><b>RetinaGuide</b><small>GROUNDED EXPLANATIONS</small></div><span className="chat-live">● AVAILABLE</span></div><div className="messages">{messages.map((message, index) => <div className={`message ${message.role}`} key={index}>{message.text}</div>)}<div ref={chatEnd} /></div><form className="chat-form" onSubmit={submitQuestion}><input aria-label="Ask RetinaGuide" maxLength={500} placeholder="Ask about this analysis…" value={question} onChange={event => setQuestion(event.target.value)} /><button type="submit" disabled={!question.trim() || asking} aria-label="Send question">↗</button></form></div></section>
      </>}
      <footer><div className="brand footer-brand"><span className="brand-icon">◉</span><span>RetinaStage<small>RESEARCH WORKSPACE</small></span></div><p>Educational prototype · APTOS 2019 · Qualified human interpretation required.</p><span>NOT FOR CLINICAL USE</span></footer>
    </main>
  </div>
}
