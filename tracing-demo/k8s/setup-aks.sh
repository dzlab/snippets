#!/bin/bash

RESOURCE_GROUP=test-dzlab-azrg-01
AKS_NAME=test-dzlab-azaks-01
ACR_NAME=dzlabacr01

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD=$(tput bold)

echo "\n${GREEN}login into Azure\n${NC}"
az login

echo "\n${GREEN}Creating resource group $RESOURCE_GROUP\n${NC}"
az group create --name $RESOURCE_GROUP --location westus

echo "\n${GREEN}Creating AKS $AKS_NAME\n${NC}"
az aks create --resource-group $RESOURCE_GROUP --name $AKS_NAME --node-count 1 --generate-ssh-keys

echo "\n${GREEN}Downloading AKS $AKS_NAME credentials\n${NC}"
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_NAME

echo "\n${GREEN}Creating container registery $ACR_NAME\n${NC}"
az acr create -n $ACR_NAME -g $RESOURCE_GROUP --sku basic

echo "\n${GREEN}Attaching AKS $AKS_NAME to container registery $ACR_NAME\n${NC}"
az aks update -n $AKS_NAME -g $RESOURCE_GROUP --attach-acr $ACR_NAME

echo "\n${GREEN}Login into container registery $ACR_NAME\n${NC}"
az acr login --name $ACR_NAME