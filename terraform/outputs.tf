output "ecr_rag_project_url" {
  value = aws_ecr_repository.rag_project.repository_url
}

output "ecr_rag_lambda_url" {
  value = aws_ecr_repository.rag_lambda.repository_url
}

output "s3_bucket" {
  value = aws_s3_bucket.documents.bucket
}