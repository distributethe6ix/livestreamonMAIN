resource "random_integer" "bucket_suffix" {
  min = 1000
  max = 9999
}

locals {
  bucket_name = "${var.bucket_name}-${random_integer.bucket_suffix.result}"
}

resource "aws_s3_bucket" "mah_bucket" {
  bucket = local.bucket_name
  tags = {
    Name = local.bucket_name
  }
}

resource "aws_s3_bucket_ownership_controls" "mah_bucket" {
  bucket = aws_s3_bucket.mah_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "mah_bucket" {
  bucket = aws_s3_bucket.mah_bucket.id
  acl    = "private"

  depends_on = [aws_s3_bucket_ownership_controls.mah_bucket]
}

resource "aws_iam_role" "lambda_role" {
  name = "s3_notification_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "s3_notification_lambda_policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_s3_bucket.mah_bucket.arn}/*",
          "arn:aws:logs:*:*:*"
        ]
      }
    ]
  })
}

resource "aws_lambda_function" "s3_notification" {
  filename      = "lambda_function.zip"
  function_name = "s3_notification_handler"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.mah_bucket.id
    }
  }
}

resource "aws_lambda_permission" "s3_notification" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.s3_notification.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.mah_bucket.arn

  lifecycle {
    replace_triggered_by = [ aws_lambda_function.s3_notification ]
  }
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.mah_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.s3_notification.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.s3_notification]

  lifecycle {
    replace_triggered_by = [ aws_lambda_function.s3_notification ]
  }
}
