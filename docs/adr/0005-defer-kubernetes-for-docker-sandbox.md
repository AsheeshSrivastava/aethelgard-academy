# ADR 0005: Defer Kubernetes in Favor of Container-Isolated Runners

- **Status:** Accepted
- **Decider:** Lead Educational Engineer & Systems Architect (Asheesh Ranjan Srivastava)
- **Date:** 2026-10-30

---

## 1. Context & Problem Statement

The platform must safely execute untrusted learner Python scripts with resource quotas (memory $\le 128$MB, CPU $\le 1$ core, timeout $\le 5$s) and network isolation (`--network none`).

We considered whether to introduce **Kubernetes (K8s)** to orchestrate execution pods versus using **direct container runtimes (Docker Engine / containerd)**.

Introducing Kubernetes at this phase introduces:
1. Heavy cluster management overhead (control plane, etcd, CNI, ingress controllers).
2. Substantial infrastructure cost and complex local development setup (Minikube / Kind).
3. Decreased development velocity by shifting focus from core pedagogy to cluster operations.

---

## 2. Decision

We **defer Kubernetes** and adopt **direct container execution via Docker Engine**:
1. Ephemeral, rootless Docker containers running on the host via the Docker Engine API or subprocess runner.
2. Hardened security profiles: `--network none`, `--read-only`, dropped Linux capabilities (`--cap-drop ALL`), and cgroup memory/CPU limits.
3. Decoupled behind the `ICodeRunner` Hexagonal Port.

If and when the platform reaches multi-node scale ($\ge 50,000$ active concurrent runners across distributed clusters), we will implement a `KubernetesJobRunner` adapter fulfilling the existing `ICodeRunner` protocol without altering any platform business logic.

---

## 3. Consequences

### Positive
- **Instant Local Development:** Zero Kubernetes setup; runs directly with standard Docker or fallback mock runner.
- **Low Operational Complexity:** Single-node Docker daemon can comfortably execute thousands of containerized runs per hour.
- **Future-Proof:** The `ICodeRunner` protocol guarantees that switching to Kubernetes later requires zero refactoring of curriculum, progression, or state modules.

### Trade-offs / Mitigations
- Single-node compute boundary. Mitigated by the fact that learner scripts are ephemeral (running for $< 500$ms on average), yielding high concurrent density per machine.
