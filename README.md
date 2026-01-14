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

