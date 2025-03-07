resource "aws_lambda_function" "transcribe_processor" {
  filename      = "transcribe_function.zip"
  function_name = "transcribe-processor"
  role          = aws_iam_role.lambda_role.arn
  handler       = "transcribe_function.lambda_handler"
  runtime       = "python3.11"
  timeout       = 300

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.mah_bucket.id
    }
  }

}

resource "aws_iam_role" "transcribe_processor" {
  name = "transcribe-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.transcribe_processor.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "bedrock_invoke" {
  name = "bedrock-invoke-policy"
  role = aws_iam_role.transcribe_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = ["*"]
      }
    ]
  })
}

# allow the lambda to write to the bucket
resource "aws_iam_role_policy" "s3_write" {
  name = "s3-write-policy"
  role = aws_iam_role.transcribe_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.mah_bucket.arn}/*"
        ]
      }
    ]
  })
}
