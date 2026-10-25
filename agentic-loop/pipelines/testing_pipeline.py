from collectors.testing_collector import collect_testing_context
from config.review_config import TESTING_PROMPTS
from pipelines.evidence_pipeline import run_evidence_pipeline


def run_testing_pipeline(service_config, feature, manifest_path, expected_commit=None, checks_only=False):
    return run_evidence_pipeline(service_config, feature, "testing", lambda: collect_testing_context(feature, service_config, manifest_path, expected_commit), TESTING_PROMPTS, checks_only)
