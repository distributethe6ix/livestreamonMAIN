terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "terraform-state-20250207175545578300000001"
    key    = "terraform.tfstate"
    region = "ca-central-1"
  }
}