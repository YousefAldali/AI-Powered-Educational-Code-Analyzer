import { useState, useRef } from 'react'
import CodeEditor from './components/CodeEditor/CodeEditor'
import TutorPanel from './components/TutorPanel/TutorPanel'
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

export default function App() {
    const [code, setCode] = useState(PLACEHOLDER)
    const [language, setLanguage] = useState('python')
    const [fileName, setFileName] = useState(null)
    const fileInputRef = useRef(null)

    const { result, isLoading, error, submit } = useReview()

    async function handleSubmit() {
        if (!code.trim()) return
        await submit({ code, language })
    }

    function handleFileChange(e) {
        const file = e.target.files?.[0]
        if (!file) return
        setFileName(file.name)
        const lang = file.name.endsWith('.java') ? 'java' : file.name.endsWith('.cs') ? 'csharp' : 'python'
        setLanguage(lang)
        const reader = new FileReader()
        reader.onload = (ev) => setCode(ev.target.result ?? '')
        reader.readAsText(file)
        // Reset input so re-uploading the same file triggers onChange
        e.target.value = ''
    }

    return (
        <div className={styles.app}>
            {/* ── Header ── */}
            <header className={styles.header}>
                <div className={styles.headerInner}>
                    <div className={styles.logo}>
                        <span className={styles.logoGlyph}>⟡</span>
                        <span className={styles.logoText}>CodeTutor</span>
                        <span className={styles.logoBeta}>beta</span>
                    </div>
                    <p className={styles.tagline}>
                        An AI-powered Teaching Assistant for CS students
                    </p>
                </div>
            </header>

            {/* ── Main split layout ── */}
            <main className={styles.main}>
                {/* Left: Editor */}
                <section className={styles.editorSection}>
                    <div className={styles.sectionLabel}>
                        <span className={styles.labelDot} />
                        Your Code
                        {fileName && <span className={styles.fileName}>{fileName}</span>}
                    </div>

                    <CodeEditor
                        value={code}
                        onChange={setCode}
                        language={language}
                        onLanguageChange={setLanguage}
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
                        <div className={styles.langToggle}>
                            {['python', 'java', 'csharp'].map((lang) => (
                                <button
                                    key={lang}
                                    className={`${styles.langBtn} ${language === lang ? styles.langBtnActive : ''}`}
                                    onClick={() => setLanguage(lang)}
                                    disabled={isLoading}
                                >
                                    {lang === 'csharp' ? 'C#' : lang.toUpperCase()}
                                </button>
                            ))}
                        </div>
                    </div>
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

            <footer className={styles.footer}>
                Final Year Project · Educational ML Code Review System
            </footer>
        </div>
    )
}
