import { useState, useRef } from 'react'
import {
  Upload,
  Play,
  FileCode,
  Sparkles,
  ArrowRight,
  Shield,
  Zap,
  Code,
} from 'lucide-react'
import CodeEditor from '../CodeEditor/CodeEditor'
import { PYTHON_CODE, JAVA_CODE } from '../../mockData'
import styles from './SubmitView.module.css'

const PRESETS = [
  {
    id: 'python-sqlite',
    name: 'student_lookup.py',
    lang: 'python',
    desc: 'Python SQLite lookup with string concatenation, mutable default, and off-by-one',
    code: PYTHON_CODE,
    badge: 'SQL Injection · Loop bounds',
  },
  {
    id: 'java-sql',
    name: 'UserRepository.java',
    lang: 'java',
    desc: 'Java JDBC queries with raw Statement and unclosed Connection resource leak',
    code: JAVA_CODE,
    badge: 'Resource leak · SpotBugs',
  },
  {
    id: 'clean-sort',
    name: 'sort_utils.py',
    lang: 'python',
    desc: 'Clean bubble sort implementation with boundary checks and clean execution',
    code: `def bubble_sort(arr):
    """Sorts a list in ascending order without modifying the original."""
    items = list(arr)
    n = len(items)
    for i in range(n):
        for j in range(0, n - i - 1):
            if items[j] > items[j + 1]:
                items[j], items[j + 1] = items[j + 1], items[j]
    return items`,
    badge: 'Clean code (0 issues)',
  },
]

export default function SubmitView({
  initialCode = '',
  initialLang = 'python',
  onSubmit,
  isLoading = false,
}) {
  const [code, setCode] = useState(initialCode || PYTHON_CODE)
  const [language, setLanguage] = useState(initialLang)
  const [fileName, setFileName] = useState('student_lookup.py')
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef(null)

  function handleFileSelect(e) {
    const file = e.target.files?.[0]
    if (!file) return
    processFile(file)
  }

  function processFile(file) {
    setFileName(file.name)
    const lower = file.name.toLowerCase()
    if (lower.endsWith('.java')) setLanguage('java')
    else if (lower.endsWith('.py')) setLanguage('python')
    else if (lower.endsWith('.cs')) setLanguage('csharp')

    const reader = new FileReader()
    reader.onload = (ev) => {
      setCode(ev.target?.result || '')
    }
    reader.readAsText(file)
  }

  function handleDragOver(e) {
    e.preventDefault()
    setIsDragging(true)
  }

  function handleDragLeave() {
    setIsDragging(false)
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) processFile(file)
  }

  function handleLoadPreset(preset) {
    setCode(preset.code)
    setLanguage(preset.lang)
    setFileName(preset.name)
  }

  function handleReview() {
    if (!code.trim() || isLoading) return
    onSubmit({ code, language, filename: fileName })
  }

  const lineCount = code.split('\n').length
  const charCount = code.length

  return (
    <div className={styles.container}>
      {/* ── Left Column: Code Input & Editor ── */}
      <div className={styles.editorCol}>
        {/* Editor Top Bar */}
        <div className={styles.editorHeader}>
          <div className={styles.fileIdentity}>
            <FileCode size={15} className={styles.fileIcon} />
            <span className={styles.fileName}>{fileName}</span>
            <span className={styles.metaCount}>
              {lineCount} lines · {charCount} chars
            </span>
          </div>

          <div className={styles.headerRight}>
            {/* Language Selector */}
            <div className={styles.langSelector} role="radiogroup" aria-label="Language selection">
              {['python', 'java'].map((lang) => (
                <button
                  key={lang}
                  type="button"
                  className={`${styles.langBtn} ${language === lang ? styles.langBtnActive : ''}`}
                  onClick={() => setLanguage(lang)}
                  role="radio"
                  aria-checked={language === lang}
                >
                  {lang === 'python' ? 'Python' : 'Java'}
                </button>
              ))}
            </div>

            <button
              className={styles.uploadBtn}
              onClick={() => fileInputRef.current?.click()}
              title="Upload code file (.py, .java)"
            >
              <Upload size={13} />
              <span>Upload file</span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".py,.java,.cs"
              className={styles.hiddenInput}
              onChange={handleFileSelect}
            />
          </div>
        </div>

        {/* Drag and Drop Zone or Monaco Editor */}
        <div
          className={`${styles.editorArea} ${isDragging ? styles.dragging : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {isDragging && (
            <div className={styles.dropOverlay}>
              <Upload size={28} className={styles.dropIcon} />
              <p className={styles.dropText}>Drop Python or Java source file here</p>
            </div>
          )}

          <CodeEditor
            value={code}
            onChange={setCode}
            language={language}
            issues={[]}
          />
        </div>

        {/* Bottom Action Bar */}
        <div className={styles.bottomBar}>
          <div className={styles.tutorHint}>
            <Sparkles size={14} className={styles.hintIcon} />
            <span>CodeTutor will detect bugs, security flaws, performance bottlenecks, and explain why.</span>
          </div>

          <button
            className={styles.reviewBtn}
            onClick={handleReview}
            disabled={!code.trim() || isLoading}
          >
            {isLoading ? (
              <span className={styles.loadingSpinner} />
            ) : (
              <Play size={14} className={styles.playIcon} />
            )}
            <span>{isLoading ? 'Analyzing code…' : 'Start Code Review'}</span>
          </button>
        </div>
      </div>

      {/* ── Right Column: Presets & Educational Context ── */}
      <div className={styles.sidebarCol}>
        <div className={styles.sidebarSection}>
          <div className={styles.sidebarHeading}>
            <span>REALISTIC STUDENT SCENARIOS</span>
          </div>
          <p className={styles.sidebarSub}>
            Select a sample code snippet with common university programming mistakes:
          </p>

          <div className={styles.presetsList}>
            {PRESETS.map((p) => {
              const isSelected = fileName === p.name
              return (
                <button
                  key={p.id}
                  className={`${styles.presetCard} ${isSelected ? styles.presetSelected : ''}`}
                  onClick={() => handleLoadPreset(p)}
                >
                  <div className={styles.presetTop}>
                    <span className={styles.presetName}>{p.name}</span>
                    <span className={styles.presetBadge}>{p.badge}</span>
                  </div>
                  <p className={styles.presetDesc}>{p.desc}</p>
                </button>
              )
            })}
          </div>
        </div>

        <div className={styles.sidebarDivider} />

        {/* What to expect checklist */}
        <div className={styles.sidebarSection}>
          <div className={styles.sidebarHeading}>
            <span>TUTOR PIPELINE CHECKS</span>
          </div>

          <div className={styles.pipelineItems}>
            <div className={styles.pipeItem}>
              <Shield size={14} className={styles.pipeIcon} />
              <div>
                <div className={styles.pipeTitle}>Static Security Analysis</div>
                <div className={styles.pipeDesc}>Bandit & SpotBugs check for injection and leaks</div>
              </div>
            </div>

            <div className={styles.pipeItem}>
              <Zap size={14} className={styles.pipeIcon} />
              <div>
                <div className={styles.pipeTitle}>Deep Pattern Reasoning</div>
                <div className={styles.pipeDesc}>CodeBERT & AST verify logic and loop boundaries</div>
              </div>
            </div>

            <div className={styles.pipeItem}>
              <Code size={14} className={styles.pipeIcon} />
              <div>
                <div className={styles.pipeTitle}>Formative Teaching</div>
                <div className={styles.pipeDesc}>Interactive unified diffs with 1-click application</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
