#!/bin/bash

set -e

echo "[*] Updating system packages..."
sudo apt-get update -y
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    apt-transport-https \
    software-properties-common

echo "[*] Adding Docker GPG key..."
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo "[*] Adding Docker APT repository..."
ARCH=$(dpkg --print-architecture)
RELEASE=$(lsb_release -cs)
echo \
  "deb [arch=$ARCH signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $RELEASE stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "[*] Updating package index..."
sudo apt-get update -y

echo "[*] Installing Docker Engine..."
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "[*] Enabling Docker service..."
sudo systemctl enable docker
sudo systemctl start docker

echo "[*] Adding current user ($USER) to the docker group..."
sudo usermod -aG docker $USER

echo "[✓] Docker installation complete. You may need to log out and back in for group changes to take effect."
