import { useRef, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import styles from './CodeEditor.module.css'

// ── Restrained syntax theme (light) ──
const LIGHT_THEME = {
  base: 'vs',
  inherit: true,
  rules: [
    { token: '', foreground: '1C1917', background: 'FAFAF8' },
    { token: 'comment', foreground: 'A8A29E', fontStyle: 'italic' },
    { token: 'keyword', foreground: '0F766E' },
    { token: 'string', foreground: '92400E' },
    { token: 'number', foreground: '1E40AF' },
    { token: 'type', foreground: '6D28D9' },
    { token: 'delimiter', foreground: '78716C' },
    { token: 'variable', foreground: '1C1917' },
    { token: 'function', foreground: '1C1917' },
  ],
  colors: {
    'editor.background': '#FAFAF8',
    'editorGutter.background': '#F4F4F1',
    'editorLineNumber.foreground': '#C7C3BA',
    'editorLineNumber.activeForeground': '#57534E',
    'editorCursor.foreground': '#0F766E',
    'editor.foreground': '#1C1917',
    'editor.lineHighlightBackground': '#F4F4F100',
    'editor.lineHighlightBorder': '#E0DDD600',
    'editor.selectionBackground': '#0F766E20',
    'scrollbarSlider.background': '#C7C3BA44',
    'scrollbarSlider.hoverBackground': '#A8A29E66',
    'editorWidget.background': '#F4F4F1',
    'editorSuggestWidget.background': '#F4F4F1',
    'editorSuggestWidget.border': '#E0DDD6',
  },
}

// ── Restrained syntax theme (dark) ──
const DARK_THEME = {
  base: 'vs-dark',
  inherit: true,
  rules: [
    { token: '', foreground: 'ECECEA', background: '18181B' },
    { token: 'comment', foreground: '63636B', fontStyle: 'italic' },
    { token: 'keyword', foreground: '14B8A6' },
    { token: 'string', foreground: 'D97706' },
    { token: 'number', foreground: '60A5FA' },
    { token: 'type', foreground: 'A78BFA' },
    { token: 'delimiter', foreground: '71717A' },
    { token: 'variable', foreground: 'ECECEA' },
    { token: 'function', foreground: 'ECECEA' },
  ],
  colors: {
    'editor.background': '#18181B',
    'editorGutter.background': '#1C1C1F',
    'editorLineNumber.foreground': '#3F3F46',
    'editorLineNumber.activeForeground': '#A1A1AA',
    'editorCursor.foreground': '#14B8A6',
    'editor.foreground': '#ECECEA',
    'editor.lineHighlightBackground': '#1C1C1F00',
    'editor.lineHighlightBorder': '#2E2E3300',
    'editor.selectionBackground': '#14B8A620',
    'scrollbarSlider.background': '#3F3F4644',
    'scrollbarSlider.hoverBackground': '#63636B66',
    'editorWidget.background': '#1C1C1F',
    'editorSuggestWidget.background': '#1C1C1F',
    'editorSuggestWidget.border': '#2E2E33',
  },
}

// Maps severity → decoration class names
const SEVERITY_CLASSES = {
  error:   { line: 'error-line-highlight',   glyph: 'error-glyph-margin' },
  warning: { line: 'warning-line-highlight',  glyph: 'warning-glyph-margin' },
  info:    { line: 'info-line-highlight',     glyph: 'info-glyph-margin' },
  style:   { line: 'info-line-highlight',     glyph: 'info-glyph-margin' },
}

export default function CodeEditor({
  value,
  onChange,
  language,
  readOnly = false,
  issues = [],
  onLineClick,
  height = '100%',
}) {
  const editorRef = useRef(null)
  const monacoRef = useRef(null)
  const decorationsRef = useRef([])

  function handleMount(editor, monaco) {
    editorRef.current = editor
    monacoRef.current = monaco

    monaco.editor.defineTheme('tutorLight', LIGHT_THEME)
    monaco.editor.defineTheme('tutorDark', DARK_THEME)

    // Pick theme based on current data-theme
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
    monaco.editor.setTheme(isDark ? 'tutorDark' : 'tutorLight')
  }

  // Watch for theme changes and update Monaco
  useEffect(() => {
    const observer = new MutationObserver(() => {
      const monaco = monacoRef.current
      if (!monaco) return
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
      monaco.editor.setTheme(isDark ? 'tutorDark' : 'tutorLight')
    })
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    })
    return () => observer.disconnect()
  }, [])

  // Apply gutter markers and line highlights based on issues
  useEffect(() => {
    const editor = editorRef.current
    const monaco = monacoRef.current
    if (!editor || !monaco) return

    const decorations = issues.map((issue) => {
      const cls = SEVERITY_CLASSES[issue.severity] || SEVERITY_CLASSES.info
      return {
        range: new monaco.Range(issue.line, 1, issue.line, 1),
        options: {
          isWholeLine: true,
          className: cls.line,
          glyphMarginClassName: cls.glyph,
          glyphMarginHoverMessage: { value: issue.title },
          overviewRuler: {
            color:
              issue.severity === 'error'
                ? '#B91C1C'
                : issue.severity === 'warning'
                ? '#92400E'
                : '#1E40AF',
            position: monaco.editor.OverviewRulerLane.Right,
          },
        },
      }
    })

    decorationsRef.current = editor.deltaDecorations(
      decorationsRef.current,
      decorations
    )
  }, [issues])

  // Scroll to a specific line when triggered externally
  function revealLine(lineNumber) {
    const editor = editorRef.current
    if (!editor) return
    editor.revealLineInCenter(lineNumber)
    editor.setPosition({ lineNumber, column: 1 })
  }

  // Expose revealLine to parent via ref pattern
  useEffect(() => {
    if (onLineClick) {
      // Store revealLine on the DOM for parent access (simple approach)
      const el = editorRef.current?.getDomNode()
      if (el) el.__revealLine = revealLine
    }
  })

  return (
    <div className={styles.wrapper}>
      <Editor
        height={height}
        language={language === 'csharp' ? 'csharp' : language}
        value={value}
        theme="tutorLight"
        onChange={readOnly ? undefined : onChange}
        onMount={handleMount}
        options={{
          readOnly,
          fontSize: 13,
          fontFamily: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace",
          fontLigatures: false,
          automaticLayout: true,
          wordWrap: 'on',
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          tabSize: 4,
          insertSpaces: true,
          lineNumbersMinChars: 3,
          padding: { top: 12, bottom: 12 },
          scrollbar: {
            verticalScrollbarSize: 6,
            horizontalScrollbarSize: 6,
          },
          overviewRulerLanes: 1,
          renderLineHighlight: 'none',
          cursorBlinking: 'smooth',
          smoothScrolling: true,
          contextmenu: false,
          glyphMargin: issues.length > 0,
          lineDecorationsWidth: issues.length > 0 ? 14 : 0,
          folding: false,
          renderWhitespace: 'none',
          guides: { indentation: false },
        }}
      />
    </div>
  )
}

// Helper to imperatively scroll the editor to a line
CodeEditor.revealLine = function (editorElement, lineNumber) {
  editorElement?.querySelector('.monaco-editor')?.__revealLine?.(lineNumber)
}
