# terraform/outputs.tf
output "box_ip" { value = azurerm_public_ip.box.ip_address }
output "ssh_command" { value = "ssh boxadmin@${azurerm_public_ip.box.ip_address}" }
output "keycloak" { value = "http://${azurerm_public_ip.box.ip_address}:8080" }
output "gitlab" { value = "http://${azurerm_public_ip.box.ip_address}" }