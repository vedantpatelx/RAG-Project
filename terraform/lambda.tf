resource "aws_lambda_function" "ingestion" {
  function_name = "rag-ingestion"
  package_type  = "Image"
  image_uri     = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/rag-lambda:latest"
  role          = aws_iam_role.lambda.arn
  timeout       = 300
  memory_size   = 3008
}

resource "aws_lambda_permission" "s3" {
  statement_id  = "s3-trigger"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.documents.arn
}

resource "aws_s3_bucket_notification" "trigger" {
  bucket = aws_s3_bucket.documents.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.ingestion.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "documents/"
    filter_suffix       = ".pdf"
  }

  depends_on = [aws_lambda_permission.s3]
}