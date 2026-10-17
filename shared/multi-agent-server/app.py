import os
import hmac
from flask import Flask, jsonify, request
from coordinator import FEATURES,run_workflow,get_workflow,review_workflow,workflow_status,workflow_history
app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=25000

@app.before_request
def authenticate():
    if request.path in ('/','/health'):return None
    secret=os.getenv('MULTI_AGENT_API_KEY','')
    if secret and not hmac.compare_digest(request.headers.get('X-Multi-Agent-Key',''),secret):
        return jsonify({'status':'error','error':'Unauthorized'}),401

def feature_arg(data):
    f=data.get('feature','')
    if f not in FEATURES:raise ValueError('feature must be one of: '+', '.join(sorted(FEATURES)))
    return f

@app.get('/')
@app.get('/health')
def health():return jsonify({'service':'multi-agent-server','status':'running','features':sorted(FEATURES)})

@app.post('/workflow')
def workflow():
    data=request.get_json(silent=True) or {}
    try:
        f=feature_arg(data)
        result=run_workflow(data.get('user_request',''),f,data.get('context',{}))
        return jsonify(result),202
    except (ValueError,TypeError) as exc:return jsonify({'status':'error','error':str(exc)}),400

@app.get('/workflow/<workflow_id>')
def get_one(workflow_id):
    f=request.args.get('feature','')
    if f not in FEATURES:return jsonify({'error':'Valid feature required'}),400
    result=get_workflow(workflow_id,f)
    return (jsonify(result),200) if result else (jsonify({'error':'Not found'}),404)

@app.post('/workflow/<workflow_id>/review')
def review_one(workflow_id):
    data=request.get_json(silent=True) or {}
    try:
        f=feature_arg(data)
        result,error=review_workflow(workflow_id,f,data.get('decision'),data.get('correction',''))
        if error:return jsonify({'error':error}),404 if error=='not_found' else 409
        return jsonify(result),200
    except (ValueError,TypeError) as exc:return jsonify({'error':str(exc)}),400

@app.get('/workflow/status')
def status():
    f=request.args.get('feature')
    if f and f not in FEATURES:return jsonify({'error':'Invalid feature'}),400
    return jsonify(workflow_status(f))

@app.get('/workflow/history')
def history():
    f=request.args.get('feature','')
    if f not in FEATURES:return jsonify({'error':'Valid feature required'}),400
    return jsonify({'status':'success','workflows':workflow_history(f)})

if __name__=='__main__':
    app.run(host=os.getenv('MULTI_AGENT_HOST','0.0.0.0'),port=int(os.getenv('PORT','7003')),debug=False)
