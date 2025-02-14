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

  depends_on = [ aws_s3_bucket_ownership_controls.mah_bucket ]
}
