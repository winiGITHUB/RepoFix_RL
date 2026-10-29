import { useEffect, useState } from 'react'
import { Activity, ArrowDown, ArrowRight, Check, CheckCircle2, ChevronDown, CircleDot, Clock3, Code2, FileCode2, FlaskConical, GitBranch, LoaderCircle, Play, Sparkles, Terminal, Wrench, XCircle } from 'lucide-react'

type Event = { step: number; kind: string; title: string; detail: string; status: string }
type Run = { run_id: string; language: string; compile_status: string; run_status: string; stdout: string; stderr: string; duration_ms: number; sample_results: {case:number; passed:boolean; input:string; expected:string; actual:string; stderr:string; exit_code:number}[]; diagnosis: { verdict: string; bug_category: string; location: string; counterexample: string; root_cause: string; hints: string[]; solution_review: string; suggested_patch: string }; trace: Event[] }

const eventIcon = (kind: string) => kind === 'tool' ? <Wrench size={15} /> : kind === 'evaluation' ? <FlaskConical size={15} /> : kind === 'reasoning' ? <Sparkles size={15} /> : <CircleDot size={15} />

export default function App() {
  const [language, setLanguage] = useState<'python' | 'cpp'>('python')
  const [problem, setProblem] = useState('')
  const [sourceCode, setSourceCode] = useState('')
  const [sampleCases, setSampleCases] = useState('[\n  {"input": "", "expected_output": ""}\n]')
  const [run, setRun] = useState<Run | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [provider, setProvider] = useState('checking…')

  useEffect(() => {
    fetch('/api/health').then(r => r.json()).then((health: { provider: string }) => setProvider(health.provider)).catch(() => setProvider('offline'))
  }, [])

  async function startRun() {
    if (!problem.trim() || !sourceCode.trim() || busy) return
    setBusy(true); setRun(null); setError('')
    try {
      const samples = JSON.parse(sampleCases)
      const response = await fetch('/api/submissions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ problem, language, source_code: sourceCode, samples }) })
      if (!response.ok) throw new Error((await response.json()).detail ?? '任务执行失败')
      setRun(await response.json())
    } catch (e) { setError(e instanceof Error ? e.message : '请求失败') }
    finally { setBusy(false) }
  }

  return <div className="app-shell">
    <header className="topbar">
      <div className="brand"><div className="brand-mark"><Code2 size={19} /></div><span>repofix<span className="brand-accent">.rl</span></span><span className="brand-tag">AGENT LAB</span></div>
      <div className="top-center"><span className="live-dot" /> Local workspace <span className="top-divider">/</span> <GitBranch size={13} /> main</div>
      <div className="top-right"><span className="model-pill"><span className="model-dot" /> {provider}</span><div className="avatar">W</div></div>
    </header>

    <main className="layout">
      <aside className="sidebar">
        <div className="side-label">WORKSPACE</div>
        <button className="nav-item active"><Activity size={16} /> Repair tasks <span className="nav-count">01</span></button>
        <button className="nav-item muted"><FlaskConical size={16} /> Experiments <span className="soon">SOON</span></button>
        <div className="side-divider" />
        <div className="side-label">LANGUAGES</div>
        <div className="benchmark-card"><div className="bench-icon"><FileCode2 size={16} /></div><div><strong>Python + C++</strong><span>Local code runner</span></div><ChevronDown size={14} className="bench-chevron" /></div>
        <div className="side-bottom"><div className="connection"><span className="live-dot" /> API connected</div><span>v0.1.0 · Local prototype</span></div>
      </aside>

      <section className="content">
        <div className="page-heading"><div><div className="eyebrow">ALGORITHM CODE REVIEW</div><h1>Understand your bug<span className="heading-period">.</span></h1><p>Run your code, find the issue, and review the problem-solving approach.</p></div><div className="heading-chip"><Sparkles size={14} /> Tutor session</div></div>
        <div className="work-grid">
          <div className="main-column">
            <section className="panel task-panel">
              <div className="panel-top"><div className="section-kicker"><span className="step-number">01</span> YOUR SUBMISSION</div><span className="task-count">LOCAL ONLY</span></div>
              <div className="submission-form"><label className="input-label">Programming language<select value={language} onChange={e => setLanguage(e.target.value as 'python' | 'cpp')}><option value="python">Python 3</option><option value="cpp">C++17</option></select></label><label className="input-label">Problem description<textarea className="problem-input" value={problem} onChange={e => setProblem(e.target.value)} placeholder="Paste the problem statement or describe the task…" rows={4}/></label><label className="input-label">Your code<textarea className="code-input" value={sourceCode} onChange={e => setSourceCode(e.target.value)} placeholder={language === 'python' ? 'Paste your Python solution…' : 'Paste your C++17 solution…'} rows={11} spellCheck={false}/></label><label className="input-label">Examples (JSON array with input and expected_output)<textarea className="sample-input" value={sampleCases} onChange={e => setSampleCases(e.target.value)} rows={5} spellCheck={false}/></label></div>
              <div className="run-row"><div className="run-caption"><span className="caption-dot" /> Runs locally <span className="run-caption-sep">·</span> 3s timeout</div><button className="run-button" onClick={startRun} disabled={busy || !problem.trim() || !sourceCode.trim()}>{busy ? <LoaderCircle className="spin" size={16} /> : <Play size={15} fill="currentColor" />} {busy ? 'Analyzing' : 'Run & review'} <ArrowRight size={15} /></button></div>
            </section>

            <section className="panel trace-panel">
              <div className="panel-top"><div className="section-kicker"><span className="step-number">02</span> EXECUTION TRACE</div>{run ? <span className="run-id">RUN {run.run_id.slice(0, 8).toUpperCase()}</span> : <span className="waiting-label">{busy ? 'IN PROGRESS' : 'AWAITING RUN'}</span>}</div>
              {!run && !busy ? <div className="trace-empty"><div className="empty-orbit"><Activity size={21} /></div><strong>Your agent trace will appear here</strong><span>Choose a task and run the agent to inspect each action.</span></div> : <div className="timeline">{(run?.trace ?? []).map((event, index) => <div className="trace-event" key={event.step}><div className="event-rail"><div className={`event-icon ${event.kind}`}>{eventIcon(event.kind)}</div>{index < (run?.trace.length ?? 0) - 1 && <div className="rail-line" />}</div><div className="event-body"><div className="event-title-row"><strong>{event.title}</strong><span className="event-status"><Check size={12} /> {event.status === 'passed' ? 'PASSED' : 'DONE'}</span></div><pre>{event.detail}</pre></div></div>)}{busy && <div className="running-row"><LoaderCircle className="spin" size={15} /> Agent is working…</div>}</div>}
            </section>
          </div>

          <div className="right-column">
            <section className="panel result-panel"><div className="section-kicker"><span className="step-number">03</span> DIAGNOSIS</div>{!run ? <div className="result-placeholder"><div className="result-icon"><CheckCircle2 size={21} /></div><strong>Waiting for your submission</strong><span>Execution output and diagnosis will appear here.</span></div> : <><div className={`result-banner ${run.run_status === 'completed' ? 'passed' : 'failed'}`}><div className="result-check">{run.compile_status === 'failed' ? <XCircle size={18} /> : <CheckCircle2 size={18} />}</div><div><strong>{run.compile_status === 'failed' ? 'Compilation failed' : `Run: ${run.run_status}`}</strong><span>{run.diagnosis.verdict}</span></div></div><div className="diagnosis-body"><div><small>BUG TYPE · {run.diagnosis.bug_category}</small><h3>{run.diagnosis.root_cause}</h3><p><b>位置：</b>{run.diagnosis.location}</p><p><b>反例：</b>{run.diagnosis.counterexample}</p><p><b>复盘：</b>{run.diagnosis.solution_review}</p>{run.diagnosis.hints?.length > 0 && <><b>提示</b><ol>{run.diagnosis.hints.map((hint, i) => <li key={i}>{hint}</li>)}</ol></>}</div></div><div className="result-foot"><span><span className="pass-dot" /> {run.language.toUpperCase()} · {run.duration_ms}ms</span><span>{run.run_status}</span></div></>}</section>

            <section className="panel diff-panel"><div className="diff-head"><div className="section-kicker"><span className="step-number">04</span> PROGRAM OUTPUT</div>{run && <span className="file-label"><Terminal size={13} /> stdout / stderr</span>}</div>{run ? <pre className="diff-code">{run.stdout || run.stderr || 'No output'}</pre> : <div className="diff-placeholder"><div><Terminal size={18} /></div><span>Execution output</span><small>Program output will appear here.</small></div>}</section>
            <div className="insight-card"><div className="insight-icon"><Sparkles size={15} /></div><p><strong>Why this matters</strong><br />Each run creates a verifiable trajectory that can later become training data for GRPO.</p><ArrowDown size={14} /></div>
          </div>
        </div>
        {error && <div className="error-toast"><XCircle size={16} /> {error}</div>}
        <footer className="page-footer"><span>CODEREVIEW TUTOR <b>·</b> LOCAL CODE DIAGNOSIS</span><span>USER CODE RUNS LOCALLY <b>·</b> DO NOT EXPOSE PUBLICLY</span></footer>
      </section>
    </main>
  </div>
}
