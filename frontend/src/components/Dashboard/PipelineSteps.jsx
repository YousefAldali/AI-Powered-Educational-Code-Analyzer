import styles from './PipelineSteps.module.css'

// Numbered vertical timeline used for the pipeline diagrams.
// Each step: { kicker, title, text?, tone?, content? }
// tone picks the accent colour: blue | orange | purple | green | cyan | gray
export function Steps({ steps, caption }) {
    return (
        <figure className={styles.figure}>
            <ol className={styles.steps}>
                {steps.map((step, i) => (
                    <li key={step.title} className={`${styles.step} ${styles[`tone_${step.tone || 'blue'}`]}`}>
                        <div className={styles.marker} aria-hidden="true">{i + 1}</div>
                        <div className={styles.body}>
                            <div className={styles.kicker}>{step.kicker}</div>
                            <h4 className={styles.title}>{step.title}</h4>
                            {step.text && <p className={styles.text}>{step.text}</p>}
                            {step.content}
                        </div>
                    </li>
                ))}
            </ol>
            {caption && <figcaption className={styles.caption}>{caption}</figcaption>}
        </figure>
    )
}

// Grid of small cards (e.g. Layer 1 and Layer 2 side by side)
export function Tiles({ children }) {
    return <div className={styles.tiles}>{children}</div>
}

export function Tile({ label, title, sub, tone = 'blue', dashed = false }) {
    return (
        <div className={`${styles.tile} ${styles[`tone_${tone}`]} ${dashed ? styles.tileDashed : ''}`}>
            {label && <div className={styles.tileLabel}>{label}</div>}
            <div className={styles.tileTitle}>{title}</div>
            {sub && <div className={styles.tileSub}>{sub}</div>}
        </div>
    )
}

// Inline sequence of chips joined by arrows: A → B → C
export function Flow({ items }) {
    return (
        <ol className={styles.flow}>
            {items.map((item) => (
                <li key={item.title} className={styles.flowItem}>
                    <span className={styles.flowTitle}>{item.title}</span>
                    {item.sub && <span className={styles.flowSub}>{item.sub}</span>}
                </li>
            ))}
        </ol>
    )
}

// Small highlighted note under a step
export function Note({ children, tone = 'orange' }) {
    return <div className={`${styles.note} ${styles[`tone_${tone}`]}`}>{children}</div>
}
