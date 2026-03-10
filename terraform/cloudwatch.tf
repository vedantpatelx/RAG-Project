resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/rag-project"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/rag-ingestion"
  retention_in_days = 7
}