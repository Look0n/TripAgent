import json
from .common import ask
def plan_workflow(user_request, context):
    result = ask('planner', json.dumps({'request':user_request,'context':context},ensure_ascii=False), 280)
    return {'status':'success','agent':'planner_agent','plan':result}
