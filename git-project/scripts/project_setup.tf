provider "aws" {
  region = "us-east-1"
}

# Unique suffix to avoid naming conflicts
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# --- BRONZE BUCKET (Raw Ingestion) ---
resource "aws_s3_bucket" "bronze" {
  bucket = "prj-dl-bronze-${random_string.suffix.result}"
  force_destroy = true 
}


# --- IAM Policy: Least Privilege ---
resource "aws_iam_policy" "databricks_access" {
  name        = "Databricks_Medallion_Access"
  description = "Granular access to Bronze, Silver, and Gold layers"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Bronze: Databricks only needs to Read and List
        Action = ["s3:GetObject", "s3:ListBucket"]
        Effect = "Allow"
        Resource = [
          aws_s3_bucket.bronze.arn,
          "${aws_s3_bucket.bronze.arn}/*"
        ]
      }
    ]
  })
}

# --- IAM Role for Databricks to Assume ---
resource "aws_iam_role" "databricks_role" {
  name = "Databricks_CrossAccount_Role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_medallion" {
  role       = aws_iam_role.databricks_role.name
  policy_arn = aws_iam_policy.databricks_access.arn
}

data "aws_caller_identity" "current" {}

# --- Outputs (Use these for your Databricks config later) ---
output "bronze_bucket" { value = aws_s3_bucket.bronze.id }
output "iam_role_arn" { value = aws_iam_role.databricks_role.arn }