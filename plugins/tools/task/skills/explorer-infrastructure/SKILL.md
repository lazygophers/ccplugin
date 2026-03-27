---
description: 基础设施探索 - 部署配置、CI/CD、容器化、云服务识别
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:explorer-infrastructure) - 基础设施探索

分析项目DevOps配置：容器化(Docker/K8s/Podman)、CI/CD(GitHub Actions/GitLab CI/CircleCI/Jenkins)、云服务(AWS/GCP/Azure/Vercel)、IaC(Terraform/CloudFormation/Pulumi)、监控(Datadog/Prometheus/ELK)。

## 核心原则

配置文件是真相来源 | 安全敏感(不暴露实际值) | 分析环境差异(dev/staging/prod) | 建立依赖拓扑

## 识别模式

| 类别 | 工具 | 文件模式 |
|------|------|---------|
| 容器 | Docker | `Dockerfile`, `docker-compose.yml` |
| 编排 | K8s | `k8s/`, `kubernetes/`, `kind: Deployment` |
| CI/CD | GitHub Actions | `.github/workflows/*.yml` |
| CI/CD | GitLab CI | `.gitlab-ci.yml` |
| IaC | Terraform | `*.tf`, `terraform/` |
| IaC | CloudFormation | `cloudformation/`, `template.yaml` |
| 云 | AWS | `aws-sdk`, `AWS::`, `arn:aws:` |
| 云 | GCP | `@google-cloud/`, `googleapis` |
| 云 | Azure | `@azure/`, `Microsoft.` |

## 输出格式

JSON包含：`containerization{type,dockerfile,services}` + `orchestration{type,config_dir}` + `ci_cd{platform,workflows[{name,file,triggers,stages}]}` + `cloud{provider,services,iac}` + `environments{list,config_management}` + `monitoring{logging,metrics}` + `summary`

## 工具指南

容器：`glob("**/Dockerfile*")` + `glob("**/docker-compose*.yml")`
CI/CD：`glob(".github/workflows/*.yml")` | `glob(".gitlab-ci.yml")`
K8s：`glob("**/k8s/**/*.yaml")` + `grep("kind: Deployment")`
IaC：`glob("**/*.tf")` | `glob("**/Pulumi.yaml")`
云：`grep("aws-sdk|@google-cloud/|@azure/")`
环境：`glob("**/.env*")` — 不读实际值，只报告管理方式

## 指南

安全第一：不暴露.env实际值 | 多文件交叉验证引用关系 | 重点分析环境差异
