import json
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from agents.planner_agent import plan_workflow
from agents.worker_agent import generate_output
from agents.reviewer_agent import review_output

FEATURES = {'account','accommodation','attractions','checklist','flight'}
ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv('MULTI_AGENT_DB_PATH',str(ROOT/'workflow_state.sqlite3')))
LOCK = threading.RLock()
EXECUTOR = ThreadPoolExecutor(max_workers=int(os.getenv('MAX_WORKFLOWS','4')))
TIMEOUT = float(os.getenv('AGENT_STEP_TIMEOUT_SECONDS','75'))

def now(): return datetime.now(timezone.utc).isoformat()
def connect():
    conn=sqlite3.connect(DB_PATH,timeout=10)
    conn.row_factory=sqlite3.Row
    return conn

def init_db():
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    with connect() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS workflows (id TEXT PRIMARY KEY, feature TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT, workflow_id TEXT NOT NULL, event TEXT NOT NULL, timestamp TEXT NOT NULL, detail TEXT NOT NULL)')

def record(workflow_id,feature,status,payload,event,detail=None):
    with LOCK,connect() as conn:
        t=now()
        conn.execute('INSERT INTO workflows VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,payload=excluded.payload,updated_at=excluded.updated_at',(workflow_id,feature,status,json.dumps(payload,ensure_ascii=False),t,t))
        conn.execute('INSERT INTO audit (workflow_id,event,timestamp,detail) VALUES (?,?,?,?)',(workflow_id,event,t,json.dumps(detail or {},ensure_ascii=False)))

def get_workflow(workflow_id,feature=None):
    with connect() as conn:
        row=conn.execute('SELECT * FROM workflows WHERE id=?',(workflow_id,)).fetchone()
    if row is None or (feature and row['feature']!=feature):return None
    return json.loads(row['payload'])

def step(func,*args):
    # Calls execute inside the workflow's worker thread; no orphaned nested futures.
    start=time.monotonic()
    result=func(*args)
    if time.monotonic()-start>TIMEOUT:
        raise TimeoutError('Agent step exceeded configured duration')
    return result

def execute(workflow_id,user_request,feature,context):
    start=time.monotonic()
    payload=get_workflow(workflow_id)
    try:
        plan=step(plan_workflow,user_request,context)
        payload['planner_result']=plan
        payload['status']='running'
        record(workflow_id,feature,'running',payload,'planner_completed')
        worker=step(generate_output,user_request,plan,context)
        payload['worker_result']=worker
        record(workflow_id,feature,'running',payload,'worker_completed')
        review=step(review_output,user_request,plan,worker,context)
        payload['reviewer_result']=review
        payload['status']='pending_review'
        payload['duration_ms']=int((time.monotonic()-start)*1000)
        record(workflow_id,feature,'pending_review',payload,'awaiting_human_review')
    except Exception as exc:
        payload['status']='failed'
        payload['error']=f'{type(exc).__name__}: {exc}'[:500]
        payload['duration_ms']=int((time.monotonic()-start)*1000)
        record(workflow_id,feature,'failed',payload,'workflow_failed',{'error_type':type(exc).__name__})

def run_workflow(user_request,feature='account',context=None):
    if feature not in FEATURES:raise ValueError('Unsupported feature')
    if not isinstance(user_request,str) or not user_request.strip() or len(user_request)>4000:raise ValueError('user_request must be 1-4000 characters')
    if context is None:context={}
    if not isinstance(context,dict) or len(json.dumps(context))>20000:raise ValueError('context must be an object under 20 KB')
    context=dict(context,feature=feature)
    workflow_id=str(uuid.uuid4())
    payload={'workflow_id':workflow_id,'feature':feature,'user_request':user_request,'status':'queued','created_at':now(),'planner_result':None,'worker_result':None,'reviewer_result':None,'human_decision':{'required':True,'status':'pending','allowed_values':['Accept','Partially Accept','Reject']}}
    record(workflow_id,feature,'queued',payload,'workflow_created')
    EXECUTOR.submit(execute,workflow_id,user_request,feature,context)
    return payload

def review_workflow(workflow_id,feature,decision,correction=''):
    if decision not in ('Accept','Partially Accept','Reject'):raise ValueError('Invalid decision')
    if not isinstance(correction,str) or len(correction)>4000:raise ValueError('Invalid correction')
    if decision=='Partially Accept' and not correction.strip():raise ValueError('Correction is required for partial acceptance')
    with LOCK:
        payload=get_workflow(workflow_id,feature)
        if payload is None:return None,'not_found'
        if payload['status']!='pending_review':return payload,'conflict'
        payload['human_decision']={'required':True,'status':'completed','decision':decision,'correction':correction,'timestamp':now()}
        payload['status']='rejected' if decision=='Reject' else 'completed'
        # Approval records a decision; feature backend must explicitly apply any approved changes.
        record(workflow_id,feature,payload['status'],payload,'human_review_recorded',{'decision':decision})
        return payload,None

def workflow_status(feature=None):
    with connect() as conn:
        if feature:
            rows=conn.execute('SELECT status,COUNT(*) AS n FROM workflows WHERE feature=? GROUP BY status',(feature,)).fetchall()
        else:
            rows=conn.execute('SELECT status,COUNT(*) AS n FROM workflows GROUP BY status').fetchall()
    return {'status':'success','feature':feature,'counts':{r['status']:r['n'] for r in rows}}

def workflow_history(feature,limit=20):
    with connect() as conn:
        rows=conn.execute('SELECT id,feature,status,created_at,updated_at FROM workflows WHERE feature=? ORDER BY created_at DESC LIMIT ?',(feature,limit)).fetchall()
    return [dict(r) for r in rows]
init_db()
