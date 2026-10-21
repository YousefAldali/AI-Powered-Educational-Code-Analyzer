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
        { token: '', foreground: 'dce4f0', background: '0c1222' },
        { token: 'comment', foreground: '7d90ae', fontStyle: 'italic' },
        { token: 'keyword', foreground: '7aa3e3' },
        { token: 'string', foreground: '4ade80' },
        { token: 'number', foreground: 'fbbf24' },
        { token: 'type', foreground: 'a78bfa' },
        { token: 'delimiter', foreground: '94a3b8' },
    ],
    colors: {
        'editor.background': '#0c1222',
        'editorGutter.background': '#0c1222',
        'editorLineNumber.foreground': '#4d6283',
        'editorLineNumber.activeForeground': '#7aa3e3',
        'editorCursor.foreground': '#7aa3e3',
        'editor.foreground': '#dce4f0',
        'editor.lineHighlightBackground': '#111d32',
        'editor.lineHighlightBorder': '#111d32',
        'editor.selectionBackground': '#4a7cc955',
        'scrollbarSlider.background': '#2d4a6e88',
        'scrollbarSlider.hoverBackground': '#2d4a6ecc',
        'editorWidget.background': '#111d32',
        'editorSuggestWidget.background': '#111d32',
        'editorSuggestWidget.border': '#1e3352',
    },
}

export default function CodeEditor({ value, onChange, language, onLanguageChange, autoDetect = true, errorLines = [] }) {
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
                    color: '#d47272',
                    position: monaco.editor.OverviewRulerLane.Full,
                },
                minimap: {
                    color: '#d47272',
                    position: monaco.editor.MinimapPosition.Inline,
                },
            },
        }))

        decorationsRef.current = editor.deltaDecorations(
            decorationsRef.current,
            decorations
        )
    }, [errorLines])

    function handleChange(val) {
        const code = val ?? ''
        onChange(code)
        // Only guess the language while the user hasn't chosen one
        if (!autoDetect) return
        const detected = detectLanguage(code)
        if (detected !== language) onLanguageChange?.(detected)
    }

    return (
        <div className={styles.wrapper}>
            <div className={styles.header}>
                <span className={styles.dots} aria-hidden="true">
                    <span /><span /><span />
                </span>
                <span className={styles.badges}>
                    {errorLines.length > 0 && (
                        <span className={styles.errorBadge}>
                            {errorLines.length} issue{errorLines.length > 1 ? 's' : ''} found
                        </span>
                    )}
                    <span className={styles.langBadge}>{language === 'csharp' ? 'C#' : language.toUpperCase()}</span>
                </span>
            </div>
            <Editor
                height="clamp(280px, 55vh, 420px)"
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
