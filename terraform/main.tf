# terraform/main.tf
terraform {
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 3.0" }
    local   = { source = "hashicorp/local", version = "~> 2.0" }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "box" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_virtual_network" "box" {
  name                = "${var.box_name}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.box.location
  resource_group_name = azurerm_resource_group.box.name
}

resource "azurerm_subnet" "box" {
  name                 = "${var.box_name}-subnet"
  resource_group_name  = azurerm_resource_group.box.name
  virtual_network_name = azurerm_virtual_network.box.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_public_ip" "box" {
  name                = "${var.box_name}-pip"
  location            = azurerm_resource_group.box.location
  resource_group_name = azurerm_resource_group.box.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_network_security_group" "box" {
  name                = "${var.box_name}-nsg"
  location            = azurerm_resource_group.box.location
  resource_group_name = azurerm_resource_group.box.name

  # Only your IP can reach the box
  security_rule {
    name                       = "SSH"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "Keycloak"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "8080"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "GitLab"
    priority                   = 120
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "Quiz"
    priority                   = 125
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5000"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  # Callback listener port — player's netcat/listener for the RCE output
  security_rule {
    name                       = "Callback"
    priority                   = 130
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "8000-9000"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_network_interface" "box" {
  name                = "${var.box_name}-nic"
  location            = azurerm_resource_group.box.location
  resource_group_name = azurerm_resource_group.box.name
  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.box.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.box.id
  }
}

resource "azurerm_network_interface_security_group_association" "box" {
  network_interface_id      = azurerm_network_interface.box.id
  network_security_group_id = azurerm_network_security_group.box.id
}

resource "azurerm_linux_virtual_machine" "box" {
  name                = var.box_name
  resource_group_name = azurerm_resource_group.box.name
  location            = azurerm_resource_group.box.location
  # GitLab minimum: 4 vCPU / 16 GB RAM. Standard_D4s_v3 can be capacity-blocked in some regions.
  size                            = var.vm_size
  admin_username                  = "boxadmin"
  admin_password                  = var.ssh_password
  disable_password_authentication = false

  network_interface_ids = [azurerm_network_interface.box.id]

  admin_ssh_key {
    username   = "boxadmin"
    public_key = file(var.ssh_public_key_path)
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
    disk_size_gb         = 80 # GitLab + Keycloak + repo data
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }
}

resource "local_file" "ansible_inventory" {
  content  = <<-EOT
    [box]
    ${azurerm_public_ip.box.ip_address} ansible_user=boxadmin ansible_password=${var.ssh_password} ansible_ssh_common_args='-o StrictHostKeyChecking=no'
  EOT
  filename = "../ansible/inventory.ini"
}