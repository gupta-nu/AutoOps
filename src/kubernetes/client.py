"""
Kubernetes Client - Interface for Kubernetes cluster operations
"""

import asyncio
import yaml
from typing import Any, Dict, List, Optional
from datetime import datetime

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from opentelemetry import trace

from ..monitoring.tracing import get_tracer
from config.settings import settings

tracer = get_tracer(__name__)


class KubernetesClient:
    """
    Kubernetes client wrapper for AutoOps operations
    """
    
    def __init__(self):
        self._load_config()
        self._initialize_clients()
    
    def _load_config(self):
        """Load Kubernetes configuration"""
        try:
            if settings.kubeconfig_path:
                config.load_kube_config(config_file=settings.kubeconfig_path)
            else:
                # Try in-cluster config first, then local config
                try:
                    config.load_incluster_config()
                except config.ConfigException:
                    config.load_kube_config()
        except Exception as e:
            raise Exception(f"Failed to load Kubernetes config: {str(e)}")
    
    def _initialize_clients(self):
        """Initialize Kubernetes API clients"""
        self.api_client = client.ApiClient()
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.networking_v1 = client.NetworkingV1Api()
        self.autoscaling_v1 = client.AutoscalingV1Api()
        self.storage_v1 = client.StorageV1Api()
    
    @tracer.start_as_current_span("k8s_create_resource")
    async def create_resource(
        self, 
        resource_type: str, 
        namespace: str, 
        manifest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a Kubernetes resource"""
        with tracer.start_as_current_span("create_operation") as span:
            span.set_attribute("resource_type", resource_type)
            span.set_attribute("namespace", namespace)
            
            try:
                if resource_type == "pod":
                    result = self.core_v1.create_namespaced_pod(
                        namespace=namespace, body=manifest
                    )
                elif resource_type == "deployment":
                    result = self.apps_v1.create_namespaced_deployment(
                        namespace=namespace, body=manifest
                    )
                elif resource_type == "service":
                    result = self.core_v1.create_namespaced_service(
                        namespace=namespace, body=manifest
                    )
                elif resource_type == "configmap":
                    result = self.core_v1.create_namespaced_config_map(
                        namespace=namespace, body=manifest
                    )
                elif resource_type == "secret":
                    result = self.core_v1.create_namespaced_secret(
                        namespace=namespace, body=manifest
                    )
                elif resource_type == "ingress":
                    result = self.networking_v1.create_namespaced_ingress(
                        namespace=namespace, body=manifest
                    )
                elif resource_type == "namespace":
                    result = self.core_v1.create_namespace(body=manifest)
                elif resource_type == "persistentvolumeclaim":
                    result = self.core_v1.create_namespaced_persistent_volume_claim(
                        namespace=namespace, body=manifest
                    )
                elif resource_type == "horizontalpodautoscaler":
                    result = self.autoscaling_v1.create_namespaced_horizontal_pod_autoscaler(
                        namespace=namespace, body=manifest
                    )
                else:
                    raise ValueError(f"Unsupported resource type: {resource_type}")
                
                span.set_attribute("success", True)
                return self._serialize_k8s_object(result)
                
            except ApiException as e:
                span.record_exception(e)
                raise Exception(f"Kubernetes API error: {e.status} - {e.reason}")
    
    @tracer.start_as_current_span("k8s_update_resource")
    async def update_resource(
        self, 
        resource_type: str, 
        name: str, 
        namespace: str, 
        manifest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a Kubernetes resource"""
        with tracer.start_as_current_span("update_operation") as span:
            span.set_attribute("resource_type", resource_type)
            span.set_attribute("resource_name", name)
            span.set_attribute("namespace", namespace)
            
            try:
                if resource_type == "pod":
                    result = self.core_v1.patch_namespaced_pod(
                        name=name, namespace=namespace, body=manifest
                    )
                elif resource_type == "deployment":
                    result = self.apps_v1.patch_namespaced_deployment(
                        name=name, namespace=namespace, body=manifest
                    )
                elif resource_type == "service":
                    result = self.core_v1.patch_namespaced_service(
                        name=name, namespace=namespace, body=manifest
                    )
                elif resource_type == "configmap":
                    result = self.core_v1.patch_namespaced_config_map(
                        name=name, namespace=namespace, body=manifest
                    )
                elif resource_type == "secret":
                    result = self.core_v1.patch_namespaced_secret(
                        name=name, namespace=namespace, body=manifest
                    )
                elif resource_type == "ingress":
                    result = self.networking_v1.patch_namespaced_ingress(
                        name=name, namespace=namespace, body=manifest
                    )
                else:
                    raise ValueError(f"Unsupported resource type for update: {resource_type}")
                
                span.set_attribute("success", True)
                return self._serialize_k8s_object(result)
                
            except ApiException as e:
                span.record_exception(e)
                raise Exception(f"Kubernetes API error: {e.status} - {e.reason}")
    
    @tracer.start_as_current_span("k8s_delete_resource")
    async def delete_resource(
        self, 
        resource_type: str, 
        name: str, 
        namespace: str
    ) -> Dict[str, Any]:
        """Delete a Kubernetes resource"""
        with tracer.start_as_current_span("delete_operation") as span:
            span.set_attribute("resource_type", resource_type)
            span.set_attribute("resource_name", name)
            span.set_attribute("namespace", namespace)
            
            try:
                if resource_type == "pod":
                    result = self.core_v1.delete_namespaced_pod(
                        name=name, namespace=namespace
                    )
                elif resource_type == "deployment":
                    result = self.apps_v1.delete_namespaced_deployment(
                        name=name, namespace=namespace
                    )
                elif resource_type == "service":
                    result = self.core_v1.delete_namespaced_service(
                        name=name, namespace=namespace
                    )
                elif resource_type == "configmap":
                    result = self.core_v1.delete_namespaced_config_map(
                        name=name, namespace=namespace
                    )
                elif resource_type == "secret":
                    result = self.core_v1.delete_namespaced_secret(
                        name=name, namespace=namespace
                    )
                elif resource_type == "ingress":
                    result = self.networking_v1.delete_namespaced_ingress(
                        name=name, namespace=namespace
                    )
                elif resource_type == "namespace":
                    result = self.core_v1.delete_namespace(name=name)
                elif resource_type == "persistentvolumeclaim":
                    result = self.core_v1.delete_namespaced_persistent_volume_claim(
                        name=name, namespace=namespace
                    )
                else:
                    raise ValueError(f"Unsupported resource type for deletion: {resource_type}")
                
                span.set_attribute("success", True)
                return self._serialize_k8s_object(result)
                
            except ApiException as e:
                span.record_exception(e)
                raise Exception(f"Kubernetes API error: {e.status} - {e.reason}")
    
    @tracer.start_as_current_span("k8s_scale_deployment")
    async def scale_deployment(
        self, 
        name: str, 
        namespace: str, 
        replicas: int
    ) -> Dict[str, Any]:
        """Scale a deployment"""
        with tracer.start_as_current_span("scale_operation") as span:
            span.set_attribute("deployment_name", name)
            span.set_attribute("namespace", namespace)
            span.set_attribute("replicas", replicas)
            
            try:
                # Get current deployment
                deployment = self.apps_v1.read_namespaced_deployment(
                    name=name, namespace=namespace
                )
                
                # Update replicas
                deployment.spec.replicas = replicas
                
                # Apply update
                result = self.apps_v1.patch_namespaced_deployment(
                    name=name, namespace=namespace, body=deployment
                )
                
                span.set_attribute("success", True)
                return self._serialize_k8s_object(result)
                
            except ApiException as e:
                span.record_exception(e)
                raise Exception(f"Kubernetes API error: {e.status} - {e.reason}")
    
    @tracer.start_as_current_span("k8s_get_resource")
    async def get_resource(
        self, 
        resource_type: str, 
        name: str, 
        namespace: str
    ) -> Dict[str, Any]:
        """Get a specific Kubernetes resource"""
        with tracer.start_as_current_span("get_operation") as span:
            span.set_attribute("resource_type", resource_type)
            span.set_attribute("resource_name", name)
            span.set_attribute("namespace", namespace)
            
            try:
                if resource_type == "pod":
                    result = self.core_v1.read_namespaced_pod(
                        name=name, namespace=namespace
                    )
                elif resource_type == "deployment":
                    result = self.apps_v1.read_namespaced_deployment(
                        name=name, namespace=namespace
                    )
                elif resource_type == "service":
                    result = self.core_v1.read_namespaced_service(
                        name=name, namespace=namespace
                    )
                elif resource_type == "configmap":
                    result = self.core_v1.read_namespaced_config_map(
                        name=name, namespace=namespace
                    )
                elif resource_type == "secret":
                    result = self.core_v1.read_namespaced_secret(
                        name=name, namespace=namespace
                    )
                elif resource_type == "ingress":
                    result = self.networking_v1.read_namespaced_ingress(
                        name=name, namespace=namespace
                    )
                elif resource_type == "namespace":
                    result = self.core_v1.read_namespace(name=name)
                else:
                    raise ValueError(f"Unsupported resource type: {resource_type}")
                
                span.set_attribute("success", True)
                return self._serialize_k8s_object(result)
                
            except ApiException as e:
                span.record_exception(e)
                raise Exception(f"Kubernetes API error: {e.status} - {e.reason}")
    
    @tracer.start_as_current_span("k8s_list_resources")
    async def list_resources(
        self, 
        resource_type: str, 
        namespace: str = None
    ) -> List[Dict[str, Any]]:
        """List Kubernetes resources"""
        with tracer.start_as_current_span("list_operation") as span:
            span.set_attribute("resource_type", resource_type)
            if namespace:
                span.set_attribute("namespace", namespace)
            
            try:
                if resource_type == "pod":
                    if namespace:
                        result = self.core_v1.list_namespaced_pod(namespace=namespace)
                    else:
                        result = self.core_v1.list_pod_for_all_namespaces()
                elif resource_type == "deployment":
                    if namespace:
                        result = self.apps_v1.list_namespaced_deployment(namespace=namespace)
                    else:
                        result = self.apps_v1.list_deployment_for_all_namespaces()
                elif resource_type == "service":
                    if namespace:
                        result = self.core_v1.list_namespaced_service(namespace=namespace)
                    else:
                        result = self.core_v1.list_service_for_all_namespaces()
                elif resource_type == "namespace":
                    result = self.core_v1.list_namespace()
                elif resource_type == "node":
                    result = self.core_v1.list_node()
                else:
                    raise ValueError(f"Unsupported resource type for listing: {resource_type}")
                
                span.set_attribute("success", True)
                span.set_attribute("items_count", len(result.items))
                
                return [self._serialize_k8s_object(item) for item in result.items]
                
            except ApiException as e:
                span.record_exception(e)
                raise Exception(f"Kubernetes API error: {e.status} - {e.reason}")
    
    async def patch_resource(
        self, 
        resource_type: str, 
        name: str, 
        namespace: str, 
        patch: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a patch to a Kubernetes resource"""
        return await self.update_resource(resource_type, name, namespace, patch)
    
    def _serialize_k8s_object(self, k8s_obj) -> Dict[str, Any]:
        """Convert Kubernetes object to dictionary"""
        if hasattr(k8s_obj, 'to_dict'):
            return k8s_obj.to_dict()
        else:
            # Fallback for objects that don't have to_dict method
            return self.api_client.sanitize_for_serialization(k8s_obj)
    
    async def get_cluster_info(self) -> Dict[str, Any]:
        """Get basic cluster information"""
        try:
            version = client.VersionApi().get_code()
            nodes = self.core_v1.list_node()
            namespaces = self.core_v1.list_namespace()
            
            return {
                "version": self._serialize_k8s_object(version),
                "nodes_count": len(nodes.items),
                "namespaces_count": len(namespaces.items),
                "cluster_health": "healthy"  # Simplified health check
            }
        except Exception as e:
            return {
                "error": str(e),
                "cluster_health": "unhealthy"
            }
