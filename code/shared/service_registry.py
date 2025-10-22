#!/usr/bin/env python3
"""
Enterprise-Grade Service Registry
Centralized, environment-aware service URL management for PipeLineServices

Features:
- Zero hardcoded URLs/ports in application code
- Automatic environment detection (dev/staging/prod)
- Type-safe service discovery
- Clear error messages for misconfiguration
- Docker/Kubernetes ready

Usage:
    from service_registry import ServiceRegistry

    registry = ServiceRegistry()

    # Get service URLs
    chunking_url = registry.get_service_url('chunking')
    metadata_url = registry.get_service_url('metadata')

    # Get all ingestion service URLs
    ingestion_urls = registry.get_ingestion_services()

    # Get all retrieval service URLs
    retrieval_urls = registry.get_retrieval_services()
"""

import os
from typing import Dict, Optional
from enum import Enum


class ServiceType(Enum):
    """Service types for organized access"""
    # Ingestion Services
    CHUNKING = "chunking"
    METADATA = "metadata"
    EMBEDDINGS = "embeddings"
    STORAGE = "storage"
    LLM_GATEWAY = "llm_gateway"

    # Retrieval Services
    SEARCH = "search"
    RERANKING = "reranking"
    COMPRESSION = "compression"
    ANSWER_GENERATION = "answer_generation"
    INTENT = "intent"

    # Infrastructure
    MILVUS = "milvus"
    APISIX = "apisix"


class ServiceRegistry:
    """
    Centralized service URL registry with environment awareness

    Automatically detects environment from PIPELINE_ENV variable:
    - dev: Development (8070-8079 Ingestion, 8090-8099 Retrieval)
    - staging: Staging (8080-8089 Ingestion, 8100-8109 Retrieval)
    - prod: Production (8060-8069 Ingestion, 8110-8119 Retrieval)
    """

    def __init__(self, environment: Optional[str] = None):
        """
        Initialize service registry

        Args:
            environment: Override environment (dev/staging/prod)
                        If None, reads from PIPELINE_ENV variable
        """
        self.environment = environment or os.getenv("PIPELINE_ENV", "dev")

        if self.environment not in ["dev", "staging", "prod"]:
            raise ValueError(
                f"Invalid environment '{self.environment}'. "
                f"Must be 'dev', 'staging', or 'prod'. "
                f"Set PIPELINE_ENV environment variable."
            )

        # Service URL mapping (read from environment variables)
        self._service_urls: Dict[str, str] = {}
        self._load_service_urls()

    def _load_service_urls(self):
        """Load all service URLs from environment variables"""

        # Define expected environment variables for each service
        service_env_vars = {
            # Ingestion Services
            ServiceType.CHUNKING.value: "CHUNKING_SERVICE_URL",
            ServiceType.METADATA.value: "METADATA_SERVICE_URL",
            ServiceType.EMBEDDINGS.value: "EMBEDDINGS_SERVICE_URL",
            ServiceType.STORAGE.value: "STORAGE_SERVICE_URL",
            ServiceType.LLM_GATEWAY.value: self._get_llm_gateway_var(),

            # Retrieval Services
            ServiceType.SEARCH.value: "SEARCH_SERVICE_URL",
            ServiceType.RERANKING.value: "RERANK_SERVICE_URL",
            ServiceType.COMPRESSION.value: "COMPRESS_SERVICE_URL",
            ServiceType.ANSWER_GENERATION.value: "ANSWER_SERVICE_URL",
            ServiceType.INTENT.value: "INTENT_SERVICE_URL",

            # Infrastructure
            ServiceType.MILVUS.value: self._get_milvus_var(),
            ServiceType.APISIX.value: "APISIX_GATEWAY_URL",
        }

        # Load URLs from environment
        missing_services = []
        for service, env_var in service_env_vars.items():
            url = os.getenv(env_var)
            if url:
                self._service_urls[service] = url
            else:
                # Only required services should fail
                if service in [
                    ServiceType.CHUNKING.value,
                    ServiceType.METADATA.value,
                    ServiceType.EMBEDDINGS.value,
                    ServiceType.STORAGE.value,
                    ServiceType.LLM_GATEWAY.value
                ]:
                    missing_services.append(f"{service} ({env_var})")

        if missing_services:
            raise EnvironmentError(
                f"Missing required service URLs for environment '{self.environment}':\n" +
                "\n".join(f"  - {s}" for s in missing_services) +
                f"\n\nPlease check your .env.{self.environment} file."
            )

    def _get_llm_gateway_var(self) -> str:
        """Get the correct LLM Gateway environment variable name"""
        env_map = {
            "dev": "LLM_GATEWAY_URL_DEVELOPMENT",
            "staging": "LLM_GATEWAY_URL_STAGING",
            "prod": "LLM_GATEWAY_URL_PRODUCTION"
        }
        return env_map[self.environment]

    def _get_milvus_var(self) -> str:
        """Get the correct Milvus environment variable name"""
        # Milvus host and port are separate variables
        return f"MILVUS_HOST_{self.environment.upper()}"

    def get_service_url(
        self,
        service: str,
        endpoint: Optional[str] = None,
        required: bool = True
    ) -> Optional[str]:
        """
        Get URL for a specific service

        Args:
            service: Service name (e.g., 'chunking', 'metadata')
            endpoint: Optional endpoint path to append (e.g., '/v1/orchestrate')
            required: If True, raises error if service not configured

        Returns:
            Full service URL with endpoint, or None if not configured and not required

        Raises:
            KeyError: If service is required but not configured

        Example:
            >>> registry.get_service_url('chunking', '/v1/orchestrate')
            'http://localhost:8071/v1/orchestrate'
        """
        if service not in self._service_urls:
            if required:
                raise KeyError(
                    f"Service '{service}' not configured for environment '{self.environment}'. "
                    f"Available services: {list(self._service_urls.keys())}"
                )
            return None

        base_url = self._service_urls[service].rstrip('/')

        if endpoint:
            endpoint = endpoint if endpoint.startswith('/') else f'/{endpoint}'
            return f"{base_url}{endpoint}"

        return base_url

    def get_health_url(self, service: str) -> str:
        """
        Get health check URL for a service

        Args:
            service: Service name

        Returns:
            Health check URL (base_url + /health)

        Example:
            >>> registry.get_health_url('chunking')
            'http://localhost:8071/health'
        """
        base_url = self.get_service_url(service)

        # Remove any existing endpoint paths
        if '/v1/' in base_url:
            base_url = base_url.split('/v1/')[0]

        return f"{base_url}/health"

    def get_ingestion_services(self) -> Dict[str, str]:
        """
        Get all ingestion service URLs

        Returns:
            Dictionary mapping service name to base URL
        """
        ingestion_services = [
            ServiceType.CHUNKING.value,
            ServiceType.METADATA.value,
            ServiceType.EMBEDDINGS.value,
            ServiceType.STORAGE.value,
            ServiceType.LLM_GATEWAY.value
        ]

        return {
            service: self._service_urls[service]
            for service in ingestion_services
            if service in self._service_urls
        }

    def get_retrieval_services(self) -> Dict[str, str]:
        """
        Get all retrieval service URLs

        Returns:
            Dictionary mapping service name to base URL
        """
        retrieval_services = [
            ServiceType.SEARCH.value,
            ServiceType.RERANKING.value,
            ServiceType.COMPRESSION.value,
            ServiceType.ANSWER_GENERATION.value,
            ServiceType.INTENT.value
        ]

        return {
            service: self._service_urls[service]
            for service in retrieval_services
            if service in self._service_urls
        }

    def get_all_services(self) -> Dict[str, str]:
        """Get all configured service URLs"""
        return self._service_urls.copy()

    def print_summary(self):
        """Print configuration summary for debugging"""
        print("=" * 80)
        print(f"SERVICE REGISTRY - Environment: {self.environment.upper()}")
        print("=" * 80)

        print("\n📥 INGESTION SERVICES:")
        for service, url in self.get_ingestion_services().items():
            print(f"  {service:15} → {url}")

        print("\n📤 RETRIEVAL SERVICES:")
        for service, url in self.get_retrieval_services().items():
            print(f"  {service:15} → {url}")

        print("\n🔧 INFRASTRUCTURE:")
        for service in [ServiceType.MILVUS.value, ServiceType.APISIX.value]:
            if service in self._service_urls:
                print(f"  {service:15} → {self._service_urls[service]}")

        print("=" * 80)


# Singleton instance for easy import
_registry: Optional[ServiceRegistry] = None


def get_registry() -> ServiceRegistry:
    """
    Get singleton ServiceRegistry instance

    Returns:
        ServiceRegistry instance

    Example:
        >>> from service_registry import get_registry
        >>> registry = get_registry()
        >>> chunking_url = registry.get_service_url('chunking')
    """
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry


# Convenience functions for direct access
def get_service_url(service: str, endpoint: Optional[str] = None) -> str:
    """Convenience function to get service URL"""
    return get_registry().get_service_url(service, endpoint)


def get_health_url(service: str) -> str:
    """Convenience function to get health check URL"""
    return get_registry().get_health_url(service)


if __name__ == "__main__":
    # Test the registry
    print("Testing Service Registry\n")

    try:
        registry = ServiceRegistry()
        registry.print_summary()

        print("\n\nExample Usage:")
        print(f"Chunking URL: {registry.get_service_url('chunking', '/v1/orchestrate')}")
        print(f"Metadata Health: {registry.get_health_url('metadata')}")

    except Exception as e:
        print(f"ERROR: {e}")
        print("\nMake sure PIPELINE_ENV is set and .env file is loaded!")
