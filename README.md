## **Week 1 : Choosing my prject**

Before I met my supervisor, I spent some time thinking about what would help me after I graduate and finish university. I asked myself what things I like and what things I don’t. After a while, I realized that I really enjoy AI and that I’m good at it, so I decided I want to do something in that field.

I started thinking about what kind of project could help a student develop their programming skills faster and in a more efficient way. Then I came up with the idea of an automated code review tool something that helps students see where they are weak and shows them how to improve.

When I met my supervisor, we discussed the idea, and he suggested making it more interactive for example, allowing students to learn and get feedback while they are writing the code itself. He also mentioned that I could improve it even more by adding a feature that helps make the code more efficient for instance, if the code takes 4 or 5 lines, the system could suggest a shorter or more optimized version.

---


# Week 2 Meeting My Supervisor and Deciding What to Choose

# AI Code Review (IBM Reference)

AI code review is a tool that uses AI techniques to assist in reviewing code for quality, style, and functionality.

Before starting, it's important to note that machine learning (ML) models are used to identify problems and small bugs in code, as well as detect security issues and vulnerabilities.

AI code review tools often provide suggestions or even automated fixes helping developers save time and improve code quality.

---

## Key Components of AI Code Review

There are four crucial components that make up AI code review:

### 1. Static Code Analysis
Analyzes source code **before running a program** to catch potential issues early.

### 2. Dynamic Code Analysis
Tests the code **during execution** to detect potential issues, performance problems, and security vulnerabilities.

### 3. Rule-Based Systems
Uses **predefined rules and best practices** to analyze code consistency, style, and known error patterns.

### 4. NLP and LLMs
Natural Language Processing (NLP) models trained on large datasets of code form the core of modern AI code review.  
Large Language Models (LLMs) such as GPT 4 are increasingly being used to provide context-aware feedback and suggestions.

---

## Reference
Source: [IBM — AI Code Review](https://www.ibm.com/think/insights/ai-code-review)




# Week 3 Progress Report

This week, I focused on reading more about my project topic and trying to understand it in more depth.  
I spent time learning about how to **collect data**, **train models**, **build the tool**, and **evaluate the results**.  
I also started exploring research papers and documentation related to **CodeBERT** to understand how it works and how it can be used for automated code review.

---

### Key Points
- Read and summarized key concepts about data collection, model training, and evaluation.  
- Studied how **CodeBERT** connects natural language and programming languages.  
- Took notes to outline the main stages of the project.  
- Planned an initial workflow for the project (data ,model ,tool , evaluation).  

---

### Summary
This week helped me get a clearer idea of how to start implementing the project and what areas I need to focus on next.




## **Week 4: PromptLayer (Revolutionizing Code Reviews with AI-Powered Automation)**

**Link:** [https://www.promptlayer.com/research-papers/revolutionizing-code-reviews-with-ai-powered-automation](https://www.promptlayer.com/research-papers/revolutionizing-code-reviews-with-ai-powered-automation)

This week I read a new paper called **“Code Review Automation via Multi task Federated LLM  An Empirical Study”** by *Jahnavi Kumar* and *Sridhar Chimalakonda*. It talks about how **AI** and **federated learning** can help automate the code review process.

The idea is that normal code reviews take a lot of time, so they used a **large language model** that can handle multiple things at once like checking if a code change needs a review, writing comments, and even suggesting how to improve the code.

The researchers from **IIT Tirupati** propose using a **multi-task federated LLM**, meaning:

* **Federated learning** lets multiple organizations collaboratively train a shared model *without sharing their private code.*
* The model is trained for **three tasks at once:**

  1. Predict whether a code change needs review
  2. Generate comments explaining issues or suggestions
  3. Propose refined code

They tested two different multi-task training strategies:

* **Sequential Training**  trained tasks one after another, but the model forgot older tasks
* **Cumulative Training**  trained all tasks together, which worked better

In general, the paper showed that this kind of AI system could really help developers **save time**, **keep their code quality high**, and **protect data privacy**.

---


## **Week 5: Medium (Revolutionizing Code Review with Large Language Models: A Deep Dive into code2Prompt and its Peers)**

**Link:** [https://medium.com/anolytics/revolutionizing-code-review-with-large-language-models-a-deep-dive-into-code2prompt-and-its-peers-fa8213b47cfd](https://medium.com/anolytics/revolutionizing-code-review-with-large-language-models-a-deep-dive-into-code2prompt-and-its-peers-fa8213b47cfd)

This week I read a Medium article titled **“Revolutionizing Code Review with Large Language Models: A Deep Dive into code2Prompt and its Peers.”**
It explores how large language models like **GPT, CodeBERT**, and others are transforming code review. The main focus is on **code2Prompt**, comparing it with tools like **GitHub Copilot**, **DeepCode**, and **AI21 Labs Code Review**.

The main goal of the article is to show how AI can **automate, prioritize, and improve the code review process.**

---

### 1) **Introduction**

Code review is very important for:

* Ensuring code quality
* Detecting bugs
* Promoting collaboration among engineers

Manual reviews, however, are **slow, subjective, and inconsistent**, especially when dealing with large codebases.
LLMs like GPT or CodeBERT can speed up the process by **automating** parts of it intelligently.

---

### 2) **The Current Landscape of LLM Based Code Review Tools**

The article discusses three main AI powered tools currently in use:

* **GitHub Copilot**
* **DeepCode**
* **AI21 Labs Code Review**

These tools help with syntax and bug detection but are **not fully intelligent reviewers**.

---

### 3) **code2Prompt : The New Solution**

**code2Prompt** is presented as an **advanced LLM based reviewer** that overcomes many traditional limitations by using **semantic and contextual understanding** of the code.

#### **How it works:**

1. **Code Chunking**

   * The code is divided into smaller logical blocks (chunks).
   * This reduces overload and helps the AI focus on one piece at a time.
   * Uses graph based algorithms to find dependencies between functions and modules.

2. **Contextualization**

   * After chunking, the model analyzes how each code piece fits into the entire project.
   * It uses **dependency, control flow, and data flow analysis** to understand relationships.
   * This leads to **more accurate and relevant feedback.**

3. **Prioritized Review**

   * Not all code is equally risky so code2Prompt ranks chunks by importance.
   * It looks at:

     * Code complexity
     * Type of change
     * Potential issues or style violations
   * High risk areas (like security critical code) are reviewed first.

4. **Code Quality Assessment**

   * Goes beyond bug detection it evaluates:

     * Code style (PEP8, Google, Airbnb standards)
     * Best practices
     * Maintainability and readability
   * Suggests **refactors** or style improvements to make code cleaner.

---

### 4) **Challenges and Limitations**

Even with AI, there are still issues:

* **Bias & Incompleteness:** LLMs can reflect their training data and miss edge cases.
* **Explainability:** Hard to know why the AI made certain suggestions.
* **Cost & Compute:** Running large models for every pull request can be expensive and slow.

---

### 5) **How This Relates to My Work**

This article directly connects to my project idea building an **AI code reviewer** that gives **smart and contextual feedback.**
code2Prompt uses techniques I can integrate into my own system, such as:

* Code **chunking**
* **Contextual** review
* **Risk-based prioritization**
* **Code style evaluation**

These methods will help me design a more **intelligent and structured code review system** for my project.

---

## **Week 6: Kinde (Reading More on How to Start the Project)**

**Link:** [https://kinde.com/learn/ai-for-software-engineering/code-reviews/ai-code-review-automation-building-custom-linting-rules-with-llms/](https://kinde.com/learn/ai-for-software-engineering/code-reviews/ai-code-review-automation-building-custom-linting-rules-with-llms/)

This week I continued reading more about how to **start building the AI code review project from scratch.**
The article explains how traditional code reviews are very important for software quality, but they are also **slow and time consuming.** Static tools like linters can catch syntax or style errors, but they can’t give **deep, contextual feedback** like a senior engineer would.
This is where **AI powered code review** comes in using **Large Language Models (LLMs)** to create **custom linting rules** that go far beyond what normal static tools can do.

---

### 1) **What is AI-Powered Code Review?**

AI-powered code review uses **LLMs** to analyze code changes and give feedback based on **custom natural language rules.**
The AI reviewer acts like an **editor**, suggesting improvements to structure, clarity, and style but following your team’s unique best practices and architecture, not just generic rules.

---

### 2) **How It Works**

Automating code review with an LLM means integrating it with your **CI/CD pipeline**.
The main steps are:

1. **Trigger Event** – Pipeline starts when code is pushed.
2. **Gather Context** – Collect files and diffs for review.
3. **Define Rules** – Write custom NLP rules for how code should be reviewed.
4. **Construct the Prompt** – Combine the code and the rules into a clear prompt.
5. **Call the LLM API** – Send the prompt to the model for analysis.
6. **Post Feedback** – Return comments or suggestions automatically.

---

### 3) **Use Cases for Custom AI Rules**

The biggest advantage of this approach is that it can enforce **complex logic and team conventions** that static tools can’t handle, such as:

* **Architectural Consistency:** e.g. `auth-service` should never make direct database calls; it must use the `user-management-service` API.
* **Security Vulnerabilities:** Identify unsafe logical paths or missing checks.
* **Code Quality & Maintainability:** Suggest splitting large functions or improving efficiency.
* **Proper Documentation:** Make sure all major changes include updated docs or comments.

---

### 4) **Challenges and Misconceptions**

Even with AI, there are still challenges:

* **It’s a reviewer, not a dictator:** LLM feedback should be treated as suggestions, not rules that block merging.
* **Cost:** Each pull request triggers API calls, so costs can add up quickly.
* **Latency:** Large models can make feedback slow, so optimization is important.
* **Prompt Engineering:** Clear and specific prompts lead to much better feedback.

---

### 5) **Best Practices for Implementation**

Some good tips from the article:

* **Start small:** Begin with 1–2 simple, high-value rules before expanding.
* **Iterate your rules:** Update and evolve them as your codebase grows.
* **Combine with traditional tools:** Use linters for syntax and AI for deep, contextual feedback.
* **Secure API keys:** Store them safely in CI/CD secrets (like GitHub Secrets or GitLab variables).
* **Be specific:** Instead of vague rules, write detailed instructions like “Ensure every function has a JSDoc comment block describing its purpose, parameters, and return value.”

---

### 6) **How This Helps My Project**

This guide helps me understand **how to practically start building** my AI code review tool.
It gives me a **clear workflow**  how to integrate the model into the pipeline, define my own review rules, and mix AI with existing linting tools.
This is exactly what I need to begin implementing my project step by step.

---

## Week 7 Report – Flask
 (https://flask.palletsprojects.com/en/stable/)

This week I started coding parts of my project. Before doing anything big, I wanted to choose a simple and clear way to begin. So I did a bit of research and found something called **Flask**. It’s a web application framework in Python, and honestly it looked very easy to understand.

After reading more about it, I actually liked it a lot. It’s lightweight, simple, and gives me full control over how I want my backend to look. It doesn’t force anything, and that’s perfect for me at this stage of the project.

So I started building a small Flask web application. Nothing complicated, just a clean and simple design that helps me get used to how Flask works. I also made a basic page where you can paste code directly or upload a `Python` file. This is my first step toward the real system where students will send their code for analysis.

This week was mainly about understanding Flask, setting everything up, and creating the first version of my web app. It’s a small step, but it already looks good and gives me a clear direction for what I want to do next.


## Week 8 Report – Analyzer and Security

- https://flake8.pycqa.org/en/latest/
- https://bandit.readthedocs.io/en/latest/
- https://github.com/microsoft/CodeBERT/blob/master/README.md
- https://www.researchgate.net/publication/347233117_CodeBERT_A_Pre-Trained_Model_for_Programming_and_Natural_Languages
- https://huggingface.co/microsoft/codebert-base


This week, I worked on the analysis and security aspects of my project, as outlined in my proposal. I focused on integrating and testing **Bandit** and **Flake8**, and I also spent time gaining a deeper understanding of **CodeBERT** and its limitations to better guide the development of the project.

I added Bandit and Flake8 into my Flask application, ran several tests, and confirmed that both tools work as expected, with the exception of an issue related to infinite `while` loops. Since this is a semantic error, it will likely require an AI-based approach to resolve later in the project.

Additionally, I researched more about CodeBERT, the model I will be using for code analysis. I identified several limitations:  
- CodeBERT can only analyze **one file at a time**  
- It cannot naturally handle **multiple interconnected files**  
- It has an **input limit of 512 tokens**

These constraints will affect the usability and functionality of the tool. To address this, I plan to implement a method to structure and pass multiple related files to the model. I will also explore approaches for increasing input capacity, such as splitting code intelligently, summarizing portions of it, or potentially switching to a more powerful model in the future.





## Week 9 Report:  Model Understanding, Tokenization & Baseline Setup

This week was mainly about building a proper foundation before adding the machine learning model into my system. At the start, I wasn’t fully sure how to integrate CodeBERT or even where to place the different components inside the project. This lack of clarity made it difficult to start the implementation, so I focused first on understanding how the model processes code and how the different baselines fit together.

Once I understood the tokenizer → embeddings → transformer → classifier pipeline, everything started to fall into place and I was finally able to plan out how I will integrate the model.

---

## Interface Updates

- Added the Monaco editor.
- Improved the design of the tool to make it cleaner, more readable, and easier to use.

---

## Main Challenges This Week

- Not knowing where to begin with CodeBERT integration.
- Confusion about how tokenization, embeddings, and vectorization differ.
- Trying to understand why CodeBERT uses 768-dimensional embeddings.
- Learning both classical ML approaches and transformer based approaches at the same time.
- Making Baseline B clear but also aware of its limitations.
- Realising I needed the theory before any serious coding.

A lot of this week was understanding, not implementation, but it should save time later.

---

## Baselines for My Project

I finalised the list of baselines I will use to evaluate CodeBERT. Each baseline represents a different level of complexity, from classical tools to modern transformer models, and maybe later i will be adding more based on my supervisor.

### Baseline A: Static Analysis Tools (Bandit + Flake8)  
**Status:** (Completed)

These tools provide rule based checks for style issues and simple security problems. They are useful, but they cannot detect deeper logic errors or semantic bugs. This baseline gives me a traditional, non-ML reference point.

---

### Baseline B: Keyword Matching (Very Simple Rules)  
**Status:** (Completed)

This baseline checks for obvious risky patterns such as:

- Infinite loops.
- Unsafe or risky functions.
- Inputs without validation.

It is intentionally weak, but it shows how simple heuristics perform and creates a clear gap that CodeBERT should be able to fill.

---

### Baseline C: TF-IDF + Logistic Regression (Classical ML)  
**Status:** In Progress

This baseline will:

- Convert code into TF-IDF vectors.
- Train a Logistic Regression classifier.
- Predict whether code is “buggy” or “clean”.

It is easy to train and explain, and it will help show the difference between classical ML and transformer-based models. This baseline is important because it provides a fair mid-level comparison.

---

### Baseline D: CodeBERT (Transformer Model)  
**Status:** Preparation Phase

This is the main model for my FYP. It uses:

- A BPE tokenizer.
- 768-dimensional embeddings.
- Multiple transformer layers.
- A classification head on top.

This model should capture structure, context, and meaning in the code, making it more capable than the previous baselines. I will start integrating it once the baselines are fully set up.

---

## Tokenizer & Vectorization Notes

Understanding how text is processed before reaching the model was a major focus this week. This helped me understand why different baselines behave the way they do.

### 1. BPE Tokenizer (CodeBERT)

CodeBERT uses a Byte bair Encoding tokenizer, which breaks code into subword units rather than whole words. This is important because programming languages have huge numbers of unique identifiers. BPE:

- Handles new variable and function names.
- Works across multiple programming languages.
- Treats symbols and operators consistently.

---

### 2. Embeddings (768-Dimensional)

After tokenization, each token is mapped to a 768-dimensional embedding vector. These embeddings represent:

- Context.
- Syntax.
- Code structure.
- Relationships between parts of the code.

This is how CodeBERT forms a deeper understanding of the input instead of simply counting words.

---

### 3. TF-IDF (For Baseline C)

TF-IDF converts code into numeric values based on how often each token appears and how important it is across the dataset. It does not capture context, but:

- It is simple.
- It is easy to interpret.
- It provides a solid classical baseline.

---

### 4. Comparing Vectorization Approaches

#### CodeBERT (BPE + Embeddings)

- Learns from large code datasets.
- Understands structure and meaning.
- Captures relationships between variables, functions, and control flow.
- Suitable for detecting more complex logic and semantic bugs.

#### TF-IDF

- Counts words without context.
- Simple to train.
- Good for establishing a baseline.
- Helps highlight the improvement from using transformer-based models.

---


This week was mostly about understanding the foundation I need before implementing the model. I improved the design with Monaco, completed Baselines A and B, and prepared for Baseline C and CodeBERT. I also learned how tokenization, embeddings, and vectorization work, which finally gave me a clear picture of how the model will fit into the system.



# Week 10 Report : Evaluation Preparation and Baselines

## Overview
This week focused on preparing the project for proper evaluation.  
The main goal was to finalise the baselines, prepare a test dataset, and understand how to fairly compare CodeBERT against simpler approaches.

## Dataset Preparation
I prepared a clean evaluation dataset consisting of buggy and non-buggy Python code snippets.

Key points:
- The same test set will be used for all models
- No overlap between training and testing data
- Code samples are kept small to fit CodeBERT’s 512-token limit

This ensures a fair and controlled comparison.

## Baseline Definitions

### Baseline A – Static Analysis
This baseline uses Flake8 and Bandit to detect:
- Style violations
- Common programming errors
- Basic security issues

This represents traditional rule-based analysis tools.

### Baseline B – Keyword Matching
A very simple heuristic approach:
- Flags patterns such as `while True`, `eval()`, and unsafe `input()`
- No learning or context awareness

This baseline is intentionally weak to highlight its limitations.

### Baseline C – Classical Machine Learning
A lightweight machine learning baseline using:
- Code tokenisation
- TF-IDF feature extraction
- Logistic Regression for classification

This provides a strong non-deep-learning comparison.

## Model Understanding
I also focused on understanding how CodeBERT processes source code:
- Code is split into subword tokens
- Tokens are converted into embedding vectors
- A classification head predicts buggy or non-buggy code

This helped in planning evaluation and analysis.

## Evaluation Plan
The planned evaluation metrics include:
- Accuracy
- Precision and recall
- Manual inspection of detected issues

Both quantitative and qualitative results will be reported.

## Identified Limitations
Some current limitations were identified:
- Only single-file analysis is supported
- No cross-file context is considered
- Large files must be truncated due to token limits

These limitations will be discussed as future work.




# Week 11 – Data Collection + The Leakage Problem 

Links : 
https://www.kaggle.com/datasets/shamimhasan8/python-code-bug-and-fix-pairs?resource=download


This week I focused on the dataset itself and why it is tricky for machine learning. I collected my data from Kaggle, and the dataset is **not** independent random code samples. Instead, it contains **buggy and fixed code in pairs**, meaning every buggy code snippet has a matching corrected version.

## Example

**ID = 100**

### Buggy
```python
def add(a, b):
    return a - b
````

### Fixed

```python
def add(a, b):
    return a + b
```

## The Key Issue: Data Leakage

The key issue is that these two pieces of code are **almost identical**. This creates a major machine learning problem: **data leakage**.

If the model sees the buggy version during training and then sees the fixed version during testing (or the opposite), it can **“cheat”** by recognising near-duplicate patterns instead of actually learning how to detect bugs. This would produce **fake high accuracy** that does not represent real performance.

## The Golden Rule of ML

> Never let the model see the exam while it is studying.

In my case:

* **Training = studying**
* **Testing = exam**
* **Buggy/Fixed pairs = near-duplicate questions**

So if I split the dataset randomly by rows, I would cause leakage automatically.

## What I Learned This Week

This week was mainly about understanding the dataset structure and why I must use a **correct splitting method** (e.g., splitting by pair/group/ID so both versions stay together) before training any model.

## Week 12 : Fixing the Data Properly (`prepare_data.py` + 80/10/10 Split)

This week I fixed the dataset splitting problem properly by creating a script called `prepare_data.py`. I realised I cannot do machine learning correctly without having:

- **Train set**
- **Validation set**
- **Test set**

And most importantly, these splits must not share **near-duplicate pairs** (buggy vs fixed versions of the same problem). If they do, the model can “cheat” and the evaluation becomes invalid.

### What `prepare_data.py` Does

- Reads the raw CSV file
- Extracts **unique Problem IDs**
- Shuffles the IDs using a **fixed random seed** (so the split is reproducible)
- Splits the IDs into:
  - **80% training**
  - **10% validation**
  - **10% test**
- For each Problem ID, it creates two labeled examples:
  - Buggy code → label **1** (bug present)
  - Fixed code → label **0** (no bug)
- Writes the final clean files:
  - `train.csv`
  - `val.csv`
  - `test.csv`

### Why Splitting by ID Matters

The key point is that splitting by **Problem ID** keeps buggy and fixed versions together in the same split:

- **ID 100 → Train** (buggy + fixed)
- **ID 101 → Test** (buggy + fixed)

So now there is:
- **no cheating**
- **no leakage**
- **scientifically valid evaluation**

### Challenges I Faced This Week

- **Near-duplicate data problem:** the buggy and fixed versions are extremely similar, so random splitting by rows breaks evaluation.
- **Choosing the right split method:** I had to split by **ID/group** instead of rows to stop leakage properly.
- **Reproducibility:** without a fixed seed, each split would change every run, making results hard to compare fairly.
- **Label consistency:** I had to keep labels consistent across the whole project (Buggy = 1, Fixed = 0) so training and evaluation are not confusing.
- **Balancing the splits:** using 80/10/10 means I need enough data in validation and test to measure performance reliably.





## Week 13 – Training Pipeline and Baselines (A, B, C)

Link: 
(Baseline A,B,C)
https://mdpi-res.com/entropy/entropy-22-01057/article_deploy/entropy-22-01057.pdf?version=1600699607

https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10820528&tag=1

https://dl.acm.org/doi/pdf/10.1145/3695993

https://arxiv.org/abs/2505.17928

https://ieeexplore.ieee.org/document/10799479

https://link.springer.com/content/pdf/10.1007/s11265-022-01740-z.pdf

https://consensus.app/papers/details/29216b9524965df9898bc90b754b9f8e/?utm_source=share&utm_medium=clipboard



This week focused on what happens **after data preparation** and how the different baselines fit into the overall training and evaluation pipeline. Once `prepare_data.py` completes, the dataset split becomes final and the **test set is locked**. From this point onward, the test data is never used during training, and test labels are never inspected. This ensures that all evaluation results remain fair and unbiased.

---

## Purpose of Baselines

The baselines are included to answer a critical research question:

**Is CodeBERT genuinely effective, or does it only appear strong without proper comparison?**

By evaluating CodeBERT against simpler and more traditional approaches, the project demonstrates whether improvements come from real semantic understanding rather than superficial patterns.

---

### Baseline A – Static Analysis (Bandit Only)

Baseline A uses **Bandit** to scan source code for security vulnerabilities and risky patterns such as `eval()` and `exec()`.

Flake8 was intentionally disabled because it mainly detects syntax and formatting issues. Since the dataset contains many syntax-level bugs, including Flake8 would artificially inflate accuracy without requiring any learning.

Restricting this baseline to Bandit creates a fairer **security-only** comparison and prevents static tools from dominating the results.

---

### Baseline B – Keyword Matching

Baseline B is the simplest possible approach and relies purely on string matching. It flags code as buggy if specific patterns appear.

**Example:**

python
if "while True" in code:
    buggy


This baseline has no understanding of structure, context, or intent. It only checks for exact matches, making it intentionally weak but useful as a lower-bound reference.

---

### Baseline C – TF-IDF + Logistic Regression

Baseline C is a classical machine-learning approach that converts source code into numerical features using TF-IDF and then trains a Logistic Regression classifier. This baseline represents a middle ground between simple heuristics and deep learning models.

---

### Baseline C: How It Works (Simple Explanation)

### 1. TF-IDF: Converting Code to Numbers

First, the model looks at the code and counts important words. It does not understand code like a human; instead, it converts the source code into a large table of numbers.

* **TF (Term Frequency):** How often does a word (such as `eval`, `while`, or `exec`) appear in this file?
* **IDF (Inverse Document Frequency):** How rare is this word across all files?

Common words like `import` receive a low score, while rare or suspicious words receive a higher score.

---

### 2. Logistic Regression: Assigning Weights

This is the step where the model “draws the line.” During training, logistic regression learns a weight for every word.

**Positive weights (indicating buggy code):**

* `eval` → +5.2
* `exec` → +4.8
* `shell` → +3.1

**Negative weights (indicating clean code):**

* `def` → −1.2
* `return` → −0.8
* `class` → −0.5

Words commonly found in buggy code push the score up, while words common in clean code push it down.

---

### 3. The Math: “Drawing the Line”

To classify a new piece of code, the model calculates a total score:

```
Score = (TF-IDF of `eval` × 5.2) + (TF-IDF of `def` × -1.2) + ...
```

* The decision line is at **0**
* If `Score > 0`, the code is predicted as **BUGGY**
* If `Score < 0`, the code is predicted as **CLEAN**

In simple terms, “drawing the line” means finding the right set of weights so that buggy code ends up on one side of the line and clean code on the other.

---

## Limitations of Baseline C



Despite being more powerful than simple heuristics, Baseline C has important limitations. It ignores token order and context, meaning expressions such as `1 - 2` and `2 - 1` may appear similar. It also struggles with very short or trivial code snippets, where limited lexical information leads to sparse feature vectors.

In such cases, predictions may approach random behaviour, with confidence close to 50%. This highlights a key limitation of bag-of-words approaches: they cannot capture program semantics.

---

## Motivation for CodeBERT

Baseline C is not designed to truly understand code. Its role is to act as a strong classical machine-learning baseline that exposes the limits of token-frequency-based representations.

The consistent performance gap between Baseline C and CodeBERT demonstrates the necessity of transformer-based models that leverage contextual embeddings and learned programming language semantics.




## Week 14 – CodeBERT, Evaluation, EDA, Error Analysis, and Flask Demo

This week I focused on the deep learning part of the project and the full evaluation pipeline. I also completed the analysis scripts that support the final results and reporting.

### CodeBERT (Deep Learning Model)

CodeBERT is a pre-trained deep learning model trained on millions of source code examples across multiple programming languages. In this project, I did not train CodeBERT from scratch. Instead, I fine-tuned it for my specific task, which is classifying code as **buggy** or **fixed**.

In my implementation, CodeBERT works as follows:
- Code is tokenized using **Byte Pair Encoding (BPE)**
- Token order and context are preserved
- The model is fine-tuned using `train.csv`
- Validation is performed using `val.csv`
- The trained model is saved as `codebert_finetuned`

Unlike TF-IDF, CodeBERT understands context. For example, it can detect that changing `+` to `-` alters program behaviour, not just the token value.

### Evaluation (evaluate_final.py)

To produce reliable and reproducible results, I used a dedicated evaluation script called `evaluate_final.py`. This script:
- Loads the locked `test.csv`
- Runs all models (baselines and CodeBERT)
- Computes the following metrics:
  - Accuracy
  - Precision
  - Recall
  - F1-score
- Saves all results to `evaluation_results.csv`

This ensures that all reported results are generated in a controlled and fair manner.

### Exploratory Data Analysis (generate_eda.py)

EDA was used only to understand the dataset, not for training. The analysis showed that:
- The dataset is balanced between buggy and fixed samples
- Code length distributions are similar for both classes
- No trivial shortcuts exist in the data

This confirms that the classification task is non-trivial.

### Error Analysis (error_analysis.py)

Error analysis was used to examine model mistakes. The script:
- Saves misclassified samples
- Helps identify failure patterns
- Supports discussion of model limitations in the report

The test set was never used for retraining.

### Flask Web Application (Demo Only)

Finally, all models were integrated into a Flask web application. The web app:
- Runs all models on user-submitted code
- Displays predictions side-by-side
- Visualises differences between approaches

The Flask application is used **only for demonstration purposes**. All official results reported in the project are produced by the evaluation scripts, not the web interface.



# Week 15 – Testing, Validation, and System Flow

This week focused on testing the complete system end-to-end and formalising the design using flowcharts. At this stage, the project moves from isolated components to a fully connected and validated system. The main objective was to clearly demonstrate how data flows through the system, how models are trained and evaluated, and why the results are scientifically valid.

## Overall System Pipeline

The automated code review system starts with paired buggy–fixed code samples collected from Kaggle. These pairs are then processed using a leakage-safe data preparation strategy based on problem IDs, ensuring that related buggy and fixed versions are never split across training and testing.

Multiple baselines are evaluated alongside a transformer-based model to provide a fair comparison. These include static analysis, rule-based heuristics, and a classical machine-learning approach using TF-IDF and Logistic Regression. The strongest model, CodeBERT, is fine-tuned specifically for the bug-detection task. All models are evaluated using standard classification metrics, and their outputs are made available through a user-facing web interface.

## System Design and Workflow

The system is organised around two complementary workflows:

1. **The user interaction and execution flow**, which describes how users interact with the system.
2. **The model training and evaluation pipeline**, which governs how data is processed and models are assessed.

Separating these workflows ensures that the system is both usable in practice and methodologically correct from a machine-learning perspective.

### 1. User Interaction Flow (AI Code Review System)

The user interaction flow begins when a student opens the web dashboard and provides source code. Code can be supplied either by uploading a file (Python or Java) or by pasting code directly into the editor.

A strict input validation step ensures that only supported formats are accepted. If validation fails, the system immediately returns an error message and prevents invalid input from reaching the backend. Once valid input is confirmed, the system naturally detects the programming language and initiates the analysis.

The backend then executes a hybrid analysis pipeline consisting of:

* Static analysis
* Rule-based heuristics
* Classical machine-learning models
* A fine-tuned CodeBERT model

Results from all models are aggregated and presented through a structured dashboard. This includes a model comparison table, detected issues with explanations, and suggested improvements. After reviewing the output, the user may analyse another piece of code, at which point the process correctly loops back to the input stage.

### 2. Model Training and Evaluation Pipeline

The training pipeline begins by loading the raw Kaggle dataset containing paired buggy and fixed code samples. Before any training occurs, a dedicated data preparation and quality-control stage is applied. This stage removes duplicates, mitigates data leakage, and performs basic code cleaning and tokenisation.

This step is critical because buggy and fixed versions of the same code are often nearly identical. If handled incorrectly, models could memorise patterns and achieve artificially high accuracy.

After preparation, the dataset is split into:

* 80% training
* 10% validation
* 10% test

Labels are assigned consistently, where clean code is labelled as 0 and buggy or insecure code is labelled as 1.

### 3. Parallel Model Configuration and Training

Four models are configured and evaluated in parallel:

* **Baseline A – Static Analysis**: Security-focused tools that are configured once and do not involve learning.
* **Baseline B – Rule-Based Keywords**: Manually defined patterns targeting risky constructs such as eval() or infinite loops.
* **Baseline C – Classical Machine Learning**: TF-IDF vectorisation followed by Logistic Regression.
* **CodeBERT – Transformer-Based Model**: A pre-trained model fine-tuned on the prepared dataset.

Only Baseline C and CodeBERT are trainable models. Static analysis and rule-based baselines are intentionally excluded from optimisation loops because they do not learn from data.

### 4. Validation Loop and Model Optimisation

After training, the machine-learning models are evaluated on the validation set. This stage is used exclusively for hyperparameter tuning and model selection.

If validation performance is not satisfactory, the pipeline loops back to the training stage. This allows adjustments such as:

* Hyperparameter tuning for Baseline C
* Fine-tuning configuration changes for CodeBERT

This iterative loop reflects standard machine-learning practice and ensures that the test set remains untouched until final evaluation. Static baselines are excluded from this loop because they are non-trainable.

Once validation performance is acceptable, all four models are frozen and evaluated exactly once on the locked test set.

### 5. Evaluation, Analysis, and Deployment

Final evaluation includes accuracy, precision, recall, F1-score, and confusion matrices. In addition to aggregate metrics, an error analysis stage examines false positives and false negatives to better understand model behaviour and limitations.

Visualisations such as ROC curves and heatmaps are generated to support comparative analysis. Rather than selecting models dynamically at runtime, the comparison is used analytically to justify why CodeBERT outperforms simpler baselines.

All models are then deployed within the Flask web application, allowing users to compare outputs interactively. The pipeline concludes with the generation of the final project report, documenting methodology, experiments, and findings.

## Ablation Study on CodeBERT Fine-Tuning

An ablation study was conducted to isolate the effect of task-specific fine-tuning. Two configurations were compared:

* A pre-trained CodeBERT model used without fine-tuning
* The same model fine-tuned on the bug-detection dataset

Both configurations used the same architecture, evaluation protocol, and locked test set. The pre-trained model achieved 50% accuracy and 0% F1, indicating that it failed to detect buggy code and defaulted to predicting all samples as clean. In contrast, the fine-tuned model achieved 95% accuracy and approximately 95% F1, correctly identifying the majority of buggy samples.

This demonstrates that CodeBERT’s effectiveness depends critically on task-specific fine-tuning, rather than pre-training alone.

## OLD vs NEW Evaluation (Clarification)

The old version of the system lacked hyperparameter tuning, ablation studies, statistical testing, and detailed error analysis. Although the models were functional, the results were harder to defend academically.

The new version includes documented leakage prevention, extensive hyperparameter tuning, results from a formal ablation study, confusion matrices for all models, statistical significance testing, and full reproducibility. The reported numbers are real outputs generated by the evaluation scripts, not estimated values.

This final version represents a scientifically valid, reproducible, and defensible system, suitable for both practical deployment and academic evaluation.

---

# Week 16 Report — Java & C# Integration and Multi-Language Training Challenges

## References and Resources

* InferredBugs repository (Java & C# dataset):
  [https://github.com/microsoft/InferredBugs/tree/main](https://github.com/microsoft/InferredBugs/tree/main)

* Long-context and code understanding limitations in transformers:
  [https://arxiv.org/pdf/2306.14893](https://arxiv.org/pdf/2306.14893)

* Recent work on code understanding and multi-language modelling:
  [https://arxiv.org/html/2509.10199v3](https://arxiv.org/html/2509.10199v3)

* Empirical software engineering study on bug datasets:
  [https://link.springer.com/content/pdf/10.1007/s10664-024-10558-1.pdf](https://link.springer.com/content/pdf/10.1007/s10664-024-10558-1.pdf)

* Microsoft Infer / InferSharp dataset release:
  [https://www.microsoft.com/en-us/download/details.aspx?id=103554](https://www.microsoft.com/en-us/download/details.aspx?id=103554)

* Code representation learning and defect prediction:
  [https://arxiv.org/pdf/2105.12787](https://arxiv.org/pdf/2105.12787)

---

## Overview

This week focused on extending the project beyond Python by integrating Java and C# bug–fix pairs using the InferredBugs dataset. In parallel, the original Python dataset was revised to improve consistency and tooling compatibility.

The main objective was to evaluate whether multi-language training with CodeBERT improves generalisation or introduces new challenges. While the integration was technically successful, the experiments revealed fundamental issues related to dataset quality, token limits, and supervision strength, particularly for Python.

---

## Dataset Expansion — Java & C# (InferredBugs)

### Raw Dataset

* Source: InferredBugs-main.zip
* Structure:

  * Thousands of nested folders
  * Each folder represents a single bug instance
  * Files:

    * method_before.txt (buggy code)
    * method_after.txt (fixed code)

### Extraction and Standardisation (extract_inferred_bugs.py)

A custom extraction script was implemented to ensure full compatibility with the existing pipeline. The script:

* Recursively scans all dataset folders
* Extracts paired buggy and fixed methods
* Outputs data using the same schema as the Python dataset:

```
id, buggy_code, fixed_code, commit_message, commit_url, date, language
```

For clarity and maintainability, the outputs were split into:

* java_bug_fix_pairs.csv
* csharp_bug_fix_pairs.csv

---

## ID Management, Cleaning, and Python Dataset Revision

### ID Renumbering

To avoid ID collisions:

* Python: 1–1000
* Java: 1001–9295 (8,295 samples)
* C#: 9296–12186 (2,891 samples)

The original dataset folder name was preserved in the commit_message field to maintain traceability.

### Line Number Cleaning (Java and C#)

Many files contained line prefixes such as:

```
55: if (x == 0)
```

These were removed using regex-based cleaning to produce clean, compilable source code. This step was essential for correct tokenisation and semantic learning.

### Python Dataset Cleanup (Consistency and VS Code Compatibility)

The original Python dataset was revised to improve consistency across languages and tools:

* Removed emojis and Markdown-style formatting
* Normalised all files to contain plain source code only
* Ensured full compatibility with VS Code and downstream tokenisation
* Prevented non-code tokens from influencing embeddings or classification

---

## Final Integration (prepare_data.py)

* Combined Python, Java, and C# into a unified dataset
* 12,186 unique problem IDs (~24,000 total code samples)
* Data split:

  * 80% training
  * 10% validation
  * 10% test
* Enforced strict data leakage prevention

  * No problem ID appears in more than one split

Temporary extracted folders and archives were removed after validation to keep the repository clean.

---

## Experiments Conducted and Runtime

### Mixed Training (Python + Java + C#)

* Runtime: not explicitly recorded
* Best validation accuracy: 57.47%

Observed behaviour:

* Strong bias toward predicting buggy
* Very low recall for clean
* Fixed code frequently misclassified as buggy

---

### Java-Only Training

* Runtime: 2 hours 22 minutes
* Best validation accuracy: 64.54%

Java showed the strongest performance, indicating clearer and more consistent bug–fix signals.

---

### Python-Only Training

* Runtime: 37 minutes
* Best validation accuracy: 50.00%

The model failed to learn meaningful decision boundaries and collapsed to predicting a single class.

---

### C#-Only Training

* Runtime: 43 minutes
* Best validation accuracy: 54.84%

Performance was unstable, suggesting weaker or noisier supervision signals compared to Java.

---

## Key Challenges Identified

### Accuracy Drop After Multi-Language Training

Accuracy dropped from approximately 93% (Python-only earlier experiments) to around 53–57% after integrating Java and C#. This reflects increased task difficulty due to longer code sequences, truncation, cross-language distribution shift, and inconsistent bug definitions.

### Token Limit (512 Tokens)

CodeBERT only processes tokens up to its maximum sequence length. For long Java and C# methods, the buggy or fixed lines may fall outside the visible context, leading to misclassification of fixed code as buggy.

### Extremely Weak Supervision in Python

Analysis of Python bug–fix pairs revealed:

* Average character difference: 2.2 characters
* 98% of pairs differ by fewer than 10 characters

Such minimal edits provide insufficient signal for sequence-level classification, explaining the 50% accuracy ceiling.

### Dataset Imbalance by Language

Dataset size distribution:

* Java: 13,236 samples
* C#: 4,620 samples
* Python: 1,640 samples

This imbalance increases the likelihood that majority-language patterns dominate mixed training.

---

## Outcomes of Week 16

* Integrated Java and C# into the dataset pipeline
* Cleaned and standardised all datasets under a unified schema
* Executed mixed and language-specific training experiments
* Identified the root cause of Python underperformance
* Collected detailed runtime and evaluation diagnostics





Alright — here’s **Week 17** rewritten in **your style** (simple, direct, like a student), and I added **real links** (copy-paste).

---

## Week 17 Report: Fixing the Python Problem + New Metrics (AP / AUROC)

### Links (real)

```txt
RoBERTa docs (Transformers):
https://huggingface.co/docs/transformers/en/model_doc/roberta

CodeBERT model card:
https://huggingface.co/microsoft/codebert-base

CodeBERT paper (PDF):
https://arxiv.org/pdf/2002.08155

BUGLAB paper (PDF):
https://arxiv.org/pdf/2105.12787

Microsoft CodeBERT GitHub repo:
https://github.com/microsoft/CodeBERT

Muennighoff/python-bugs dataset:
https://huggingface.co/datasets/Muennighoff/python-bugs

BugLab / BUGLAB reference repo (Microsoft NeurIPS 2021):
https://github.com/microsoft/neurips21-self-supervised-bug-detection-and-repair
```

([Hugging Face][1])

---

## 1) The main problem (Python is different)

### What I noticed

* Python bug–fix pairs are **too similar**
* The average diff is like **2 characters**, and most are **< 10 chars**
* Examples: `0 → 1`, `- → +`, `[0] → [1]`, `>` vs `>=`, small rename

### Why this kills CodeBERT (in my setup)

* I’m training CodeBERT as **sequence classification**
* Input = whole snippet
* Label = Buggy or Clean

But in Python:

* buggy and fixed look **almost identical**
* so the model sees “same input” but **different label**
* the bug signal is tiny and gets **drowned** by the rest of the code (and truncation)

So learning becomes unstable → model just guesses / collapses to 1 class.

This explains why Python was stuck at **~50%** before, while Java/C# worked normally.

([Hugging Face][1])

---

## 2) BUGLAB idea (why I didn’t switch now)

I looked at BUGLAB because it solves the exact weakness:

* It can **localise the bug token**, not just “buggy/clean”
* It uses **graph representation (data/control flow)** + a special model (GNN style)

But the issue:

* It needs a totally different pipeline (graph building + new training architecture)
* It’s not a “change dataset” thing, it’s a **new system**
* would take roughly **1–2 weeks** to implement properly in my project

So for now I stayed in the CodeBERT pipeline and fixed the data + evaluation.

([arXiv][2])

---

## 3) Experiments I ran (and what happened)

### Test A : Synthetic-only (ChatGPT generated)

* Time: **56 minutes**
* Validation accuracy: **~97%**
* Clean/Buggy balanced

This looks amazing but it mainly proves:

* the model learns **synthetic patterns**
* not real-world bugs

---

### Test B — Real + lots of Synthetic (20k + 2.5k)

This failed hard on real data:

* Real accuracy goes back to **~50%**
* The model basically learns: “synthetic style = I know it, real style = guess / bias”

So this is a classic **distribution shift** problem.

---

### Test C — New direction: Quality > Quantity (worked)

I switched strategy:

* Use **curated real data** instead of huge synthetic volume

Results:

* Muennighoff alone (1k): val accuracy around **0.76–0.78**
* Merged HF (1k) + cleaned real/Kaggle (1k) → **2,000 samples**
* Peak validation: **83.75%**

This was the first setup that actually generalised properly.

([Hugging Face][3])

---

## 4) Pipeline upgrades (major improvements)

This week I also fixed the *evaluation validity* and made it more “examiner-proof”:

### What changed

* **Leakage-safe splitting**

  * split by pair ID before expanding buggy/fixed
  * stops buggy + fixed versions leaking into different splits

* **Diff-window extraction**

  * only keep ±5 lines around the change
  * removes noise + reduces truncation

* **Added AP + AUROC**

  * accuracy alone is not enough
  * AP is good for bug detection ranking
  * AUROC gives threshold-independent separability

* **Checkpointing by best AP**

  * saves best model for what I actually care about
  * not just accuracy

* **Error analysis outputs**

  * confusion matrix plots
  * failed cases CSV (ID + prob)

---

## 5) Final results (this week)

### Python (after fixing pipeline)

* **Accuracy: 81.05%**
* **AP: 92.13%**
* **AUROC: 91.27%**

This basically confirms:

* the “Python 50% issue” was mainly **dataset + evaluation setup**
* not “CodeBERT is broken”

---

### Java (real + synthetic, after metric upgrade)

* Test Accuracy: **0.7384** (earlier run)
* After AP/AUROC training, validation metrics improved strongly (AP ~0.92+)
* Confusion matrix + failed cases saved for report



---

### C# (new bundle + best-AP selection)

* Validation improved over epochs
* Best AP saved automatically (`best_ap`)
* Final test accuracy reported: **0.6275**
* Confusion matrix + failed cases with probabilities generated

---

## 6) Main conclusion (Week 17 takeaway)

**Python failed before because the bug signal was too tiny (few characters), so sequence-level classification gets contradictory supervision.**

The fix was:

* better data (curated + cleaned)
* better inputs (diff windows)
* correct evaluation (leakage-safe split)
* better metrics (AP/AUROC + best-AP checkpoints)

BUGLAB is still a strong future option, but it needs a different architecture and pipeline.









# Week 18 Report

# Overview

This week I restructured my FYP into four clear system parts.

I decided to temporarily skip **Part 1 (CodeBERT final optimisation)** and return to it later after improving the dataset quality and understanding the training behaviour better.

## System Structure (4 Parts)

1. **Part 1 – CodeBERT Training & Strong Baseline**
2. **Part 2 – Educational LLM (Qwen 2.5 Coder)**
3. **Part 3 – Adding Haskell**
4. **Part 4 – Connecting Everything Together (Full ACRT pipeline)**

---

# Part 1 – CodeBERT Baseline

## Research Reading

Reviewed:

- CodeBERT & Transformer papers
- IBM Self-Attention explanation
- Qwen technical reports
- https://huggingface.co/papers/2409.12186
- https://huggingface.co/papers/2407.10671
- https://huggingface.co/papers/2309.00071

Improvements made:

- Cleaner training loop
- Proper validation tracking
- Saving BEST_AP checkpoints
- Added AP & AUROC metrics
- Improved reproducibility
- Better shard handling

---

## Initial Problem – Overfitting

Dataset: Small 6,000 synthetic Python samples

Observed:

- Fast overfitting
- High train accuracy
- Weak validation performance
- Synthetic data too predictable
- Poor syntax diversity

Conclusion:
Dataset not strong enough for real generalisation.

---

# Switching to Real Dataset – TSSB-3M

## Initial Extraction

From 3M samples:

- 2,545,792 → 637,125 rows
- 75% duplicates removed

### Cleaning Summary

| Cleaning Step | Removed |
|---------------|----------|
| Exact duplicates | 1,904,867 |
| Too short (<10 chars) | 3,628 |
| Too long (>2000 chars) | 33 |
| Non-code | 139 |

Final:
- 637,125 unique rows
- 23 bug patterns
- 129MB CSV

---

## Second Cleaning Pass

| Cleaning Step | Removed |
|---------------|----------|
| Exact duplicates | 274,391 |
| Too short | 868 |
| Too long | 7 |
| Non-code | 45 |

Result:
- 453,846 → 178,535 rows
- 39% kept
- 38MB final dataset

---

# Upgrade to CTSSB-1M (Cleaner Version)

Source:
https://github.com/cedricrupb/TSSB3M

Converted 10 `.jsonl.gz` files into:

`ctssb_1m_raw.csv`

### Raw Dataset

- 966,985 records
- Columns:
  - id
  - buggy_code
  - fixed_code
  - project
  - commit_sha
  - likely_bug
  - sstub_pattern

---

## CTSSB Cleaning Results

Initial: 966,985  
Final Kept: 861,655  

Removed:

- Null values: 27
- Duplicates: 103,912
- Too short: 1,308
- Too long: 83

Final file:

`clean/languages/python/ctssb_1m_cleaned.csv` (154MB)

This is now the main Python training dataset.

---

# Training Strategy Fix

### Old Approach (Problematic)

Used both buggy and fixed per pair:

```python
samples.append(buggy)
samples.append(fixed)
````

Issue:

* 2 samples per pair
* Potential leakage
* Model memorisation risk

---

### New Approach (Corrected)
- I said let me try a new approach but that wasnt the best idea. because it wasnt generalising well. and the model wasnt learning the bug patterns well.
```python
use_buggy = random.random() < 0.5
if use_buggy:
    samples.append(buggy)
else:
    samples.append(fixed)
```

Now:

* 1 sample per pair
* Reduced leakage
* Better generalisation
* More realistic binary setup

---

# CodeBERT Training Results (CTSSB-1M)

Best validation:

* Val Accuracy ≈ 57.7%
* AP ≈ 0.6244
* AUROC ≈ 0.6175

Observation:

* Train accuracy steadily increases
* Validation plateaus around epoch 6–7
* Mild overfitting after that

Conclusion:
Dataset is much harder.
Model learning real bug patterns.
 
 But I havent Teststed it in a real Code after improvments yet.

---

# Part 2 – Educational LLM

Model used:

**Qwen2.5-Coder-7B-Instruct (4-bit)**

Tested on Kaggle.

Successful:

* Model loads correctly
* 4-bit quantization works
* 20 sample test completed
* Output saved correctly

---

# Initial LLM Problems

Observed:
* Making More Educational Content
* Hallucinated diffs
* Broken formatting
* Truncated outputs
* Missing sections

---

# Major Engineering Fix  Grounded Diff Injection

Implemented:

* Ground truth diff injection
* Strict format enforcement
* Hard fallback system

---

## 100 Sample Evaluation

Results:

* Fake diff: 0
* Format compliance: 100%
* 93% high-quality explanations
* 7% safe fallback

Meaning:

* Prompt engineering is strong
* Diff grounding works
* System is robust

---

# Next Steps

## Part 1 (Return Later)

* Tune CodeBERT further
* Try diff-window input
* Compare full snippet vs changed lines
* Improve generalisation

## Part 2

* Scale LLM to larger subset
* Qwen2.5-Coder 7B 
* Improve hallucination handling
* Possibly fine-tune explainer layer

## Part 3

* Add Haskell dataset
* Keep system language-agnostic
* Extend training pipeline

## Part 4

Integrate:

* CodeBERT classifier
* LLM explainer
* Multi-language support
* Final educational pipeline

---

# Reflection

This week focused heavily on:

* Dataset engineering
* Cleaning
* Removing duplicates
* Fixing LLM hallucinations
* Improving robustness

The system is now transitioning from:

"Experimental prototype"

to

"Research-pipeline".

Major breakthrough:
Educational LLM is now stable and grounded. But need a bit more improvements. next week i will try to improve it. and try it in a real dataset.

---



# Week 19 Report


##  Papers & Reading This Week

This week I focused on strengthening the theoretical foundation of my project before scaling experiments further.

I reviewed:

* CodeBERT paper
  [https://dl.acm.org/doi/pdf/10.1145/3524842.3528505](https://dl.acm.org/doi/pdf/10.1145/3524842.3528505)

* IBM – Self-Attention explanation
  [https://www.ibm.com/think/topics/self-attention](https://www.ibm.com/think/topics/self-attention)

* Qwen2.5-Coder-7B-Instruct
  [https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct)

* Recent LLM-for-code papers:
  [https://huggingface.co/papers/2409.12186](https://huggingface.co/papers/2409.12186)
  [https://arxiv.org/abs/2409.12186](https://arxiv.org/abs/2409.12186)

  [https://huggingface.co/papers/2407.10671](https://huggingface.co/papers/2407.10671)
  [https://arxiv.org/abs/2407.10671](https://arxiv.org/abs/2407.10671)

  [https://huggingface.co/papers/2309.00071](https://huggingface.co/papers/2309.00071)
  [https://arxiv.org/abs/2309.00071](https://arxiv.org/abs/2309.00071)

* TSSB-3M repository
  [https://github.com/cedricrupb/TSSB3M/tree/main?tab=readme-ov-file](https://github.com/cedricrupb/TSSB3M/tree/main?tab=readme-ov-file)

These readings helped me better understand:

* How CodeBERT is properly evaluated.
* How self-attention works internally.
* How modern LLMs for code are structured.
* Why dataset quality is more important than dataset size.

---

#  CodeBERT – Overfitting Issue

At the beginning of the week, I trained CodeBERT on a small Python dataset (~6000 samples).

Observed behaviour:

* Training accuracy kept increasing.
* Validation accuracy plateaued early.
* The model started memorising repetitive patterns like `return None`.

So clearly:

* The dataset was too small.
* The synthetic patterns were too simple.
* Or duplication was causing memorisation.

This pushed me to move to a large real-world dataset.

I also tested the trained model manually on different code snippets more than **8 times** this week to observe prediction stability and generalisation across different bug types.

---

#  TSSB-3M Dataset Cleaning

I extracted the TSSB-3M dataset and performed heavy cleaning.

Initial extraction:

* 2,545,792 rows

After cleaning:

* 637,125 unique rows
* ~75% were duplicates

### Removed:

| Cleaning Step          | Removed   |
| ---------------------- | --------- |
| Exact duplicates       | 1,904,867 |
| Too short (<10 chars)  | 3,628     |
| Too long (>2000 chars) | 33        |
| Non-code entries       | 139       |

This was a big realisation.

If I had trained on raw 3M data, the model would likely memorise duplicated patterns instead of learning diverse bug behaviour.

Further filtering reduced:

* 453,846 → 178,535 rows
* Only 39% retained

This confirmed duplication is a major issue in mined datasets.

---

#  CTSSB-1M (Cleaner Dataset)

After reviewing the dataset paper more carefully, I identified CTSSB-1M as a cleaner subset of TSSB-3M.

I converted all `.jsonl.gz` files into:

```
flask/data/raw/languages/python/ctssb_1m_raw.csv
```

* 966,985 bug fixes
* 241 MB

### Cleaning Results:

| Metric             | Value   |
| ------------------ | ------- |
| Initial records    | 966,985 |
| Final kept         | 861,655 |
| Duplicates removed | 103,912 |
| Too short removed  | 1,308   |
| Too long removed   | 83      |

Final dataset:

```
clean/languages/python/ctssb_1m_cleaned.csv
```

* 154 MB
* 861,655 high-quality samples

This is now my main training dataset.

Much more realistic than my previous synthetic dataset.

---

#  Sampling Strategy Improvement

Previously:

* I used BOTH buggy and fixed per pair (2 samples).

Now:

* I randomly select only ONE per pair.

```python
use_buggy = random.random() < 0.5
```

Why this matters:

* Reduces correlation.
* Reduces leakage.
* Improves generalisation.
* Lowers overfitting risk.

This was an important structural change in the training pipeline.

---

#  CodeBERT Training Results

After improving the training and evaluation code (aligned more closely with the paper and official repo structure):

Best validation results around Epoch 7:

* Validation Accuracy ≈ 0.577
* Average Precision (AP) ≈ 0.624
* AUROC ≈ 0.617

After epoch 7:

* Training accuracy keeps increasing.
* Validation performance slightly drops.

This indicates mild overfitting, but expected at this stage.

Important point:
The model is no longer just memorising simple patterns.
The task is clearly non-trivial.

---

#  Educational LLM – First Integration

Started integrating the Educational LLM stage.

Model:

* Qwen2.5-Coder-7B-Instruct (4-bit quantised)

Platform:

* Kaggle GPU

Pipeline:

1. Load CodeBERT predictions.
2. Pass code + diff to LLM.
3. Generate structured 5-section explanation.
4. Save results to CSV.

Initial testing:

* 20 samples → successful.
* Then 100 samples → successful.

---

#  Hallucination Issue & Fix

At first, the LLM produced:

* Fake diff lines.
* Broken formatting.
* Incomplete sections.
* Cut code blocks.

After improving prompt grounding and adding a fallback system:

On 100 samples:

*  100% format compliance
*  93% high-quality grounded explanations
*  7% handled safely by fallback
*  0 fake diffs

The fallback mechanism ensures:

* No corrupted outputs.
* No hallucinated patch lines.
* All diffs grounded in real data.

This is a major improvement in robustness.

---

#  Testing Summary This Week

This week I:

* Tested CodeBERT manually more than 8 times.
* Ran LLM explanation on 20 samples.
* Scaled to 100 samples.
* Compared first and improved prompt versions.
* Verified no fake diffs.
* Confirmed full structured output compliance.

The second version of the prompt + fallback system shows major improvement in stability and reliability.

---

#  Key Lessons from Week 19

1. Dataset quality is more important than dataset size.
2. Deduplication is absolutely critical.
3. Synthetic data caused misleading overfitting.
4. CTSSB-1M provides more realistic bug diversity.
5. Prompt engineering directly impacts hallucination rate.
6. Ground-truth diff injection solves fake patch generation.
7. The pipeline is now stable enough for scaling.

---


#  Week 19 Summary

Week 19 was mainly about:

* Fixing dataset quality.
* Removing large-scale duplication.
* Improving CodeBERT training.
* Testing the model repeatedly.
* Successfully integrating Qwen LLM.
* Solving hallucination issues.
* Achieving 70% structured explanation compliance.

The system now feels significantly more stable and research-level compared to previous weeks.

---








---

# Week 20 Report

### Links : 
Here are the direct links to the references provided in the previous response so you can easily add them to your report:

1. Overfitting & Data Leakage

    Paper: Shortcut Learning in Deep Neural Networks (Geirhos et al., 2020) — (Often cited alongside their work on underspecification and leakage).

    Link: https://arxiv.org/abs/2004.07780

    Alternative (Highly specific to ML Software Engineering): Leakage and the Reproducibility Crisis in ML-based Science (Kapoor & Narayanan, 2023).

    Link: https://arxiv.org/abs/2207.07048

2. Hidden Class Imbalance & Sampling

    Paper: Software Vulnerability Detection Using Deep Neural Networks: A Survey (Lin et al., 2020).

    Link: https://arxiv.org/abs/2009.07235

3. CodeBERT vs. GraphCodeBERT

    Paper: GraphCodeBERT: Pre-training Code Representations with Data Flow (Guo et al., 2021).

    Link: https://arxiv.org/abs/2009.08366

4. Dataset Quality: PyVul

    Repository/Dataset: PyVul: A Large-scale Real-world Vulnerability Dataset (Quan et al.).

    Link: https://github.com/billquan/PyVul
## Overview

This week was extremely important for the integrity of the project.

The focus was not on pushing accuracy higher.
The focus was on detecting problems, understanding them properly, and fixing them scientifically.

Main focus areas:

* Comparing CodeBERT vs GraphCodeBERT
* Detecting and fixing overfitting
* Fixing dataset leakage
* Improving evaluation methodology
* Testing CTSSB vs PyVul
* Stabilizing the full training pipeline

This week strengthened the scientific reliability of my FYP.

---

# 1. Overfitting Problem (Critical Discovery)

After implementing the pair-input architecture and running multiple experiments on CTSSB, I noticed suspicious behaviour.

### Observations

* Training loss decreasing normally
* Validation improving early
* Later epochs unstable
* Some validation scores unusually high
* Test performance dropping compared to validation

This pattern indicated overfitting.

Instead of assuming, I analyzed the pipeline step by step to identify the exact causes.

---

# 2. Root Cause Analysis

## Cause 1 — Data Leakage (Major Issue)

Originally, I made a serious mistake.

Both training and validation datasets were loaded from the same CSV file:

```python
train_dataset = CodePairDataset("combined_ctssb_augmented_cleaned.csv")
val_dataset   = CodePairDataset("combined_ctssb_augmented_cleaned.csv")
```

This meant:

* The model saw validation samples during training
* Validation metrics were artificially inflated
* Test performance later dropped
* Evaluation was corrupted

This was not normal overfitting.
This was leakage.

### Fix Applied

I implemented proper dataset splitting:

* 70% Train
* 15% Validation
* 15% Test

The split is done before dataset loading and saved as separate CSV files.
There is now zero overlap between splits.

After applying this fix, metrics dropped — but they became honest.

This was the most important correction this week.

---

## Cause 2 — Hidden Class Imbalance

Before fixing negative sampling:

* All samples had label 0
* The model learned trivial classification
* Metrics looked stable but were meaningless

After implementing proper negative sampling:

* 50% positive samples
* 50% negative samples
* The model was forced to learn semantic differences

Once balanced, real overfitting behaviour became visible — which is actually good because it means the model is truly learning.

---

## Cause 3 — Learning Rate Too Aggressive

Initial learning rate:

```python
1e-5
```

This caused:

* Fast convergence
* Sharp updates
* Fitting noise
* Unstable validation behaviour

### Fix Applied

I reduced the learning rate:

```python
5e-6
```



This resulted in:

* Smoother convergence
* More stable gradients
* Reduced overfitting spikes
* Improved generalization

---

## Cause 4 — Threshold Over-Optimization

Previously, I optimized the classification threshold heavily on validation to maximize macro-F1.

This can cause subtle overfitting to the validation distribution.

### Fix Applied

Now I:

* Select threshold using validation
* Freeze the threshold
* Apply it directly to test

There is no test-time tuning anymore.

---

# 3. Repeated CodeBERT Testing (Stability Verification)

This week, I re-ran CodeBERT multiple times to verify stability and reproducibility.

I trained and evaluated CodeBERT more than **6 separate times** under the corrected pipeline:

* Proper train/val/test split
* Balanced negative sampling
* Lower learning rate
* Frozen threshold

Across runs, performance was consistent.

The final stable **macro-F1 score was approximately 62% on the test set**.

This confirms:

* Leakage is fully resolved
* Evaluation is stable
* Results are reproducible
* The 62% performance reflects real generalization

Although 62% is lower than earlier inflated validation numbers, it represents an honest and scientifically valid result.

This is far more valuable for the project.

---

# 4. Evidence Overfitting Was Reduced

### PyVul Results (After Fixes)

Validation:

* Macro-F1: 0.644
* AP: 0.691

Test:

* Macro-F1: 0.603
* AP: 0.664

Generalization gap:

* AP drop ≈ 0.027
* Macro-F1 drop ≈ 0.041

This is a healthy gap.

If overfitting still existed:

* Validation would be much higher than test
* Large performance collapse would occur

This is not happening now.

The system is stable.

---

# 5. CodeBERT vs GraphCodeBERT

## CodeBERT (V2)

* Buggy recall ≈ 0.98
* Very low clean recall
* Strong bias toward predicting buggy

This is structural overfitting.

The model learned dataset bias rather than true semantic bug detection.

---

## GraphCodeBERT (V3)

* Clean recall ≈ 0.61
* Buggy recall ≈ 0.55
* Balanced behaviour
* More stable threshold

GraphCodeBERT overfits less aggressively because:

* It models data-flow information
* It captures structural relations
* It has stronger semantic representations

This confirms representation quality directly impacts overfitting behaviour.

---

# 6. Threshold Sweep Analysis

I performed full threshold sweeps.

At low threshold:

* Buggy recall ≈ 1.0
* Clean recall ≈ 0.0

At high threshold:

* Opposite behaviour

Best threshold ≈ 0.52:

* Clean recall ≈ 0.50
* Buggy recall ≈ 0.53

Additionally:

* Many predictions cluster around 0.5
* High uncertainty on difficult samples

This indicates:

* The model is not memorizing
* It struggles on genuinely hard cases
* Overfitting is reduced

---

# 7. Dataset Quality Insight

Important observation:

### CTSSB

* ~821K pairs
* Large dataset
* Contains noise and trivial mutations

### PyVul

* 1,474 pairs
* Smaller
* Real vulnerability fixes
* Higher semantic signal

PyVul generalizes better.

Conclusion:

Overfitting is not only about model capacity.
Dataset quality plays a major role.

Cleaner data reduces memorization.

---

# 8. Current Stable Pipeline

After all fixes, the pipeline now includes:

* Proper 70/15/15 dataset split
* No leakage
* Balanced negative sampling
* Pair-input architecture
* Focal Loss
* Reduced learning rate
* Frozen threshold evaluation
* Full threshold sweep diagnostics
* Confusion matrix analysis
* Near-threshold uncertainty analysis

The system is now scientifically reliable.

---

# 9. Reflection

This week changed my perspective.

Getting 0.95 validation accuracy is easy.
Getting 0.62 honest macro-F1 is difficult.

But the honest result is what matters.

Fixing leakage and overfitting improved the integrity of the project much more than chasing higher numbers.

This week strengthened the foundation of my FYP significantly.

---


