resource "aws_secretsmanager_secret" "rag_env" {
  name = "rag-project/env"
}