import { useRef, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import styles from './CodeEditor.module.css'

// Figure out if they pasted Java, C#, or Python
function detectLanguage(code) {
    if (!code) return 'python'
    if (
        code.includes('public class') ||
        code.includes('System.out.') ||
        code.includes('import java.')
    ) return 'java'
    if (
        code.includes('using System') ||
        code.includes('namespace ') ||
        code.includes('Console.Write') ||
        code.includes('static void Main')
    ) return 'csharp'
    return 'python'
}

const THEME_DEF = {
    base: 'vs-dark',
    inherit: true,
    rules: [
        { token: '', foreground: 'e2e8f0', background: '020617' },
        { token: 'comment', foreground: '475569' },
        { token: 'keyword', foreground: '38bdf8' },
        { token: 'string', foreground: '4ade80' },
        { token: 'number', foreground: 'fbbf24' },
        { token: 'type', foreground: 'a78bfa' },
        { token: 'delimiter', foreground: '94a3b8' },
    ],
    colors: {
        'editor.background': '#020617',
        'editorGutter.background': '#020617',
        'editorLineNumber.foreground': '#2d4a6e',
        'editorLineNumber.activeForeground': '#38bdf8',
        'editorCursor.foreground': '#38bdf8',
        'editor.foreground': '#e2e8f0',
        'editor.lineHighlightBackground': '#0f172a',
        'editor.selectionBackground': '#1e3a8a55',
        'scrollbarSlider.background': '#1e293b88',
        'scrollbarSlider.hoverBackground': '#1e293bcc',
        'editorWidget.background': '#0b1120',
        'editorSuggestWidget.background': '#0b1120',
        'editorSuggestWidget.border': '#1e3352',
    },
}

export default function CodeEditor({ value, onChange, language, onLanguageChange, errorLines = [] }) {
    const editorRef = useRef(null)
    const monacoRef = useRef(null)
    const decorationsRef = useRef([])

    function handleMount(editor, monaco) {
        editorRef.current = editor
        monacoRef.current = monaco
        monaco.editor.defineTheme('tutorTheme', THEME_DEF)
        monaco.editor.setTheme('tutorTheme')
    }

    // Apply error line decorations when errorLines change
    useEffect(() => {
        const editor = editorRef.current
        const monaco = monacoRef.current
        if (!editor || !monaco) return

        const decorations = errorLines.map(line => ({
            range: new monaco.Range(line, 1, line, 1),
            options: {
                isWholeLine: true,
                className: 'error-line-highlight',
                glyphMarginClassName: 'error-glyph-margin',
                glyphMarginHoverMessage: { value: '⚠ Issue detected on this line' },
                overviewRuler: {
                    color: '#f87171',
                    position: monaco.editor.OverviewRulerLane.Full,
                },
                minimap: {
                    color: '#f87171',
                    position: monaco.editor.MinimapPosition.Inline,
                },
            },
        }))

        decorationsRef.current = editor.deltaDecorations(
            decorationsRef.current,
            decorations
        )
    }, [errorLines])

    // Auto-detect language when value changes externally (e.g. file upload)
    useEffect(() => {
        const detected = detectLanguage(value)
        if (detected !== language) onLanguageChange?.(detected)
    }, [value]) // eslint-disable-line

    function handleChange(val) {
        const code = val ?? ''
        onChange(code)
        const detected = detectLanguage(code)
        if (detected !== language) onLanguageChange?.(detected)
    }

    return (
        <div className={styles.wrapper}>
            <div className={styles.header}>
                <span className={styles.dots}>
                    <span /><span /><span />
                </span>
                <span className={styles.langBadge}>{language.toUpperCase()}</span>
                {errorLines.length > 0 && (
                    <span className={styles.errorBadge}>
                        {errorLines.length} issue{errorLines.length > 1 ? 's' : ''} found
                    </span>
                )}
            </div>
            <Editor
                height="420px"
                language={language}
                value={value}
                theme="tutorTheme"
                onChange={handleChange}
                onMount={handleMount}
                options={{
                    fontSize: 13,
                    fontFamily: "'Space Mono', monospace",
                    fontLigatures: true,
                    automaticLayout: true,
                    wordWrap: 'on',
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    tabSize: 4,
                    insertSpaces: true,
                    lineNumbersMinChars: 3,
                    padding: { top: 12, bottom: 12 },
                    scrollbar: { verticalScrollbarSize: 6, horizontalScrollbarSize: 6 },
                    overviewRulerLanes: 0,
                    renderLineHighlight: 'line',
                    cursorBlinking: 'smooth',
                    smoothScrolling: true,
                    contextmenu: false,
                    glyphMargin: true,
                }}
            />
        </div>
    )
}
