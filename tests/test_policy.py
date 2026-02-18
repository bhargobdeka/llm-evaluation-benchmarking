from llm_eval.config import BudgetPolicy, ReliabilityPolicy, RunConfig, RuntimePolicy, SecurityPolicy
from llm_eval.policy import merge_policy


def test_merge_policy_overrides_from_policy_yaml() -> None:
    config = RunConfig(
        run_name="test",
        providers=[],
        policy=RuntimePolicy(
            budget=BudgetPolicy(max_usd_per_run=99.0, warn_at_percent=50, enforce_hard_stop=False),
            reliability=ReliabilityPolicy(
                max_parallel_requests=10,
                request_timeout_seconds=120,
                provider_error_rate_hard_stop_percent=30,
            ),
            security=SecurityPolicy(byok_only=False, persist_user_api_keys=True),
        ),
    )
    merged = merge_policy(config, policy_path="configs/policy.yaml")
    assert merged.budget.max_usd_per_run == 5.0
    assert merged.reliability.max_parallel_requests == 3
    assert merged.reliability.provider_error_rate_hard_stop_percent == 10
    assert merged.security.byok_only is True
