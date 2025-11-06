## **Week 1 : Choosing my prject**

Before I met my supervisor, I spent some time thinking about what would help me after I graduate and finish university. I asked myself what things I like and what things I don’t. After a while, I realized that I really enjoy AI and that I’m good at it, so I decided I want to do something in that field.

I started thinking about what kind of project could help a student develop their programming skills faster and in a more efficient way. Then I came up with the idea of an automated code review tool — something that helps students see where they are weak and shows them how to improve.

When I met my supervisor, we discussed the idea, and he suggested making it more interactive — for example, allowing students to learn and get feedback while they are writing the code itself. He also mentioned that I could improve it even more by adding a feature that helps make the code more efficient — for instance, if the code takes 4 or 5 lines, the system could suggest a shorter or more optimized version.

---


# Week 2 Meeting My Supervisor and Deciding What to Choose

# AI Code Review (IBM Reference)

AI code review is a tool that uses AI techniques to assist in reviewing code for quality, style, and functionality.

Before starting, it's important to note that machine learning (ML) models are used to identify problems and small bugs in code, as well as detect security issues and vulnerabilities.

AI code review tools often provide suggestions — or even automated fixes — helping developers save time and improve code quality.

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
Large Language Models (LLMs) — such as GPT-4 — are increasingly being used to provide context-aware feedback and suggestions.

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
- Planned an initial workflow for the project (data → model → tool → evaluation).  

---

### Summary
This week helped me get a clearer idea of how to start implementing the project and what areas I need to focus on next.




## **Week 4: PromptLayer (Revolutionizing Code Reviews with AI-Powered Automation)**

**Link:** [https://www.promptlayer.com/research-papers/revolutionizing-code-reviews-with-ai-powered-automation](https://www.promptlayer.com/research-papers/revolutionizing-code-reviews-with-ai-powered-automation)

This week I read a new paper called **“Code Review Automation via Multi-task Federated LLM – An Empirical Study”** by *Jahnavi Kumar* and *Sridhar Chimalakonda*. It talks about how **AI** and **federated learning** can help automate the code review process.

The idea is that normal code reviews take a lot of time, so they used a **large language model** that can handle multiple things at once — like checking if a code change needs a review, writing comments, and even suggesting how to improve the code.

The researchers from **IIT Tirupati** propose using a **multi-task federated LLM**, meaning:

* **Federated learning** lets multiple organizations collaboratively train a shared model *without sharing their private code.*
* The model is trained for **three tasks at once:**

  1. Predict whether a code change needs review
  2. Generate comments explaining issues or suggestions
  3. Propose refined code

They tested two different multi-task training strategies:

* **Sequential Training** – trained tasks one after another, but the model forgot older tasks
* **Cumulative Training** – trained all tasks together, which worked better

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

### 2) **The Current Landscape of LLM-Based Code Review Tools**

The article discusses three main AI-powered tools currently in use:

* **GitHub Copilot**
* **DeepCode**
* **AI21 Labs Code Review**

These tools help with syntax and bug detection but are **not fully intelligent reviewers**.

---

### 3) **code2Prompt — The New Solution**

**code2Prompt** is presented as an **advanced LLM-based reviewer** that overcomes many traditional limitations by using **semantic and contextual understanding** of the code.

#### **How it works:**

1. **Code Chunking**

   * The code is divided into smaller logical blocks (chunks).
   * This reduces overload and helps the AI focus on one piece at a time.
   * Uses graph-based algorithms to find dependencies between functions and modules.

2. **Contextualization**

   * After chunking, the model analyzes how each code piece fits into the entire project.
   * It uses **dependency, control flow, and data flow analysis** to understand relationships.
   * This leads to **more accurate and relevant feedback.**

3. **Prioritized Review**

   * Not all code is equally risky — so code2Prompt ranks chunks by importance.
   * It looks at:

     * Code complexity
     * Type of change
     * Potential issues or style violations
   * High-risk areas (like security-critical code) are reviewed first.

4. **Code Quality Assessment**

   * Goes beyond bug detection — it evaluates:

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

This article directly connects to my project idea — building an **AI code reviewer** that gives **smart and contextual feedback.**
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
The article explains how traditional code reviews are very important for software quality, but they are also **slow and time-consuming.** Static tools like linters can catch syntax or style errors, but they can’t give **deep, contextual feedback** like a senior engineer would.
This is where **AI-powered code review** comes in — using **Large Language Models (LLMs)** to create **custom linting rules** that go far beyond what normal static tools can do.

---

### 1) **What is AI-Powered Code Review?**

AI-powered code review uses **LLMs** to analyze code changes and give feedback based on **custom natural language rules.**
The AI reviewer acts like an **editor**, suggesting improvements to structure, clarity, and style — but following your team’s unique best practices and architecture, not just generic rules.

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
It gives me a **clear workflow** — how to integrate the model into the pipeline, define my own review rules, and mix AI with existing linting tools.
This is exactly what I need to begin implementing my project step-by-step.

---
