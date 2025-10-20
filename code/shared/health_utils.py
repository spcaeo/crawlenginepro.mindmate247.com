"""
Shared Health Check Utilities
Standardized health check helpers for all PipeLineServices

Usage:
    from shared.health_utils import check_service_health, HealthCheckConfig

    result = await check_service_health(
        http_client=http_client,
        service_url="http://localhost:8062/health",
        config=HealthCheckConfig(timeout=2.0)
    )
"""

import httpx
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class HealthCheckConfig:
    """Configuration for health checks"""
    timeout: float = 2.0  # Standard timeout: 2 seconds
    include_version: bool = True
    include_response_time: bool = True


async def check_service_health(
    http_client: httpx.AsyncClient,
    service_url: str,
    config: Optional[HealthCheckConfig] = None
) -> Dict[str, Any]:
    """
    Standardized health check for a service endpoint

    Args:
        http_client: Async HTTP client (with connection pooling)
        service_url: Full URL to service health endpoint
        config: Health check configuration

    Returns:
        dict: {
            "status": "healthy"|"timeout"|"unreachable"|"unhealthy",
            "version": "1.0.0",  # if available
            "response_time_ms": 123.45,
            "error": "error message"  # if failed
        }
    """
    if config is None:
        config = HealthCheckConfig()

    start_time = time.time()

    try:
        response = await http_client.get(service_url, timeout=config.timeout)
        response_time = (time.time() - start_time) * 1000

        if response.status_code == 200:
            data = response.json()
            result = {
                "status": data.get("status", "healthy"),
            }

            if config.include_version:
                result["version"] = data.get("version", "unknown")

            if config.include_response_time:
                result["response_time_ms"] = round(response_time, 2)

            return result
        else:
            return {
                "status": "unhealthy",
                "error": f"HTTP {response.status_code}",
                "response_time_ms": round(response_time, 2) if config.include_response_time else None
            }

    except httpx.TimeoutException:
        return {
            "status": "timeout",
            "error": f"Health check timeout ({config.timeout}s)",
            "response_time_ms": config.timeout * 1000 if config.include_response_time else None
        }
    except httpx.ConnectError as e:
        return {
            "status": "unreachable",
            "error": f"Connection failed: {str(e)[:100]}",
            "response_time_ms": None
        }
    except Exception as e:
        return {
            "status": "unreachable",
            "error": str(e)[:200],
            "response_time_ms": None
        }


async def check_multiple_services(
    http_client: httpx.AsyncClient,
    services: Dict[str, str],
    config: Optional[HealthCheckConfig] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Check multiple services in parallel

    Args:
        http_client: Async HTTP client
        services: Dict mapping service names to health URLs
        config: Health check configuration

    Returns:
        dict: Mapping service names to health results

    Example:
        services = {
            "chunking": "http://localhost:8061/health",
            "metadata": "http://localhost:8062/health"
        }
        results = await check_multiple_services(http_client, services)
    """
    import asyncio

    tasks = {
        name: check_service_health(http_client, url, config)
        for name, url in services.items()
    }

    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    return {
        name: result if not isinstance(result, Exception) else {
            "status": "error",
            "error": str(result)
        }
        for (name, _), result in zip(services.items(), results)
    }


def aggregate_health_status(service_results: Dict[str, Dict[str, Any]]) -> str:
    """
    Aggregate health status from multiple services

    Args:
        service_results: Results from check_multiple_services

    Returns:
        str: "healthy"|"degraded"|"unhealthy"

    Logic:
        - "healthy": All services healthy
        - "degraded": Some services down, but system functional
        - "unhealthy": Critical services down
    """
    if not service_results:
        return "unknown"

    statuses = [result.get("status", "unknown") for result in service_results.values()]

    # Count healthy services
    healthy_count = sum(1 for status in statuses if status in ["healthy", "ok"])
    total_count = len(statuses)

    if healthy_count == total_count:
        return "healthy"
    elif healthy_count > 0:
        return "degraded"
    else:
        return "unhealthy"


def create_health_summary(service_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a standardized health summary

    Args:
        service_results: Results from check_multiple_services

    Returns:
        dict: {
            "total_services": 5,
            "healthy": 4,
            "unhealthy": 1,
            "status_breakdown": {
                "healthy": 4,
                "timeout": 1
            }
        }
    """
    statuses = [result.get("status", "unknown") for result in service_results.values()]

    healthy_count = sum(1 for status in statuses if status in ["healthy", "ok"])
    total_count = len(statuses)

    # Count by status type
    status_breakdown = {}
    for status in statuses:
        status_breakdown[status] = status_breakdown.get(status, 0) + 1

    return {
        "total_services": total_count,
        "healthy": healthy_count,
        "unhealthy": total_count - healthy_count,
        "status_breakdown": status_breakdown
    }


async def test_api_connectivity(
    http_client: httpx.AsyncClient,
    api_url: str,
    api_key: Optional[str] = None,
    timeout: float = 2.0
) -> bool:
    """
    Test if an external API is reachable

    Args:
        http_client: Async HTTP client
        api_url: API endpoint to test
        api_key: Optional API key for authentication
        timeout: Request timeout in seconds

    Returns:
        bool: True if API is reachable and responds with 2xx

    Example:
        # Test Nebius API
        connected = await test_api_connectivity(
            http_client,
            "https://api.studio.nebius.ai/v1/models",
            api_key=NEBIUS_API_KEY
        )
    """
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        response = await http_client.get(
            api_url,
            headers=headers,
            timeout=timeout
        )

        return response.status_code in range(200, 300)

    except Exception:
        return False


def add_cache_stats_to_health(
    health_response: Dict[str, Any],
    cache_stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add cache statistics to a health response

    Args:
        health_response: Existing health response dict
        cache_stats: Cache statistics from cache.stats()

    Returns:
        dict: Updated health response with cache info

    Example:
        health = {
            "status": "healthy",
            "version": "1.0.0"
        }
        cache_stats = cache.stats()
        health = add_cache_stats_to_health(health, cache_stats)
    """
    health_response["cache"] = {
        "enabled": cache_stats.get("enabled", False),
        "entries": cache_stats.get("entries", 0),
        "max_size": cache_stats.get("max_size", 0),
        "hit_rate": cache_stats.get("hit_rate", 0.0),
        "total_hits": cache_stats.get("total_hits", 0),
        "total_misses": cache_stats.get("total_misses", 0)
    }
    return health_response


# Standard timeout for all health checks (2 seconds)
STANDARD_HEALTH_TIMEOUT = 2.0

# Standard health check configuration
STANDARD_CONFIG = HealthCheckConfig(
    timeout=STANDARD_HEALTH_TIMEOUT,
    include_version=True,
    include_response_time=True
)
