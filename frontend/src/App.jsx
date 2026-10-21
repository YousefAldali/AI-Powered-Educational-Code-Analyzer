import { useState, useRef, useEffect } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import CodeEditor from './components/CodeEditor/CodeEditor'
import TutorPanel from './components/TutorPanel/TutorPanel'
import Dashboard from './components/Dashboard/Dashboard'
import { useReview } from './hooks/useReview'
import styles from './App.module.css'

const PLACEHOLDER = `# Paste your Python, Java, or C# code here
# The AI Tutor will explain any bugs it finds

def calculate_average(numbers):
    total = 0
    for n in numbers:
        total =+ n   # Bug: =+ should be +=
    return total / len(numbers)
`

// ── Confidence Gauge ──────────────────────────
function ConfidenceGauge({ confidence, label }) {
    const pct = Math.round((confidence ?? 0) * 100)
    const radius = 38
    const circ = 2 * Math.PI * radius
    const offset = circ - (pct / 100) * circ
    const color = pct >= 80 ? 'var(--green)' : pct >= 50 ? 'var(--amber)' : 'var(--red)'
    return (
        <div className={styles.gauge}>
            <svg width="92" height="92" viewBox="0 0 92 92">
                <circle cx="46" cy="46" r={radius} fill="none" stroke="var(--border)" strokeWidth="5" />
                <circle
                    cx="46" cy="46" r={radius}
                    fill="none" stroke={color} strokeWidth="5"
                    strokeLinecap="round"
                    strokeDasharray={circ}
                    strokeDashoffset={offset}
                    transform="rotate(-90 46 46)"
                    style={{ transition: 'stroke-dashoffset 1s ease' }}
                />
            </svg>
            <div className={styles.gaugeValue} style={{ color }}>{pct}%</div>
            <div className={styles.gaugeLabel}>{label || 'Confidence'}</div>
        </div>
    )
}

// ── Review History ──────────────────────────
function HistoryPanel({ history, onSelect }) {
    if (!history.length) return null
    return (
        <div className={styles.historyPanel}>
            <div className={styles.historyTitle}>
                <span className={styles.historyIcon}>⏱</span>
                Recent Reviews
                <span className={styles.historyCount}>{history.length}</span>
            </div>
            <div className={styles.historyList}>
                {history.map((item, i) => {
                    const isBuggy = item.result?.prediction?.label?.toLowerCase() === 'buggy'
                    return (
                        <button
                            key={i}
                            className={styles.historyItem}
                            onClick={() => onSelect(item)}
                        >
                            <span className={`${styles.historyDot} ${isBuggy ? styles.historyDotBuggy : styles.historyDotClean}`} />
                            <div className={styles.historyMeta}>
                                <span className={styles.historyLang}>{item.language.toUpperCase()}</span>
                                <span className={styles.historyTime}>{item.time}</span>
                            </div>
                            <span className={styles.historyPreview}>
                                {item.code.split('\n').filter(l => l.trim() && !l.trim().startsWith('#'))[0]?.substring(0, 40) || 'Code review'}
                            </span>
                        </button>
                    )
                })}
            </div>
        </div>
    )
}

// ── Stats Bar for Code Review ──────────────────
function ReviewStats({ result }) {
    if (!result) return null
    const pred = result.prediction
    const issues = result.static_analysis?.issues?.length ?? 0
    const isBuggy = pred?.label?.toLowerCase() === 'buggy'

    return (
        <div className={styles.reviewStats}>
            <ConfidenceGauge
                confidence={pred?.confidence}
                label="CodeBERT"
            />
            <div className={styles.statsCards}>
                <div className={styles.miniStat}>
                    <div className={styles.miniStatValue} style={{ color: isBuggy ? 'var(--red)' : 'var(--green)' }}>
                        {pred?.label || '—'}
                    </div>
                    <div className={styles.miniStatLabel}>Verdict</div>
                </div>
                <div className={styles.miniStat}>
                    <div className={styles.miniStatValue} style={{ color: issues > 0 ? 'var(--amber)' : 'var(--green)' }}>
                        {issues}
                    </div>
                    <div className={styles.miniStatLabel}>Static Issues</div>
                </div>
                <div className={styles.miniStat}>
                    <div className={styles.miniStatValue}>
                        {pred?.codebert_label || '—'}
                    </div>
                    <div className={styles.miniStatLabel}>CodeBERT</div>
                </div>
            </div>
        </div>
    )
}


// Extract error line numbers from API result
function getErrorLines(result) {
    if (!result) return []
    const lines = new Set()
    // From static analysis issues: "[Security - HIGH] Line 5: ..."
    for (const issue of result.static_analysis?.issues ?? []) {
        const m = issue.match(/Line\s+(\d+)/i)
        if (m) lines.add(parseInt(m[1]))
    }
    // From code patterns: { line: 5, ... }
    for (const p of result.code_patterns ?? []) {
        if (p.line) lines.add(p.line)
    }
    // From flagged functions: { start_line: 5, ... }
    for (const f of result.flagged_functions ?? []) {
        if (f.start_line) lines.add(f.start_line)
    }
    return [...lines].sort((a, b) => a - b)
}

function ReviewPage() {
    const [code, setCode] = useState(PLACEHOLDER)
    const [language, setLanguage] = useState('python')
    // true once the user (or an upload/history item) has set the language explicitly
    const [languageLocked, setLanguageLocked] = useState(false)
    const [fileName, setFileName] = useState(null)
    const [history, setHistory] = useState([])
    const fileInputRef = useRef(null)

    const { result, isLoading, error, submit } = useReview()
    const errorLines = getErrorLines(result)

    async function handleSubmit() {
        if (!code.trim()) return
        await submit({ code, language })
    }

    // Save to history when we get a result
    useEffect(() => {
        if (result) {
            const entry = {
                code,
                language,
                result,
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            }
            setHistory(prev => [entry, ...prev].slice(0, 10))
        }
    }, [result]) // eslint-disable-line

    function handleHistorySelect(item) {
        setCode(item.code)
        setLanguage(item.language)
        setLanguageLocked(true)
    }

    function handleFileChange(e) {
        const file = e.target.files?.[0]
        if (!file) return
        setFileName(file.name)
        const lang = file.name.endsWith('.java') ? 'java' : file.name.endsWith('.cs') ? 'csharp' : 'python'
        setLanguage(lang)
        setLanguageLocked(true)
        const reader = new FileReader()
        reader.onload = (ev) => setCode(ev.target.result ?? '')
        reader.readAsText(file)
        e.target.value = ''
    }

    return (
        <main className={styles.main}>
            {/* Left: Editor */}
            <section className={styles.editorSection}>
                <div className={styles.sectionLabel}>
                    <span className={styles.labelDot} />
                    Your Code
                    {fileName && <span className={styles.fileName} title={fileName}>{fileName}</span>}
                </div>

                <CodeEditor
                    value={code}
                    onChange={(c) => {
                        setCode(c)
                        if (!c.trim()) setLanguageLocked(false)
                    }}
                    language={language}
                    onLanguageChange={setLanguage}
                    autoDetect={!languageLocked}
                    errorLines={errorLines}
                />

                <div className={styles.actions}>
                    <button
                        className={styles.submitBtn}
                        onClick={handleSubmit}
                        disabled={isLoading || !code.trim()}
                    >
                        {isLoading ? (
                            <>
                                <span className={styles.btnSpinner} />
                                Analyzing…
                            </>
                        ) : (
                            <>
                                <span className={styles.btnIcon}>▶</span>
                                Submit for Review
                            </>
                        )}
                    </button>

                    <button
                        className={styles.uploadBtn}
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isLoading}
                        title="Upload a .py, .java, or .cs file"
                    >
                        ↑ Upload File
                    </button>

                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".py,.java,.cs"
                        className={styles.hiddenInput}
                        onChange={handleFileChange}
                    />

                    {/* Language toggle */}
                    <div className={styles.langToggle} role="group" aria-label="Language">
                        {['python', 'java', 'csharp'].map((lang) => (
                            <button
                                key={lang}
                                className={`${styles.langBtn} ${language === lang ? styles.langBtnActive : ''}`}
                                onClick={() => { setLanguage(lang); setLanguageLocked(true) }}
                                disabled={isLoading}
                                aria-pressed={language === lang}
                            >
                                {lang === 'csharp' ? 'C#' : lang.toUpperCase()}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Review History */}
                <HistoryPanel history={history} onSelect={handleHistorySelect} />
            </section>

            {/* Right: Tutor panel */}
            <section className={styles.tutorSection}>
                <div className={styles.sectionLabel}>
                    <span className={`${styles.labelDot} ${styles.labelDotAccent}`} />
                    Tutor Feedback
                </div>

                <TutorPanel result={result} isLoading={isLoading} error={error} />
            </section>
        </main>
    )
}

export default function App() {
    const location = useLocation()
    const isDashboard = location.pathname === '/dashboard'

    return (
        <div className={styles.app}>
            {/* ── Header ── */}
            <header className={styles.header}>
                <div className={styles.headerInner}>
                    <div className={styles.logoArea}>
                        <div className={styles.logo}>
                            <span className={styles.logoGlyph}>⟡</span>
                            <span className={styles.logoText}>CodeTutor</span>
                            <span className={styles.logoBeta}>beta</span>
                        </div>
                        <p className={styles.tagline}>
                            An AI-powered Teaching Assistant for CS students
                        </p>
                    </div>

                    <nav className={styles.nav}>
                        <NavLink
                            to="/"
                            end
                            className={({ isActive }) =>
                                `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`
                            }
                        >
                            <span className={styles.navIcon}>◈</span>
                            Code Review
                        </NavLink>
                        <NavLink
                            to="/dashboard"
                            className={({ isActive }) =>
                                `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`
                            }
                        >
                            <span className={styles.navIcon}>◆</span>
                            Data Analysis
                        </NavLink>
                    </nav>
                </div>
            </header>

            {/* ── Pages with transition ── */}
            <div key={location.pathname} className={styles.pageTransition}>
                <Routes location={location}>
                    <Route path="/" element={<ReviewPage />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                </Routes>
            </div>

            {/* Footer */}
            {!isDashboard && (
                <footer className={styles.footer}>
                    <div className={styles.footerInner}>
                        <span>Final Year Project · Educational ML Code Review System</span>
                    </div>
                </footer>
            )}
        </div>
    )
}
