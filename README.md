# Procure Insights – AI-Driven Procurement Intelligence Platform

🔗 **Live Demo:** https://procure-insights-1.preview.emergentagent.com/  
📦 **Tech Stack:** Python, FastAPI/Django, PostgreSQL, pgvector, Pandas, Sentence Transformers, React, Docker

---

## 📌 Project Overview
Procure Insights is an end-to-end **AI data pipeline** designed to transform raw procurement data into structured, searchable, and analytics-ready insights.  
This project demonstrates real-world **data engineering**, **vector search**, and **ML workflow integration**, similar to production systems used in modern AI startups.

---

## 🧠 Key Features
### ✅ **1. Automated Data Ingestion**
- Reads tender/procurement data from CSV/API  
- Stores raw data into a PostgreSQL staging table  

### ✅ **2. Data Cleaning & Normalization**
- Standardizes inconsistent fields  
- Cleans missing / invalid values  
- Ensures schema integrity  

### ✅ **3. Data Quality Checks**
- Detects duplicates  
- Computes null ratios  
- Schema validation  
- Drift detection  
- Logs quality scores  

### ✅ **4. AI Embedding & Semantic Search**
- Generates embeddings using **Sentence Transformers**  
- Stores vectors in `pgvector`  
- Enables **semantic similarity search** (find similar tenders)  

### ✅ **5. Backend API**
- `/search` → Vector similarity search  
- `/tenders` → View cleaned data  
- `/dq-score` → Data quality insights  
- `/health` → Pipeline status  

### ✅ **6. Minimal Frontend UI**
- Search bar  
- Tender listing  
- Quality metrics display  

---

## 🛠 Tech Stack Breakdown
| Component | Technology |
|----------|------------|
| Backend | Python, FastAPI / Django |
| ML Layer | Sentence Transformers (MiniLM-L6-v2) |
| Vector Database | PostgreSQL + pgvector |
| Data Engineering | Pandas, ETL scripts |
| Workflow | Linux cron / Python schedulers |
| Frontend | React |
| Deployment | Docker, Emergent Agent |

---

## 📂 Folder Structure

