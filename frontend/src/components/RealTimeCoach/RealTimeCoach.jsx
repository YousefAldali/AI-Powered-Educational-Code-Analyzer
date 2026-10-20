import { useState } from 'react'
import {
  Lightbulb,
  Check,
  Eye,
  EyeOff,
  Sparkles,
  HelpCircle,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react'
import CodeEditor from '../CodeEditor/CodeEditor'
import styles from './RealTimeCoach.module.css'

const COACH_PRESETS = [
  {
    id: 'mutable-default',
    title: 'Python: Mutable Default Argument',
    lang: 'python',
    code: `def track_submission(student_id, attempts=[]):
    attempts.append(student_id)
    print(f"Total recorded attempts: {len(attempts)}")
    return attempts

# Test calls
first = track_submission("alice")
second = track_submission("bob")
print(second)  # What will this print?`,
    hintLine: 1,
    hintTitle: 'Notice how `attempts=[]` behaves',
    tutorQuestion:
      'In Python, when is a default argument evaluated? When the function is defined, or every time it is called?',
    explanation:
      'Default arguments are evaluated once at function definition time. Both `alice` and `bob` will share the same `attempts` list, causing `len(attempts)` to grow on every invocation.',
    suggestedFix: `def track_submission(student_id, attempts=None):
    if attempts is None:
        attempts = []
    attempts.append(student_id)
    return attempts`,
  },
  {
    id: 'java-equals',
    title: 'Java: String Comparison with ==',
    lang: 'java',
    code: `public boolean authenticateUser(String inputPassword, String storedHash) {
    // Check if the input password matches stored record
    if (inputPassword == storedHash) {
        return true;
    }
    return false;
}`,
    hintLine: 3,
    hintTitle: 'Reference equality vs content equality',
    tutorQuestion:
      'In Java, what does the `==` operator compare when used on object references like `String`?',
    explanation:
      '`==` tests reference identity (memory address), not character sequence equality. Two distinct strings with identical characters will evaluate to false unless compared via `.equals()`.',
    suggestedFix: `public boolean authenticateUser(String inputPassword, String storedHash) {
    if (storedHash.equals(inputPassword)) {
        return true;
    }
    return false;
}`,
  },
  {
    id: 'unclosed-file',
    title: 'Python: File Descriptor Leak',
    lang: 'python',
    code: `def load_config(filepath):
    f = open(filepath, "r")
    data = f.read()
    # Missing f.close() or with statement
    return data.splitlines()`,
    hintLine: 2,
    hintTitle: 'Guaranteed resource cleanup',
    tutorQuestion:
      'What happens if an error occurs while reading the file? Does the operating system file descriptor get closed?',
    explanation:
      'Opening a file without a context manager (`with open(...)`) risks leaking file descriptors if an exception occurs before reaching cleanup.',
    suggestedFix: `def load_config(filepath):
    with open(filepath, "r") as f:
        return f.read().splitlines()`,
  },
]

export default function RealTimeCoach() {
  const [activePresetIndex, setActivePresetIndex] = useState(0)
  const currentPreset = COACH_PRESETS[activePresetIndex]

  const [code, setCode] = useState(currentPreset.code)
  const [quietMode, setQuietMode] = useState(true)
  const [hintExpanded, setHintExpanded] = useState(false)
  const [showDirectFix, setShowDirectFix] = useState(false)

  function handleSelectPreset(idx) {
    setActivePresetIndex(idx)
    setCode(COACH_PRESETS[idx].code)
    setHintExpanded(false)
    setShowDirectFix(false)
  }

  function handleApplyFix() {
    setCode(currentPreset.suggestedFix)
    setHintExpanded(false)
    setShowDirectFix(false)
  }

  return (
    <div className={styles.container}>
      {/* ── Toolbar ── */}
      <div className={styles.toolbar}>
        <div className={styles.leftGroup}>
          <div className={styles.titleArea}>
            <Sparkles size={15} className={styles.titleIcon} />
            <span className={styles.titleText}>REAL-TIME COACHING</span>
            <span className={styles.betaBadge}>Quiet Mode</span>
          </div>

          <div className={styles.divider} />

          {/* Scenario Tabs */}
          <div className={styles.presetTabs}>
            {COACH_PRESETS.map((p, idx) => (
              <button
                key={p.id}
                className={`${styles.presetTab} ${activePresetIndex === idx ? styles.presetTabActive : ''}`}
                onClick={() => handleSelectPreset(idx)}
              >
                {p.title}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.rightGroup}>
          <button
            className={`${styles.quietToggle} ${quietMode ? styles.quietActive : ''}`}
            onClick={() => setQuietMode(!quietMode)}
            title="Toggle quiet hints mode"
          >
            {quietMode ? <EyeOff size={13} /> : <Eye size={13} />}
            <span>{quietMode ? 'Quiet Mode (Default)' : 'Proactive Hints'}</span>
          </button>
        </div>
      </div>

      {/* ── Main Split View ── */}
      <div className={styles.split}>
        {/* Editor Area */}
        <div className={styles.editorPane}>
          <div className={styles.paneHeader}>
            <span className={styles.paneLabel}>INTERACTIVE EDITOR</span>
            <span className={styles.paneHint}>
              Type or modify code. Subtle hint bubbles appear without interrupting your flow.
            </span>
          </div>

          <div className={styles.editorBox}>
            <CodeEditor
              value={code}
              onChange={setCode}
              language={currentPreset.lang}
              issues={[]}
            />

            {/* In-Editor Floating Tutor Hint Bubble */}
            <div className={styles.inlineHintWrapper}>
              {!hintExpanded ? (
                <button
                  className={styles.hintPill}
                  onClick={() => setHintExpanded(true)}
                  aria-expanded="false"
                >
                  <Lightbulb size={13} className={styles.hintPillIcon} />
                  <span>Line {currentPreset.hintLine}: {currentPreset.hintTitle}</span>
                  <span className={styles.tapToInspect}>Click to view tutor question</span>
                </button>
              ) : (
                <div className={styles.hintBubble}>
                  <div className={styles.bubbleHeader}>
                    <div className={styles.bubbleTitleGroup}>
                      <Lightbulb size={14} className={styles.bubbleIcon} />
                      <span className={styles.bubbleTitle}>Tutor Reflection · Line {currentPreset.hintLine}</span>
                    </div>
                    <button
                      className={styles.bubbleCloseBtn}
                      onClick={() => setHintExpanded(false)}
                      aria-label="Close hint"
                    >
                      ✕
                    </button>
                  </div>

                  <div className={styles.bubbleBody}>
                    <div className={styles.questionCard}>
                      <HelpCircle size={14} className={styles.qIcon} />
                      <p className={styles.questionText}>{currentPreset.tutorQuestion}</p>
                    </div>

                    <p className={styles.explanationText}>{currentPreset.explanation}</p>

                    {showDirectFix && (
                      <div className={styles.fixPreview}>
                        <div className={styles.fixHeader}>Recommended Pattern</div>
                        <pre className={styles.fixCode}>{currentPreset.suggestedFix}</pre>
                      </div>
                    )}
                  </div>

                  <div className={styles.bubbleFooter}>
                    <button
                      className={styles.toggleFixBtn}
                      onClick={() => setShowDirectFix(!showDirectFix)}
                    >
                      {showDirectFix ? 'Hide suggested fix' : 'Show suggested fix'}
                    </button>

                    {showDirectFix && (
                      <button className={styles.applyBtn} onClick={handleApplyFix}>
                        <Check size={13} />
                        <span>Apply to editor</span>
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Info Column: Tutor Philosophy */}
        <div className={styles.tutorNotesPane}>
          <div className={styles.notesSection}>
            <div className={styles.notesHeading}>COACHING PHILOSOPHY</div>
            <p className={styles.notesText}>
              A strict linter interrupts students with warnings that encourage copy-pasting solutions
              without comprehension.
            </p>
            <p className={styles.notesText}>
              CodeTutor acts like a patient human lab assistant: it poses a guiding reflection question
              first, allowing university learners to self-correct before revealing the canonical fix.
            </p>
          </div>

          <div className={styles.notesDivider} />

          <div className={styles.notesSection}>
            <div className={styles.notesHeading}>ACTIVE SCENARIO DETAILS</div>
            <div className={styles.metaRow}>
              <span className={styles.metaLabel}>Language</span>
              <span className={styles.metaVal}>{currentPreset.lang.toUpperCase()}</span>
            </div>
            <div className={styles.metaRow}>
              <span className={styles.metaLabel}>Target Line</span>
              <span className={styles.metaVal}>Line {currentPreset.hintLine}</span>
            </div>
            <div className={styles.metaRow}>
              <span className={styles.metaLabel}>Pedagogical Focus</span>
              <span className={styles.metaVal}>{currentPreset.hintTitle}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
