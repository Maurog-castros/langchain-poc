# AWS CLI Examples

```powershell
aws s3 mb s3://YOUR_BUCKET_NAME --region us-east-1
aws s3 cp .\models\llama3.2.gguf s3://YOUR_BUCKET_NAME/local-ai-devops-poc/model/llama3.2.gguf
aws s3 sync .\reports s3://YOUR_BUCKET_NAME/local-ai-devops-poc/report/
aws ecr create-repository --repository-name local-ai-devops-poc
aws logs create-log-group --log-group-name /ecs/local-ai-devops-poc
aws ssm put-parameter --name /local-ai-devops-poc/openai-compatible-key --type SecureString --value "REPLACE"
```

Never commit generated AWS credentials, `.env`, large model files, datasets, or reports.
