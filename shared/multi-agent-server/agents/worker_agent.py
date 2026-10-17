import json
from .common import ask
def generate_output(user_request, plan, context):
    result = ask('worker', json.dumps({'request':user_request,'plan':plan['plan'],'context':context},ensure_ascii=False), 1400)
    return {'status':'success','agent':'worker_agent','output':result,'evidence':context.get('evidence',[])}
