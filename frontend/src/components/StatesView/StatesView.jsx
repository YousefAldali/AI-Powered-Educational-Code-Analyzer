import { useState, useEffect } from 'react'
import {
  FileCode,
  CheckCircle2,
  AlertCircle,
  Play,
  RotateCcw,
  Sparkles,
  ShieldCheck,
  Cpu,
  PenTool,
  ArrowRight,
} from 'lucide-react'
import ReviewHero from '../ReviewHero/ReviewHero'
import { PYTHON_CODE, PYTHON_REVIEW } from '../../mockData'
import styles from './StatesView.module.css'

export default function StatesView({ onNavigateToSubmit }) {
  const [activeState, setActiveState] = useState('analyzing')
  const [analyzingStep, setAnalyzingStep] = useState(1)
  const [isReplaying, setIsReplaying] = useState(false)

  // Auto-progress steps in analyzing state demo
  useEffect(() => {
    if (activeState === 'analyzing') {
      const timer1 = setTimeout(() => setAnalyzingStep(2), 1800)
      const timer2 = setTimeout(() => setAnalyzingStep(3), 3600)
      return () => {
        clearTimeout(timer1)
        clearTimeout(timer2)
      }
    } else {
      setAnalyzingStep(1)
    }
  }, [activeState, isReplaying])

  function handleReplay() {
    setAnalyzingStep(1)
    setIsReplaying((prev) => !prev)
  }

  return (
    <div className={styles.container}>
      {/* ── State Switcher Bar ── */}
      <div className={styles.stateBar}>
        <div className={styles.barLabel}>
          <span className={styles.dot} />
          <span>SYSTEM STATES DEMO</span>
        </div>

        <div className={styles.stateButtons} role="tablist">
          <button
            className={`${styles.stateBtn} ${activeState === 'empty' ? styles.stateBtnActive : ''}`}
            onClick={() => setActiveState('empty')}
            role="tab"
            aria-selected={activeState === 'empty'}
          >
            1. Empty
          </button>

          <button
            className={`${styles.stateBtn} ${activeState === 'analyzing' ? styles.stateBtnActive : ''}`}
            onClick={() => setActiveState('analyzing')}
            role="tab"
            aria-selected={activeState === 'analyzing'}
          >
            2. Analyzing (Multi-step)
          </button>

          <button
            className={`${styles.stateBtn} ${activeState === 'review' ? styles.stateBtnActive : ''}`}
            onClick={() => setActiveState('review')}
            role="tab"
            aria-selected={activeState === 'review'}
          >
            3. Review Hero
          </button>

          <button
            className={`${styles.stateBtn} ${activeState === 'clean' ? styles.stateBtnActive : ''}`}
            onClick={() => setActiveState('clean')}
            role="tab"
            aria-selected={activeState === 'clean'}
          >
            4. No Issues Found
          </button>

          <button
            className={`${styles.stateBtn} ${activeState === 'error' ? styles.stateBtnActive : ''}`}
            onClick={() => setActiveState('error')}
            role="tab"
            aria-selected={activeState === 'error'}
          >
            5. Error
          </button>
        </div>
      </div>

      {/* ── State Canvas ── */}
      <div className={styles.canvas}>
        {/* 1. EMPTY STATE */}
        {activeState === 'empty' && (
          <div className={styles.emptyContainer}>
            <div className={styles.emptyCard}>
              <div className={styles.iconCircle}>
                <FileCode size={28} className={styles.accentIcon} />
              </div>
              <h2 className={styles.emptyTitle}>No code submitted for review yet</h2>
              <p className={styles.emptyDesc}>
                Paste your Python or Java code, or choose one of our sample student scripts to see
                how CodeTutor highlights issues and teaches safe patterns.
              </p>
              <button className={styles.primaryActionBtn} onClick={onNavigateToSubmit}>
                <span>Open Submission Screen</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* 2. ANALYZING STATE (MULTI-STEP PROGRESS) */}
        {activeState === 'analyzing' && (
          <div className={styles.analyzingContainer}>
            <div className={styles.analyzingCard}>
              <div className={styles.analyzingTop}>
                <div className={styles.analyzingTitleGroup}>
                  <h2 className={styles.analyzingTitle}>Review in Progress</h2>
                  <p className={styles.analyzingSub}>
                    Analyzing <code className={styles.codePill}>student_lookup.py</code> against
                    academic benchmarks
                  </p>
                </div>
                <button
                  className={styles.replayBtn}
                  onClick={handleReplay}
                  title="Replay progress animation"
                >
                  <RotateCcw size={13} />
                  <span>Replay steps</span>
                </button>
              </div>

              {/* Progress Steps */}
              <div className={styles.stepsList}>
                {/* Step 1 */}
                <div
                  className={`${styles.stepItem} ${
                    analyzingStep > 1
                      ? styles.stepCompleted
                      : analyzingStep === 1
                      ? styles.stepActive
                      : ''
                  }`}
                >
                  <div className={styles.stepRail}>
                    <div className={styles.stepDot}>
                      {analyzingStep > 1 ? (
                        <CheckCircle2 size={14} />
                      ) : analyzingStep === 1 ? (
                        <div className={styles.spinner} />
                      ) : (
                        <span>1</span>
                      )}
                    </div>
                    <div className={styles.stepLine} />
                  </div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepHeader}>
                      <ShieldCheck size={14} className={styles.stepIcon} />
                      <span className={styles.stepName}>Static Analysis</span>
                      <span className={styles.stepTool}>Flake8 · Bandit · PMD</span>
                    </div>
                    <p className={styles.stepDesc}>
                      Checking syntax validity, SQL concatenation risks, and resource lifecycle leaks.
                    </p>
                  </div>
                </div>

                {/* Step 2 */}
                <div
                  className={`${styles.stepItem} ${
                    analyzingStep > 2
                      ? styles.stepCompleted
                      : analyzingStep === 2
                      ? styles.stepActive
                      : styles.stepPending
                  }`}
                >
                  <div className={styles.stepRail}>
                    <div className={styles.stepDot}>
                      {analyzingStep > 2 ? (
                        <CheckCircle2 size={14} />
                      ) : analyzingStep === 2 ? (
                        <div className={styles.spinner} />
                      ) : (
                        <span>2</span>
                      )}
                    </div>
                    <div className={styles.stepLine} />
                  </div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepHeader}>
                      <Cpu size={14} className={styles.stepIcon} />
                      <span className={styles.stepName}>Pattern & Deep Learning Reasoning</span>
                      <span className={styles.stepTool}>CodeBERT Transformer</span>
                    </div>
                    <p className={styles.stepDesc}>
                      Evaluating code semantics, logic boundaries, and off-by-one loop conditions.
                    </p>
                  </div>
                </div>

                {/* Step 3 */}
                <div
                  className={`${styles.stepItem} ${
                    analyzingStep === 3 ? styles.stepActive : styles.stepPending
                  }`}
                >
                  <div className={styles.stepRail}>
                    <div className={styles.stepDot}>
                      {analyzingStep === 3 ? (
                        <div className={styles.spinner} />
                      ) : (
                        <span>3</span>
                      )}
                    </div>
                  </div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepHeader}>
                      <PenTool size={14} className={styles.stepIcon} />
                      <span className={styles.stepName}>Writing Tutor Feedback</span>
                      <span className={styles.stepTool}>Educational LLM</span>
                    </div>
                    <p className={styles.stepDesc}>
                      Generating plain-language explanations, correct examples, and unified patches.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 3. REVIEW HERO */}
        {activeState === 'review' && (
          <div className={styles.fullPane}>
            <ReviewHero
              initialCode={PYTHON_CODE}
              reviewData={PYTHON_REVIEW}
              onResetToSubmit={onNavigateToSubmit}
            />
          </div>
        )}

        {/* 4. NO ISSUES FOUND STATE */}
        {activeState === 'clean' && (
          <div className={styles.emptyContainer}>
            <div className={styles.cleanCard}>
              <div className={styles.cleanIconCircle}>
                <CheckCircle2 size={32} className={styles.cleanIcon} />
              </div>
              <h2 className={styles.cleanTitle}>Clean Code · 0 Issues Detected</h2>
              <p className={styles.cleanDesc}>
                Static analysis and pattern checks passed without flagging any vulnerabilities,
                syntax bugs, or performance leaks.
              </p>
              <div className={styles.cleanChecks}>
                <div className={styles.checkPill}>✓ Bandit security clean</div>
                <div className={styles.checkPill}>✓ Flake8 boundary clean</div>
                <div className={styles.checkPill}>✓ Proper resource handling</div>
              </div>
              <button className={styles.secondaryActionBtn} onClick={onNavigateToSubmit}>
                Review Another File
              </button>
            </div>
          </div>
        )}

        {/* 5. ERROR STATE */}
        {activeState === 'error' && (
          <div className={styles.emptyContainer}>
            <div className={styles.errorCard}>
              <div className={styles.errorIconCircle}>
                <AlertCircle size={32} className={styles.errorIcon} />
              </div>
              <h2 className={styles.errorTitle}>Syntax Error in Submitted Code</h2>
              <p className={styles.errorDesc}>
                Python parser could not compile the code due to an indentation inconsistency on line 6:
              </p>
              <pre className={styles.errorSnippet}>
                {`  File "student_lookup.py", line 6
    for i in range(len(rows) + 1):
    ^
IndentationError: expected an indented block after 'for' statement on line 5`}
              </pre>
              <div className={styles.errorRemedy}>
                <strong>Tutor Tip:</strong> In Python, whitespace and indentation define code blocks.
                Ensure each block inside a loop or function is indented by 4 spaces.
              </div>
              <button className={styles.primaryActionBtn} onClick={onNavigateToSubmit}>
                Back to Code Editor
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
