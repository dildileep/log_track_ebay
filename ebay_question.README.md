# eBay DevOps / MLOps Deployment Script Review

## Overview

This document analyzes and fixes a real MLOps deployment script used at **eBay** to deploy **fraud detection models** to a production Kubernetes cluster.

The original script contains:
- 2 serious bugs that can cause production failures  
- 2 incomplete TODO sections that must be implemented for production readiness  

### Objectives
1. Identify and fix both bugs — explain what’s wrong and why.  
2. Complete both TODO sections with production-quality code.  

### Context
- Multi-tenant Kubernetes cluster  
- Over 50 million daily transactions  
- Zero downtime deployment requirement  

---

## Original Script

```python
import subprocess
import yaml
import time
import requests
 
MODEL_NAME = "fraud-detection"
NAMESPACE = "ml-prod"
IMAGE_REPO = "ebay-ml-registry.io"
DEPLOYMENT_YAML = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {MODEL_NAME}
  namespace: {NAMESPACE}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {MODEL_NAME}
  template:
    metadata:
      labels:
        app: {MODEL_NAME}
    spec:
      containers:
      - name: model-server
        image: {IMAGE_REPO}/{MODEL_NAME}:{{version}}
        ports:
        - containerPort: 8080
        # TODO: ADD READINESS AND LIVENESS PROBES HERE
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
"""
 
def build_and_push_image(version):
    print(f"Building Docker image for version {version}")
    subprocess.run(f"docker build -t {IMAGE_REPO}/{MODEL_NAME}:{version} .", shell=True)
    subprocess.run(f"docker push {IMAGE_REPO}/{MODEL_NAME}:{version}", shell=True)  # BUG 1
 
def deploy_to_k8s(version):
    deployment = DEPLOYMENT_YAML.format(version=version)
	print("Deployment applied, waiting for rollout...")
	try:
		with open("deployment.yaml", "w") as f:
			f.write(deployment)
		subprocess.run(f"kubectl apply -f deployment.yaml -n {NAMESPACE}", shell=True, check=True)
	expect Exceptions as e :
		exit 1
    time.sleep(10)  # BUG 2
    print("Deployment complete!")
 
def verify_deployment():
	res=subprocess.run(f"kubectl getservice {NAMESPACE}", shell=True, check=True)
	if res:
		log.info("deployment completed")
    # TODO: IMPLEMENT HEALTH CHECK VERIFICATION
	else:
		exit()
 
if __name__ == "__main__":
    version = "v1.2.3"
    build_and_push_image(version)
    deploy_to_k8s(version)
    verify_deployment()
    print(f"Model {MODEL_NAME} version {version} deployed successfully!")
Identified Bugs and Fixes
Bug 1 – Missing error handling and unsafe shell usage

Problem:

subprocess.run(f"docker push {IMAGE_REPO}/{MODEL_NAME}:{version}", shell=True)


Uses shell=True, which is insecure and unnecessary in CI/CD environments.

Missing check=True, so the process will not stop even if the image push fails.

A failed push could lead to deploying a non-existent image.

Fix:

subprocess.run(["docker", "push", f"{IMAGE_REPO}/{MODEL_NAME}:{version}"], check=True)


Reason:
This ensures that the deployment halts immediately if the image push fails, preventing invalid image rollouts.

Bug 2 – Using static sleep instead of rollout check

Problem:

time.sleep(10)


A fixed sleep duration does not guarantee that the deployment is ready.

Rollout times vary depending on cluster load and image size.

This could result in incomplete rollouts or traffic sent to unready pods.

Fix:

subprocess.run(
    ["kubectl", "rollout", "status", f"deployment/{MODEL_NAME}", "-n", NAMESPACE, "--timeout=180s"],
    check=True
)


Reason:
This ensures that the script waits for Kubernetes to fully complete the rollout before continuing, achieving true zero-downtime deployment.

Completed TODO Sections
TODO 1 – Add Readiness and Liveness Probes

Problem:
Without probes, Kubernetes cannot detect unhealthy containers or exclude unready pods from service load balancing.

Fix (add to deployment YAML):

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 3
  successThreshold: 1
  failureThreshold: 3


Reason:

The liveness probe restarts unhealthy pods automatically.

The readiness probe ensures only healthy pods serve traffic during deployment.

TODO 2 – Implement Deployment Health Verification

Problem:
verify_deployment() does not verify if the model API is live or responding correctly.

Fix:

def verify_deployment():
    print("Verifying deployment health...")

    # Ensure Kubernetes rollout completion
    subprocess.run(
        ["kubectl", "rollout", "status", f"deployment/{MODEL_NAME}", "-n", NAMESPACE, "--timeout=180s"],
        check=True
    )

    # Check model API readiness
    service_url = f"http://{MODEL_NAME}.{NAMESPACE}.svc.cluster.local:8080/ready"
    for _ in range(10):
        try:
            resp = requests.get(service_url, timeout=5)
            if resp.status_code == 200:
                print("Model service is healthy and ready.")
                return
        except requests.RequestException:
            pass
        time.sleep(5)

    raise RuntimeError("Deployment verification failed: service not ready after retries.")


Reason:
This ensures the model API is live, responding to requests, and ready to serve production traffic.

Final Production-Ready Script
import subprocess
import time
import requests

MODEL_NAME = "fraud-detection"
NAMESPACE = "ml-prod"
IMAGE_REPO = "ebay-ml-registry.io"

DEPLOYMENT_YAML = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {MODEL_NAME}
  namespace: {NAMESPACE}
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: {MODEL_NAME}
  template:
    metadata:
      labels:
        app: {MODEL_NAME}
    spec:
      containers:
      - name: model-server
        image: {IMAGE_REPO}/{MODEL_NAME}:{{version}}
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
"""

def build_and_push_image(version):
    print(f"Building Docker image for version {version}")
    subprocess.run(["docker", "build", "-t", f"{IMAGE_REPO}/{MODEL_NAME}:{version}", "."], check=True)
    subprocess.run(["docker", "push", f"{IMAGE_REPO}/{MODEL_NAME}:{version}"], check=True)

def deploy_to_k8s(version):
    deployment = DEPLOYMENT_YAML.format(version=version)
    with open("deployment.yaml", "w") as f:
        f.write(deployment)

    print("Applying Kubernetes deployment...")
    subprocess.run(["kubectl", "apply", "-f", "deployment.yaml", "-n", NAMESPACE], check=True)
    subprocess.run(["kubectl", "rollout", "status", f"deployment/{MODEL_NAME}", "-n", NAMESPACE, "--timeout=180s"], check=True)
    print("Deployment rollout completed successfully.")

def verify_deployment():
    print("Verifying deployment health...")
    service_url = f"http://{MODEL_NAME}.{NAMESPACE}.svc.cluster.local:8080/ready"
    for _ in range(10):
        try:
            resp = requests.get(service_url, timeout=5)
            if resp.status_code == 200:
                print("Model service is healthy and ready.")
                return
        except requests.RequestException:
            pass
        time.sleep(5)
    raise RuntimeError("Deployment verification failed: service not ready after retries.")

if __name__ == "__main__":
    version = "v1.2.3"
    build_and_push_image(version)
    deploy_to_k8s(version)
    verify_deployment()
    print(f"Model {MODEL_NAME} version {version} deployed successfully.")

Summary Table
Type	Issue	Fix	Reason
Bug 1	Unchecked Docker push using shell=True	Added check=True and removed shell=True	Prevents deploying broken images
Bug 2	Static sleep instead of rollout status	Used kubectl rollout status	Ensures pods are actually ready
TODO 1	Missing readiness/liveness probes	Added standard HTTP probes	Ensures healthy pods handle traffic
TODO 2	No health verification	Added rollout and HTTP readiness checks	Validates service before production traffic
Key Takeaways

Always use check=True in subprocess commands for safe CI/CD operations.

Avoid arbitrary sleep; use Kubernetes rollout checks.

Liveness and readiness probes are mandatory for reliable production deployments.

Always verify that the model API is live and responding after rollout.