from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
import io
from sentence_transformers import SentenceTransformer
import numpy as np
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI()
api_router = APIRouter(prefix="/api")

POSTGRES_URL = os.environ.get('POSTGRES_URL')
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_db_connection():
    conn = psycopg2.connect(POSTGRES_URL)
    return conn

def init_database():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_tenders (
            id TEXT PRIMARY KEY,
            tender_id TEXT,
            title TEXT,
            description TEXT,
            organization TEXT,
            category TEXT,
            value NUMERIC,
            currency TEXT,
            published_date TEXT,
            deadline TEXT,
            location TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cleaned_tenders (
            id TEXT PRIMARY KEY,
            tender_id TEXT UNIQUE,
            title TEXT,
            description TEXT,
            organization TEXT,
            category TEXT,
            value NUMERIC,
            currency TEXT,
            published_date DATE,
            deadline DATE,
            location TEXT,
            status TEXT,
            embedding vector(384),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS data_quality_logs (
            id TEXT PRIMARY KEY,
            check_type TEXT,
            severity TEXT,
            message TEXT,
            details JSONB,
            record_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_health (
            id TEXT PRIMARY KEY,
            status TEXT,
            total_records INTEGER,
            clean_records INTEGER,
            quality_score NUMERIC,
            last_ingestion TIMESTAMP,
            errors JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

class TenderResponse(BaseModel):
    id: str
    tender_id: str
    title: str
    description: str
    organization: str
    category: str
    value: float
    currency: str
    published_date: str
    deadline: str
    location: str
    status: str

class DataQualityLog(BaseModel):
    check_type: str
    severity: str
    message: str
    details: Dict[str, Any]
    record_count: int

class PipelineHealth(BaseModel):
    status: str
    total_records: int
    clean_records: int
    quality_score: float
    last_ingestion: Optional[str]
    errors: Dict[str, Any]

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

@api_router.get("/")
async def root():
    return {"message": "Procurement Intelligence Pipeline API", "version": "1.0.0"}

@api_router.post("/ingest")
async def ingest_data(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        records_inserted = 0
        for _, row in df.iterrows():
            tender_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO raw_tenders (id, tender_id, title, description, organization, 
                                       category, value, currency, published_date, deadline, 
                                       location, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tender_id, row.get('tender_id', tender_id), row.get('title', ''),
                row.get('description', ''), row.get('organization', ''),
                row.get('category', ''), float(row.get('value', 0)),
                row.get('currency', 'USD'), row.get('published_date', ''),
                row.get('deadline', ''), row.get('location', ''),
                row.get('status', 'Open')
            ))
            records_inserted += 1
        
        conn.commit()
        cur.close()
        conn.close()
        
        cleaned_count = await clean_and_normalize()
        await run_data_quality_checks()
        await update_pipeline_health()
        
        return {
            "status": "success",
            "records_ingested": records_inserted,
            "records_cleaned": cleaned_count,
            "message": "Data ingested and processed successfully"
        }
    except Exception as e:
        logging.error(f"Ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def clean_and_normalize():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT * FROM raw_tenders")
    raw_records = cur.fetchall()
    
    cleaned_count = 0
    for record in raw_records:
        try:
            description = record['description'] or ''
            if len(description) > 10:
                embedding = model.encode(description)
                embedding_list = embedding.tolist()
            else:
                embedding_list = [0.0] * 384
            
            cur.execute("""
                INSERT INTO cleaned_tenders 
                (id, tender_id, title, description, organization, category, value, 
                 currency, published_date, deadline, location, status, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (tender_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    embedding = EXCLUDED.embedding
            """, (
                record['id'], record['tender_id'], record['title'],
                record['description'], record['organization'],
                record['category'], record['value'], record['currency'],
                record['published_date'] or None, record['deadline'] or None,
                record['location'], record['status'], embedding_list
            ))
            cleaned_count += 1
        except Exception as e:
            logging.error(f"Cleaning error for record {record['id']}: {str(e)}")
            continue
    
    conn.commit()
    cur.close()
    conn.close()
    return cleaned_count

async def run_data_quality_checks():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("DELETE FROM data_quality_logs")
    
    cur.execute("SELECT COUNT(*) as total FROM cleaned_tenders")
    total_count = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as null_count FROM cleaned_tenders WHERE description IS NULL OR description = ''")
    null_desc = cur.fetchone()['null_count']
    if null_desc > 0:
        cur.execute("""
            INSERT INTO data_quality_logs (id, check_type, severity, message, details, record_count)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (str(uuid.uuid4()), 'null_check', 'high', 'Missing descriptions detected',
              json.dumps({'null_count': null_desc, 'percentage': round((null_desc/total_count)*100, 2)}),
              null_desc))
    
    cur.execute("""
        SELECT tender_id, COUNT(*) as dup_count 
        FROM cleaned_tenders 
        GROUP BY tender_id 
        HAVING COUNT(*) > 1
    """)
    duplicates = cur.fetchall()
    if duplicates:
        cur.execute("""
            INSERT INTO data_quality_logs (id, check_type, severity, message, details, record_count)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (str(uuid.uuid4()), 'duplicate_check', 'medium', 'Duplicate tender IDs found',
              json.dumps({'duplicate_ids': [d['tender_id'] for d in duplicates]}),
              len(duplicates)))
    
    cur.execute("SELECT COUNT(*) as outliers FROM cleaned_tenders WHERE value > 1000000000")
    outliers = cur.fetchone()['outliers']
    if outliers > 0:
        cur.execute("""
            INSERT INTO data_quality_logs (id, check_type, severity, message, details, record_count)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (str(uuid.uuid4()), 'outlier_check', 'low', 'High value outliers detected',
              json.dumps({'outlier_count': outliers}), outliers))
    
    conn.commit()
    cur.close()
    conn.close()

async def update_pipeline_health():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT COUNT(*) as total FROM raw_tenders")
    total = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as clean FROM cleaned_tenders")
    clean = cur.fetchone()['clean']
    
    cur.execute("SELECT COUNT(*) as issues FROM data_quality_logs WHERE severity IN ('high', 'medium')")
    issues = cur.fetchone()['issues']
    
    quality_score = max(0, 100 - (issues * 10))
    
    cur.execute("DELETE FROM pipeline_health")
    cur.execute("""
        INSERT INTO pipeline_health (id, status, total_records, clean_records, quality_score, 
                                    last_ingestion, errors)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (str(uuid.uuid4()), 'healthy' if quality_score > 70 else 'warning',
          total, clean, quality_score, datetime.now(timezone.utc), json.dumps({'issue_count': issues})))
    
    conn.commit()
    cur.close()
    conn.close()

@api_router.get("/tenders", response_model=List[TenderResponse])
async def get_tenders(limit: int = 50):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(f"SELECT * FROM cleaned_tenders ORDER BY created_at DESC LIMIT {limit}")
    tenders = cur.fetchall()
    cur.close()
    conn.close()
    
    return [{
        "id": t['id'],
        "tender_id": t['tender_id'],
        "title": t['title'],
        "description": t['description'] or '',
        "organization": t['organization'],
        "category": t['category'],
        "value": float(t['value']),
        "currency": t['currency'],
        "published_date": str(t['published_date']) if t['published_date'] else '',
        "deadline": str(t['deadline']) if t['deadline'] else '',
        "location": t['location'],
        "status": t['status']
    } for t in tenders]

@api_router.post("/search")
async def semantic_search(request: SearchRequest):
    try:
        query_embedding = model.encode(request.query).tolist()
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, tender_id, title, description, organization, category, 
                   value, currency, location, status,
                   1 - (embedding <=> %s::vector) as similarity
            FROM cleaned_tenders
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding, query_embedding, request.limit))
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return {
            "query": request.query,
            "results": [{
                "id": r['id'],
                "tender_id": r['tender_id'],
                "title": r['title'],
                "description": r['description'] or '',
                "organization": r['organization'],
                "category": r['category'],
                "value": float(r['value']),
                "currency": r['currency'],
                "location": r['location'],
                "status": r['status'],
                "similarity": round(float(r['similarity']), 3)
            } for r in results]
        }
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/data-quality")
async def get_data_quality():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM data_quality_logs ORDER BY created_at DESC")
    logs = cur.fetchall()
    cur.close()
    conn.close()
    
    return {
        "total_checks": len(logs),
        "logs": [{
            "check_type": log['check_type'],
            "severity": log['severity'],
            "message": log['message'],
            "details": log['details'],
            "record_count": log['record_count'],
            "created_at": log['created_at'].isoformat()
        } for log in logs]
    }

@api_router.get("/pipeline-health")
async def get_pipeline_health():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM pipeline_health ORDER BY created_at DESC LIMIT 1")
    health = cur.fetchone()
    cur.close()
    conn.close()
    
    if not health:
        return {
            "status": "not_initialized",
            "total_records": 0,
            "clean_records": 0,
            "quality_score": 0,
            "last_ingestion": None,
            "errors": {}
        }
    
    return {
        "status": health['status'],
        "total_records": health['total_records'],
        "clean_records": health['clean_records'],
        "quality_score": float(health['quality_score']),
        "last_ingestion": health['last_ingestion'].isoformat() if health['last_ingestion'] else None,
        "errors": health['errors']
    }

@api_router.post("/validate")
async def trigger_validation():
    try:
        await run_data_quality_checks()
        await update_pipeline_health()
        return {"status": "success", "message": "Validation completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    init_database()
    logger.info("Database initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")