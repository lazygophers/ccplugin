---
description: 基础设施探索规范 - 部署配置、CI/CD 分析、容器化方案和云服务识别
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:explorer-infrastructure) - 基础设施探索规范

<scope>

当你需要深入理解项目的基础设施和 DevOps 配置时使用此 skill。适用于分析容器化方案（Docker/K8s）、CI/CD 流程（GitHub Actions/GitLab CI）、云服务依赖（AWS/GCP/Azure）、环境配置和密钥管理。

支持的工具和平台：
- **容器**: Docker, Docker Compose, Podman
- **编排**: Kubernetes, ECS, Cloud Run, Nomad
- **CI/CD**: GitHub Actions, GitLab CI, CircleCI, Jenkins, ArgoCD
- **云服务**: AWS, GCP, Azure, Vercel, Netlify, Fly.io
- **IaC**: Terraform, CloudFormation, Pulumi, CDK
- **监控**: Datadog, Prometheus, Grafana, ELK, CloudWatch

</scope>

<core_principles>

配置文件是真相来源。基础设施信息主要在配置文件中，优先分析配置文件而非代码。

安全敏感。配置中可能包含密钥和凭证，分析时不暴露实际值，只报告管理方式。

环境差异。必须理解不同环境（dev/staging/production）的配置差异，这对部署决策至关重要。

依赖拓扑。基础设施组件有依赖关系（应用→数据库→存储），必须建立拓扑图。

</core_principles>

<detection_patterns>

**容器化识别**：

| 工具 | 文件模式 |
|------|---------|
| Docker | `Dockerfile`, `.dockerignore` |
| Docker Compose | `docker-compose.yml`, `compose.yaml` |
| Kubernetes | `k8s/`, `kubernetes/`, `*.yaml` (kind: Deployment) |

**CI/CD 识别**：

| 平台 | 文件模式 |
|------|---------|
| GitHub Actions | `.github/workflows/*.yml` |
| GitLab CI | `.gitlab-ci.yml` |
| CircleCI | `.circleci/config.yml` |
| Jenkins | `Jenkinsfile` |
| ArgoCD | `argocd/`, `Application` manifests |

**IaC 识别**：

| 工具 | 文件模式 |
|------|---------|
| Terraform | `*.tf`, `terraform/` |
| CloudFormation | `cloudformation/`, `template.yaml` |
| Pulumi | `Pulumi.yaml`, `index.ts` |
| CDK | `cdk.json`, `lib/*-stack.ts` |

**云服务识别**：

| 平台 | 识别标志 |
|------|---------|
| AWS | `aws-sdk`, `AWS::`, `arn:aws:` |
| GCP | `@google-cloud/`, `gcloud`, `googleapis` |
| Azure | `@azure/`, `azure-`, `Microsoft.` |
| Vercel | `vercel.json`, `VERCEL_` |
| Netlify | `netlify.toml`, `NETLIFY_` |

</detection_patterns>

<output_format>

```json
{
  "containerization": {
    "type": "Docker|Podman|None",
    "dockerfile": "Dockerfile",
    "compose": "docker-compose.yml",
    "services": ["app", "db", "redis"]
  },
  "orchestration": {
    "type": "Kubernetes|Docker Compose|Serverless",
    "config_dir": "k8s/",
    "manifests": [...]
  },
  "ci_cd": {
    "platform": "GitHub Actions|GitLab CI",
    "workflows": [
      {
        "name": "deploy",
        "file": ".github/workflows/deploy.yml",
        "triggers": ["push to main"],
        "stages": ["build", "test", "deploy"]
      }
    ]
  },
  "cloud": {
    "provider": "AWS|GCP|Azure",
    "services": ["ECS", "RDS", "S3"],
    "iac": "Terraform|None",
    "iac_files": [...]
  },
  "environments": {
    "list": ["dev", "staging", "prod"],
    "config_management": ".env|ConfigMap|Secrets Manager"
  },
  "monitoring": {
    "logging": "ELK|CloudWatch",
    "metrics": "Prometheus|Datadog"
  },
  "summary": "基础设施架构总结"
}
```

</output_format>

<tools_guide>

**容器文件搜索**：
- `glob("**/Dockerfile*")` + `glob("**/docker-compose*.yml")`
- `glob("**/compose.yaml")` + `glob("**/.dockerignore")`

**CI/CD 搜索**：
- `glob(".github/workflows/*.yml")` → GitHub Actions
- `glob(".gitlab-ci.yml")` → GitLab CI
- `glob(".circleci/config.yml")` → CircleCI
- `glob("Jenkinsfile")` → Jenkins

**K8s 搜索**：
- `glob("**/k8s/**/*.yaml")` + `glob("**/kubernetes/**/*.yaml")`
- `grep("kind: Deployment|kind: Service|kind: Ingress")`

**IaC 搜索**：
- `glob("**/*.tf")` → Terraform
- `glob("**/cloudformation/**")` → CloudFormation
- `glob("**/Pulumi.yaml")` → Pulumi

**云服务搜索**：
- `grep("aws-sdk|AWS::|arn:aws")` → AWS
- `grep("@google-cloud/|googleapis")` → GCP
- `grep("@azure/|Microsoft\\.")` → Azure

**环境配置**：
- `glob("**/.env*")` → 环境变量文件
- 注意：不读取实际 .env 文件内容，只报告存在性和管理方式

</tools_guide>

<guidelines>

安全第一：不暴露 .env 文件中的实际值，只报告环境变量名和管理方式。

多文件交叉验证：CI/CD 配置可能引用 Dockerfile，K8s 配置可能引用 ConfigMap。需要追踪这些引用关系。

环境差异分析：重点关注 dev/staging/prod 之间的配置差异，这对理解部署策略至关重要。

</guidelines>
