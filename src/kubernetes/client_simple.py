"""
Simplified Kubernetes Client for AutoOps
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from ..monitoring.tracing_simple import get_tracer

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)


class KubernetesClient:
    """Simplified Kubernetes client for basic operations"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None):
        """Initialize the Kubernetes client"""
        self.logger = logging.getLogger(__name__)
        
        try:
            if kubeconfig_path:
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                # Try to load in-cluster config first, then local config
                try:
                    config.load_incluster_config()
                except config.config_exception.ConfigException:
                    config.load_kube_config()
            
            # Initialize API clients
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize Kubernetes client: {e}")
            self.v1 = None
            self.apps_v1 = None
            self.networking_v1 = None
    
    async def create_resource(
        self, 
        resource_type: str, 
        namespace: str, 
        manifest: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a Kubernetes resource"""
        with tracer.start_as_current_span("k8s_create_resource") as span:
            span.set_attribute("resource_type", resource_type)
            span.set_attribute("namespace", namespace)
            
            try:
                if not self.v1:
                    raise Exception("Kubernetes client not initialized")
                
                # Convert manifest to appropriate Kubernetes object
                if resource_type.lower() == "deployment":
                    body = client.V1Deployment(**manifest)
                    result = self.apps_v1.create_namespaced_deployment(
                        namespace=namespace, body=body
                    )
                elif resource_type.lower() == "service":
                    body = client.V1Service(**manifest)
                    result = self.v1.create_namespaced_service(
                        namespace=namespace, body=body
                    )
                elif resource_type.lower() == "pod":
                    body = client.V1Pod(**manifest)
                    result = self.v1.create_namespaced_pod(
                        namespace=namespace, body=body
                    )
                else:
                    raise ValueError(f"Unsupported resource type: {resource_type}")
                
                span.set_status("OK")
                return {"status": "created", "name": result.metadata.name}
                
            except Exception as e:
                span.set_status("ERROR", str(e))
                self.logger.error(f"Failed to create {resource_type}: {e}")
                raise
    
    async def get_resource(
        self, 
        resource_type: str, 
        name: str, 
        namespace: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """Get a Kubernetes resource"""
        with tracer.start_as_current_span("k8s_get_resource") as span:
            span.set_attribute("resource_type", resource_type)
            span.set_attribute("name", name)
            span.set_attribute("namespace", namespace)
            
            try:
                if not self.v1:
                    raise Exception("Kubernetes client not initialized")
                
                if resource_type.lower() == "deployment":
                    result = self.apps_v1.read_namespaced_deployment(
                        name=name, namespace=namespace
                    )
                elif resource_type.lower() == "service":
                    result = self.v1.read_namespaced_service(
                        name=name, namespace=namespace
                    )
                elif resource_type.lower() == "pod":
                    result = self.v1.read_namespaced_pod(
                        name=name, namespace=namespace
                    )
                else:
                    raise ValueError(f"Unsupported resource type: {resource_type}")
                
                span.set_status("OK")
                return {
                    "name": result.metadata.name,
                    "namespace": result.metadata.namespace,
                    "status": getattr(result, 'status', {}),
                    "spec": getattr(result, 'spec', {})
                }
                
            except ApiException as e:
                if e.status == 404:
                    return None
                span.set_status("ERROR", str(e))
                self.logger.error(f"Failed to get {resource_type} {name}: {e}")
                raise
            except Exception as e:
                span.set_status("ERROR", str(e))
                self.logger.error(f"Failed to get {resource_type} {name}: {e}")
                raise
    
    async def list_resources(
        self, 
        resource_type: str, 
        namespace: str = "default"
    ) -> List[Dict[str, Any]]:
        """List Kubernetes resources"""
        with tracer.start_as_current_span("k8s_list_resources") as span:
            span.set_attribute("resource_type", resource_type)
            span.set_attribute("namespace", namespace)
            
            try:
                if not self.v1:
                    raise Exception("Kubernetes client not initialized")
                
                if resource_type.lower() == "deployment":
                    result = self.apps_v1.list_namespaced_deployment(namespace=namespace)
                elif resource_type.lower() == "service":
                    result = self.v1.list_namespaced_service(namespace=namespace)
                elif resource_type.lower() == "pod":
                    result = self.v1.list_namespaced_pod(namespace=namespace)
                else:
                    raise ValueError(f"Unsupported resource type: {resource_type}")
                
                resources = []
                for item in result.items:
                    resources.append({
                        "name": item.metadata.name,
                        "namespace": item.metadata.namespace,
                        "status": getattr(item, 'status', {}),
                        "spec": getattr(item, 'spec', {})
                    })
                
                span.set_status("OK")
                return resources
                
            except Exception as e:
                span.set_status("ERROR", str(e))
                self.logger.error(f"Failed to list {resource_type}: {e}")
                raise
    
    async def delete_resource(
        self, 
        resource_type: str, 
        name: str, 
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """Delete a Kubernetes resource"""
        with tracer.start_as_current_span("k8s_delete_resource") as span:
            span.set_attribute("resource_type", resource_type)
            span.set_attribute("name", name)
            span.set_attribute("namespace", namespace)
            
            try:
                if not self.v1:
                    raise Exception("Kubernetes client not initialized")
                
                if resource_type.lower() == "deployment":
                    self.apps_v1.delete_namespaced_deployment(
                        name=name, namespace=namespace
                    )
                elif resource_type.lower() == "service":
                    self.v1.delete_namespaced_service(
                        name=name, namespace=namespace
                    )
                elif resource_type.lower() == "pod":
                    self.v1.delete_namespaced_pod(
                        name=name, namespace=namespace
                    )
                else:
                    raise ValueError(f"Unsupported resource type: {resource_type}")
                
                span.set_status("OK")
                return {"status": "deleted", "name": name}
                
            except Exception as e:
                span.set_status("ERROR", str(e))
                self.logger.error(f"Failed to delete {resource_type} {name}: {e}")
                raise
