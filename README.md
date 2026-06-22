# AI-Powered Educational Code Analyzer

An intelligent teaching assistant that helps Computer Science students identify bugs in their code and understand *why* those bugs occur not just that they exist.




## Project Structure

```
yxa342/
├── flask/                              # Backend (Flask REST API)
│   ├── app.py                          # Main entry point — orchestrates the 3-layer pipeline
│   ├── requirements.txt                # Python dependencies
│   ├── data/                           # Datasets used by the backend
│   ├── models/
│   │   ├── codebert_config.py          # Shared CodeBERT configuration
│   │   ├── CodeBERT_Python/            # Python classifier + fine-tuned weights
│   │   ├── CodeBERT_Java/              # Java classifier + fine-tuned weights
│   │   ├── CodeBERT_CSharp/            # C# classifier + fine-tuned weights
│   │   ├── codebert_baselines/         # Static analysis (Bandit) wrapper
│   │   └── llm/
│   │       ├── tutor.py                # LLM educational explainer (Qwen2.5-7B)
│   │       └── code_patterns.py        # Regex/AST pattern detectors (all languages)
│   ├── reports/                        # Generated analysis reports
│   ├── static/                         # Static assets
│   └── templates/                      # HTML templates
│
├── frontend/                           # Frontend (React + Vite)
│   ├── index.html                      # HTML entry point
│   ├── package.json                    # Node.js dependencies
│   ├── vite.config.js                  # Vite configuration
│   └── src/
│       ├── main.jsx                    # React entry point
│       ├── App.jsx                     # Main app — code review page, routing, history
│       ├── App.module.css              # App-level styles
│       ├── index.css                   # Global design tokens
│       ├── hooks/
│       │   └── useReview.js            # Custom hook for API calls
│       └── components/
│           ├── CodeEditor/             # Monaco Editor wrapper with error highlighting
│           ├── TutorPanel/             # LLM explanation renderer (Markdown)
│           └── Dashboard/              # Data analysis dashboard with plots & charts
│
├── training_modules/                   # Model training and evaluation scripts
│   ├── python/                         # Python CodeBERT + GraphCodeBERT training
│   ├── java/                           # Java CodeBERT training
│   └── csharp/                         # C# CodeBERT training
│
├── educational_llm/                    # LLM explainer experiments & evaluation
│   ├── run_explainer.py                # LLM explainer runner
│   ├── baselines/                      # 3-baseline comparison scripts
│   ├── data/                           # LLM experiment data
│   └── outputs/                        # Generated explanations
│
└── README.md                           # Project overview (this file)
```

---

## Technologies Used

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Backend** | Python 3, Flask | REST API server |
| **ML** | PyTorch, Transformers (HuggingFace) | CodeBERT inference + Qwen LLM |
| **Analysis** | Bandit, regex/AST patterns | Static analysis & rule-based detection |
| **Frontend** | React 18, Vite | UI framework & build tool |
| **Editor** | Monaco Editor | Code input (same engine as VS Code) |
| **Models** | `microsoft/codebert-base` | Fine-tuned bug classifier (3 languages) |
| | `Qwen/Qwen2.5-Coder-7B-Instruct` | Educational explanation generator |

---

## Installation & Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- A CUDA-compatible GPU is recommended for the LLM explainer (the system works without one, but the LLM layer will use a structured fallback instead)

### 1. Clone the Repository

```bash
git clone git@git.cs.bham.ac.uk:projects-2025-26/yxa342.git
cd yxa342
```

### 2. Backend Setup

```bash
cd flask
pip install -r requirements.txt
python app.py
```

The backend will run at `http://127.0.0.1:5001`.

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will run at `http://localhost:5173`.

### 4. Using the Application

1. Open `http://localhost:5173` in your browser
2. Paste your Python, Java, or C# code into the editor, or upload a `.py` / `.java` / `.cs` file
3. Click **Submit for Review**
4. Review the educational feedback in the Tutor panel on the right
5. Navigate to **Data Analysis** to explore training results and pipeline visualisations

---

## Author

**Yousef Aldali** — 2720540
**Supervisor:** Dr. Abhirup Ghosh

