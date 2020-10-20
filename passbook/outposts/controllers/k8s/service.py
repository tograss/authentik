"""Kubernetes Service Reconciler"""
from typing import TYPE_CHECKING

from kubernetes.client import CoreV1Api, V1Service, V1ServicePort, V1ServiceSpec

from passbook.outposts.controllers.k8s.base import (
    KubernetesObjectReconciler,
    NeedsUpdate,
)
from passbook.outposts.controllers.k8s.deployment import DeploymentReconciler

if TYPE_CHECKING:
    from passbook.outposts.controllers.kubernetes import KubernetesController


class ServiceReconciler(KubernetesObjectReconciler[V1Service]):
    """Kubernetes Service Reconciler"""

    def __init__(self, controller: "KubernetesController") -> None:
        super().__init__(controller)
        self.api = CoreV1Api()

    @property
    def name(self) -> str:
        return f"passbook-outpost-{self.controller.outpost.uuid.hex}"

    def reconcile(self, current: V1Service, reference: V1Service):
        if len(current.spec.ports) != len(reference.spec.ports):
            raise NeedsUpdate()
        for port in reference.spec.ports:
            if port not in current.spec.ports:
                raise NeedsUpdate()

    def get_reference_object(self) -> V1Service:
        """Get deployment object for outpost"""
        meta = self.get_object_meta(name=self.name)
        ports = []
        for port_name, port in self.controller.deployment_ports.items():
            ports.append(V1ServicePort(name=port_name, port=port))
        selector_labels = DeploymentReconciler(self.controller).get_pod_meta()
        return V1Service(
            metadata=meta,
            spec=V1ServiceSpec(ports=ports, selector=selector_labels, type="ClusterIP"),
        )

    def create(self, reference: V1Service):
        return self.api.create_namespaced_service(self.namespace, reference)

    def delete(self, reference: V1Service):
        return self.api.delete_namespaced_service(
            reference.metadata.name, self.namespace
        )

    def retrieve(self) -> V1Service:
        return self.api.read_namespaced_service(self.name, self.namespace)

    def update(self, current: V1Service, reference: V1Service):
        return self.api.patch_namespaced_service(
            current.metadata.name, self.namespace, reference
        )
