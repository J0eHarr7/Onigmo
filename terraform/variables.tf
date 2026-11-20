# terraform/variables.tf
variable "resource_group_name" { default = "ctf-box-rg" }
variable "location" { default = "eastus2" }
variable "box_name" { default = "phantom" }
variable "vm_size" { default = "Standard_D4s_v7" }
variable "attacker_ip" { description = "Retained for compatibility; public NSG rules no longer use it" }
variable "ssh_public_key_path" { default = "~/.ssh/id_rsa.pub" }
variable "ssh_private_key_path" { default = "~/.ssh/id_rsa" }
variable "ssh_password" {
  description = "Password for the boxadmin SSH account"
  type        = string
  sensitive   = true
}