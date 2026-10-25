from collectors.multi_agent_collector import collect_multi_agent_context
from config.review_config import MULTI_AGENT_PROMPTS
from pipelines.evidence_pipeline import run_evidence_pipeline


def run_multi_agent_pipeline(service_config, feature, workflow_id, database=None, checks_only=False):
    return run_evidence_pipeline(service_config, feature, "multi-agent", lambda: collect_multi_agent_context(feature, workflow_id, database), MULTI_AGENT_PROMPTS, checks_only)
