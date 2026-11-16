output "user_pool_id" {
  description = "Cognito user pool ID."
  value       = aws_cognito_user_pool.this.id
}

output "client_id" {
  description = "Public SPA app client ID. It is not a secret."
  value       = aws_cognito_user_pool_client.web.id
}

output "issuer" {
  description = "OIDC issuer used by the FastAPI JWT verifier."
  value       = "https://cognito-idp.${var.region}.amazonaws.com/${aws_cognito_user_pool.this.id}"
}

output "cognito_domain" {
  description = "Hosted login domain used by the React app."
  value       = "https://${aws_cognito_user_pool_domain.this.domain}.auth.${var.region}.amazoncognito.com"
}