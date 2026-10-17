import json
from .common import ask
def review_output(user_request, plan, worker, context):
    result = ask('reviewer',json.dumps({'request':user_request,'plan':plan['plan'],'worker_output':worker['output'],'context':context},ensure_ascii=False),350)
    return {'status':'success','agent':'reviewer_agent','review':result}
