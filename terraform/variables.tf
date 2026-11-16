variable "region" {
  description = "AWS region for the Cognito user pool."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name used in the Cognito user pool name."
  type        = string
  default     = "dev"
}

variable "domain_prefix" {
  description = "Globally unique Cognito hosted login domain prefix in this region."
  type        = string
}

variable "callback_urls" {
  description = "Allowed sign-in callback URLs."
  type        = list(string)
  default     = ["http://localhost:5173/"]
}

variable "logout_urls" {
  description = "Allowed sign-out callback URLs."
  type        = list(string)
  default     = ["http://localhost:5173/"]
}