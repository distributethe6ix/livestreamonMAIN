
resource "aws_cloudwatch_event_rule" "transcribe_completed" {
  name        = "capture-transcribe-completion"
  description = "Capture all Transcribe job completion events"

  event_pattern = jsonencode({
    source      = ["aws.transcribe"]
    detail-type = ["Transcribe Job State Change"]
    detail = {
      TranscriptionJobStatus = ["COMPLETED"]
    }
  })
}

resource "aws_iam_role" "eventbridge_invoke_lambda" {
  name = "eventbridge-invoke-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "eventbridge_invoke_lambda" {
  name = "eventbridge-invoke-lambda-policy"
  role = aws_iam_role.eventbridge_invoke_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.transcribe_processor.arn
        ]
      }
    ]
  })
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.transcribe_completed.name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.transcribe_processor.arn
  role_arn  = aws_iam_role.eventbridge_invoke_lambda.arn
}


