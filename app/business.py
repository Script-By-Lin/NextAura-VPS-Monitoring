from telemetry import (
    BUSINESS_ACTIVE_USERS_GAUGE,
    BUSINESS_USER_REGISTRATIONS_TOTAL,
    BUSINESS_LOGIN_ATTEMPTS_TOTAL,
    BUSINESS_API_TOKEN_REQUESTS_TOTAL,
    BUSINESS_FEATURE_USAGE_TOTAL,
    BUSINESS_REVENUE_AMOUNT_TOTAL,
    BUSINESS_RATE_LIMIT_HITS_TOTAL,
    BUSINESS_SUSPICIOUS_REQUESTS_TOTAL,
)
from logger import logger

def record_user_registration(channel: str = "organic", plan: str = "free"):
    """Records a new user registration event."""
    BUSINESS_USER_REGISTRATIONS_TOTAL.labels(channel=channel).inc()
    BUSINESS_ACTIVE_USERS_GAUGE.labels(plan=plan).inc()
    logger.info(
        f"New user registered via {channel} with plan {plan}",
        extra={"extra_data": {"event": "user_registration", "channel": channel, "plan": plan}},
    )


def record_login_attempt(success: bool, reason: str = "none", client_ip: str = "127.0.0.1", user: str = "unknown"):
    """Records login attempt (success or failure) and logs in Fail2ban-compatible format."""
    status = "success" if success else "failure"
    BUSINESS_LOGIN_ATTEMPTS_TOTAL.labels(status=status, reason=reason).inc()

    if success:
        logger.info(
            f"Successful login for user '{user}'",
            extra={"extra_data": {"event": "login_success", "user": user, "client_ip": client_ip}},
        )
    else:
        # Logs as WARN with client_ip for Fail2ban jail regex matching
        logger.warning(
            f"Failed login attempt for user '{user}' (Reason: {reason})",
            extra={"extra_data": {"event": "login_failed", "user": user, "client_ip": client_ip, "reason": reason}},
        )


def record_transaction(amount: float, currency: str = "USD", plan: str = "pro"):
    """Records a revenue transaction event."""
    BUSINESS_REVENUE_AMOUNT_TOTAL.labels(currency=currency).inc(amount)
    logger.info(
        f"Processed payment of {amount} {currency} for {plan} plan",
        extra={"extra_data": {"event": "revenue_transaction", "amount": amount, "currency": currency, "plan": plan}},
    )


def record_feature_usage(feature: str, tier: str = "pro"):
    """Records feature usage."""
    BUSINESS_FEATURE_USAGE_TOTAL.labels(feature=feature, tier=tier).inc()


def record_api_token_usage(client_id: str, tier: str = "standard"):
    """Records token consumption per client."""
    BUSINESS_API_TOKEN_REQUESTS_TOTAL.labels(client_id=client_id, tier=tier).inc()


def record_rate_limit_hit(endpoint: str, client_ip: str):
    """Records rate limiting event."""
    BUSINESS_RATE_LIMIT_HITS_TOTAL.labels(endpoint=endpoint, client_ip=client_ip).inc()
    logger.warning(
        f"Rate limit triggered on endpoint {endpoint} by IP {client_ip}",
        extra={"extra_data": {"event": "rate_limit_exceeded", "endpoint": endpoint, "client_ip": client_ip}},
    )


def record_suspicious_threat(threat_type: str, source_ip: str, endpoint: str):
    """Records suspicious threat/probe detection."""
    BUSINESS_SUSPICIOUS_REQUESTS_TOTAL.labels(threat_type=threat_type, source_ip=source_ip).inc()
    logger.warning(
        f"Security threat detected: {threat_type} on {endpoint} from {source_ip}",
        extra={"extra_data": {"event": "security_threat", "threat_type": threat_type, "source_ip": source_ip, "endpoint": endpoint}},
    )
