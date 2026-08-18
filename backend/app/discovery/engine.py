import logging
from typing import List, Optional
from app.discovery.base import DiscoveryProvider, DiscoveryResult


logger = logging.getLogger(__name__)


class CompositeDiscoveryEngine:

    def __init__(self):
        self._providers: List[DiscoveryProvider] = []

    def register_provider(self, provider: DiscoveryProvider):
        self._providers.append(provider)
        logger.info("Registered discovery provider: %s (available=%s)",
                     provider.name, provider.is_available())

    def get_available_providers(self) -> List[DiscoveryProvider]:
        return [p for p in self._providers if p.is_available()]

    def discover_host(self, target: str, providers: List[str] = None, **kwargs) -> List[DiscoveryResult]:
        results = []
        active_providers = self._get_providers(providers)

        for provider in active_providers:
            try:
                result = provider.discover_host(target, **kwargs)
                if result:
                    result.raw_data["provider"] = provider.name
                    results.append(result)
                    logger.info("Provider %s found host %s", provider.name, target)
            except Exception as e:
                logger.error("Provider %s failed for host %s: %s",
                             provider.name, target, str(e))

        return results

    def discover_network(self, network_range: str, providers: List[str] = None, **kwargs) -> List[DiscoveryResult]:
        results = []
        active_providers = self._get_providers(providers)

        for provider in active_providers:
            try:
                provider_results = provider.discover_network(network_range, **kwargs)
                for result in provider_results:
                    result.raw_data["provider"] = provider.name
                results.extend(provider_results)
                logger.info("Provider %s found %d hosts in %s",
                             provider.name, len(provider_results), network_range)
            except Exception as e:
                logger.error("Provider %s failed for network %s: %s",
                             provider.name, network_range, str(e))

        return results

    def _get_providers(self, provider_names: List[str] = None) -> List[DiscoveryProvider]:
        available = self.get_available_providers()
        if provider_names:
            return [p for p in available if p.name in provider_names]
        return available
