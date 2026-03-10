resource "aws_s3_bucket" "documents" {
  bucket = "rag-project-docs-ragproject"
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration {
    status = "Enabled"
  }
}