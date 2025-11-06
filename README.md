Week 1 : Choosing my prject 

Before I met my supervisor, I spent some time thinking about what would help me after I graduate and finish university. I asked myself what things I like and what things I don’t. After a while, I realized that I really enjoy AI and that I’m good at it, so I decided I want to do something in that field.

I started thinking about what kind of project could help a student develop their programming skills faster and in a more efficient way. Then I came up with the idea of an automated code review tool — something that helps students see where they are weak and shows them how to improve.

When I met my supervisor, we discussed the idea, and he suggested making it more interactive — for example, allowing students to learn and get feedback while they are writing the code itself. He also mentioned that I could improve it even more by adding a feature that helps make the code more efficient — for instance, if the code takes 4 or 5 lines, the system could suggest a shorter or more optimized version.


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
