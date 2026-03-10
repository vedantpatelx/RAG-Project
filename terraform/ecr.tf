resource "aws_ecr_repository" "rag_project" {
  name                 = "rag-project"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "rag_lambda" {
  name                 = "rag-lambda"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}