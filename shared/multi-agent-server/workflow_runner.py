import argparse
import json
import time
from coordinator import run_workflow,get_workflow,FEATURES

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--feature',choices=sorted(FEATURES),default='account')
    p.add_argument('--request',default='Review the supplied travel preferences and suggest improvements.')
    p.add_argument('--context',default='{}',help='JSON object of evidence supplied by the caller')
    args=p.parse_args()
    result=run_workflow(args.request,args.feature,json.loads(args.context))
    workflow_id=result['workflow_id']
    while result['status'] in ('queued','running'):
        time.sleep(1)
        result=get_workflow(workflow_id,args.feature)
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
