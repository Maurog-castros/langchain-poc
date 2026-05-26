# AWS Setup

## S3

Crear bucket y prefijo:

```powershell
aws s3 mb s3://YOUR_BUCKET_NAME --region us-east-1
aws s3api put-bucket-versioning --bucket YOUR_BUCKET_NAME --versioning-configuration Status=Enabled
```

Usar política mínima en `infra/iam-policy-s3-minimal.json`.

## IAM

Principio mínimo:

- `s3:ListBucket` solo prefijo `local-ai-devops-poc/*`.
- `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` solo objetos del prefijo.
- ECR, CloudWatch, ECS/Lambda y SSM deben ir en políticas separadas por deploy role.

## CloudWatch

Futuro ECS:

- Log group: `/ecs/local-ai-devops-poc`.
- Retención sugerida PoC: 7 a 14 días.
- No loggear prompts sensibles ni secretos.

## ECR

```powershell
aws ecr create-repository --repository-name local-ai-devops-poc
```

Tag sugerido: git SHA.

## ECS o Lambda

- ECS Fargate si necesitas runtime largo, RAG local persistente o modelos auxiliares.
- Lambda si solo orquestas API remota y tareas cortas.

## Secrets

Preferir SSM Parameter Store para PoC:

```powershell
aws ssm put-parameter --name /local-ai-devops-poc/openai-compatible-key --type SecureString --value "REPLACE"
```

En producción, rotación y auditoría con Secrets Manager.
