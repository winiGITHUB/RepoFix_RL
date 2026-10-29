import { useEffect, useState } from 'react'
import { Activity, ArrowDown, ArrowRight, Check, CheckCircle2, ChevronDown, CircleDot, Clock3, Code2, FileCode2, FlaskConical, GitBranch, LoaderCircle, Play, Sparkles, Terminal, Wrench, XCircle } from 'lucide-react'

type Task = { id: string; title: string; description: string; difficulty: string; language: string }
type Event = { step: number; kind: string; title: string; detail: string; status: string }
type Run = { run_id: string; task: Task; status: string; score: number; tests_passed: number; tests_total: number; duration_ms: number; summary: string; diff: string; trace: Event[] }

const eventIcon = (kind: string) => kind === 'tool' ? <Wrench size={15} /> : kind === 'evaluation' ? <FlaskConical size={15} /> : kind === 'reasoning' ? <Sparkles size={15} /> : <CircleDot size={15} />

export default function App() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [selected, setSelected] = useState('')
  const [run, setRun] = useState<Run | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [provider, setProvider] = useState('checking…')

  useEffect(() => {
    fetch('/api/tasks').then(r => r.json()).then((items: Task[]) => { setTasks(items); if (items[0]) setSelected(items[0].id) }).catch(() => setError('无法连接后端，请先启动 FastAPI 服务。'))
    fetch('/api/health').then(r => r.json()).then((health: { provider: string }) => setProvider(health.provider)).catch(() => setProvider('offline'))
  }, [])

  const task = tasks.find(item => item.id === selected)
  async function startRun() {
    if (!selected || busy) return
    setBusy(true); setRun(null); setError('')
    try {
      const response = await fetch('/api/runs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ task_id: selected }) })
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
        <div className="side-label">BENCHMARK</div>
        <div className="benchmark-card"><div className="bench-icon"><FileCode2 size={16} /></div><div><strong>Python fixes</strong><span>Built-in demo set</span></div><ChevronDown size={14} className="bench-chevron" /></div>
        <div className="side-bottom"><div className="connection"><span className="live-dot" /> API connected</div><span>v0.1.0 · Local prototype</span></div>
      </aside>

      <section className="content">
        <div className="page-heading"><div><div className="eyebrow">CODE REPAIR WORKSPACE</div><h1>Repair a task<span className="heading-period">.</span></h1><p>Watch the agent investigate, patch, and verify a real Python bug.</p></div><div className="heading-chip"><Sparkles size={14} /> Agent run</div></div>
        <div className="work-grid">
          <div className="main-column">
            <section className="panel task-panel">
              <div className="panel-top"><div className="section-kicker"><span className="step-number">01</span> SELECT TASK</div><span className="task-count">{tasks.length.toString().padStart(2, '0')} available</span></div>
              {task ? <><div className="task-card"><div className="task-card-head"><span className="task-icon"><Code2 size={17} /></span><span className="difficulty">{task.difficulty}</span><label className="task-picker-label"><span className="sr-only">选择修复任务</span><select className="task-picker" value={selected} onChange={event => { setSelected(event.target.value); setRun(null) }}>{tasks.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}</select><ChevronDown size={14} className="task-chevron" /></label></div><h2>{task.title}</h2><p>{task.description}</p><div className="task-meta"><span><FileCode2 size={13} /> {task.language}</span><span className="meta-separator" /><span><GitBranch size={13} /> {task.id}</span></div></div>
              <div className="run-row"><div className="run-caption"><span className="caption-dot" /> Isolated workspace <span className="run-caption-sep">·</span> Hidden tests enabled</div><button className="run-button" onClick={startRun} disabled={busy}>{busy ? <LoaderCircle className="spin" size={16} /> : <Play size={15} fill="currentColor" />} {busy ? 'Running agent' : 'Run agent'} <ArrowRight size={15} /></button></div></> : <div className="empty-state">Loading tasks…</div>}
            </section>

            <section className="panel trace-panel">
              <div className="panel-top"><div className="section-kicker"><span className="step-number">02</span> EXECUTION TRACE</div>{run ? <span className="run-id">RUN {run.run_id.slice(0, 8).toUpperCase()}</span> : <span className="waiting-label">{busy ? 'IN PROGRESS' : 'AWAITING RUN'}</span>}</div>
              {!run && !busy ? <div className="trace-empty"><div className="empty-orbit"><Activity size={21} /></div><strong>Your agent trace will appear here</strong><span>Choose a task and run the agent to inspect each action.</span></div> : <div className="timeline">{(run?.trace ?? []).map((event, index) => <div className="trace-event" key={event.step}><div className="event-rail"><div className={`event-icon ${event.kind}`}>{eventIcon(event.kind)}</div>{index < (run?.trace.length ?? 0) - 1 && <div className="rail-line" />}</div><div className="event-body"><div className="event-title-row"><strong>{event.title}</strong><span className="event-status"><Check size={12} /> {event.status === 'passed' ? 'PASSED' : 'DONE'}</span></div><pre>{event.detail}</pre></div></div>)}{busy && <div className="running-row"><LoaderCircle className="spin" size={15} /> Agent is working…</div>}</div>}
            </section>
          </div>

          <div className="right-column">
            <section className="panel result-panel"><div className="section-kicker"><span className="step-number">03</span> RESULT</div>{!run ? <div className="result-placeholder"><div className="result-icon"><CheckCircle2 size={21} /></div><strong>Waiting for results</strong><span>Test score and patch summary appear after the run.</span></div> : <><div className={`result-banner ${run.status}`}><div className="result-check">{run.status === 'passed' ? <CheckCircle2 size={18} /> : <XCircle size={18} />}</div><div><strong>{run.status === 'passed' ? 'All checks passed' : 'Needs another pass'}</strong><span>{run.summary}</span></div></div><div className="metric-grid"><div className="metric"><span>TESTS</span><strong>{run.tests_passed}<i>/{run.tests_total}</i></strong></div><div className="metric"><span>SCORE</span><strong>{Math.round(run.score * 100)}<i>%</i></strong></div><div className="metric"><span>TIME</span><strong>{(run.duration_ms / 1000).toFixed(1)}<i>s</i></strong></div></div><div className="result-foot"><span><span className="pass-dot" /> Evaluation complete</span><span>Reward {run.score.toFixed(2)}</span></div></>}</section>

            <section className="panel diff-panel"><div className="diff-head"><div className="section-kicker"><span className="step-number">04</span> PATCH DIFF</div>{run && <span className="file-label"><FileCode2 size={13} /> solution.py</span>}</div>{run ? <pre className="diff-code">{run.diff.split('\n').map((line, i) => <span className={line.startsWith('+') && !line.startsWith('+++') ? 'added' : line.startsWith('-') && !line.startsWith('---') ? 'removed' : 'context'} key={i}>{line || ' '}<br /></span>)}</pre> : <div className="diff-placeholder"><div><FileCode2 size={18} /></div><span>Patch preview</span><small>The agent's code changes will show here.</small></div>}</section>
            <div className="insight-card"><div className="insight-icon"><Sparkles size={15} /></div><p><strong>Why this matters</strong><br />Each run creates a verifiable trajectory that can later become training data for GRPO.</p><ArrowDown size={14} /></div>
          </div>
        </div>
        {error && <div className="error-toast"><XCircle size={16} /> {error}</div>}
        <footer className="page-footer"><span>REPOFIX-RL <b>·</b> AGENT POST-TRAINING PLAYGROUND</span><span>DETERMINISTIC DEMO PROVIDER <b>·</b> NOT A TRAINED MODEL</span></footer>
      </section>
    </main>
  </div>
}
