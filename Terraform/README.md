# Terraform Hetzner Kubernetes Cluster

This repository contains Terraform configuration for deploying a Kubernetes cluster on Hetzner Cloud using the [kube-hetzner](https://github.com/kube-hetzner/terraform-hcloud-kube-hetzner) module.

## Overview

This project provisions a high-availability Kubernetes cluster on Hetzner Cloud infrastructure with:
- ARM-based control plane nodes (3x cax21)
- ARM-based worker nodes (3x cax31)
- Automated Packer snapshot creation for OpenSUSE MicroOS
- GitHub Actions CI/CD pipeline with environment-based deployments
- S3-compatible backend for Terraform state management

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) installed
- [Hetzner Cloud account](https://www.hetzner.com/cloud)
- SSH key pair for node access
- (Optional) S3-compatible storage for remote state

## Configuration

### Required Variables

Configure the following in [main.tf](main.tf) or as environment variables:

```bash
# Hetzner Cloud API Token
export TF_VAR_hcloud_token="your_hetzner_api_token"

# SSH Public Key
export TF_VAR_ssh_public_key="your_ssh_public_key"
```

Alternatively, set them directly in the `locals` block in [main.tf](main.tf).

### Backend Configuration

The project uses S3-compatible storage for state management:

```hcl
bucket    = "salonmaster-tfstate"
key       = "infra.tfstate"
endpoint  = "https://salonmaster-ci.nbg1.your-objectstorage.com"
```

For backend credentials, set:

```bash
export AWS_ACCESS_KEY_ID="your_s3_access_key"
export AWS_SECRET_ACCESS_KEY="your_s3_secret_key"
```

### GitHub Secrets

For CI/CD pipeline, configure these GitHub repository secrets:

- `HCLOUD_TOKEN` - Hetzner Cloud API token
- `HETZNER_PUBLIC_KEY` - SSH public key for cluster nodes
- `HETZNER_PRIVATE_KEY` - SSH private key for cluster access
- `S3_ACCESS_KEY` - S3-compatible storage access key
- `S3_SECRET_KEY` - S3-compatible storage secret key

## Cluster Configuration

### Node Pools

**Control Plane:**
- Node count: 3 (HA configuration)
- Server type: cax21 (ARM64)
- Location: nbg1 (Nuremberg)
- Placement group: control-plane

**Worker Nodes:**
- Node count: 3
- Server type: cax31 (ARM64)
- Location: nbg1 (Nuremberg)

### Network Configuration

- Network region: `eu-central`
- Load balancer type: `lb11`
- Load balancer location: `nbg1`

## Deployment

### Manual Deployment

1. Initialize Terraform:
```bash
terraform init
```

2. Review the execution plan:
```bash
terraform plan
```

3. Apply the configuration:
```bash
terraform apply
```

### Automated Deployment (GitHub Actions)

The repository includes a GitHub Actions workflow that:

1. **Packer Phase**: Checks for and creates OpenSUSE MicroOS ARM snapshot if needed
2. **Terraform Phase**: Plans and applies infrastructure changes

Deployments are triggered on push to:
- `tst` - Test environment
- `acc` - Acceptance environment
- `prd` - Production environment

The workflow includes concurrency controls to prevent simultaneous deployments to the same environment.

## Accessing the Cluster

After successful deployment, the kubeconfig file will be available. Access details can be retrieved from Terraform outputs.

```bash
# Get cluster outputs
terraform output
```

## Customization

### Changing Node Pools

To modify node pools, edit the `control_plane_nodepools` or `agent_nodepools` blocks in [main.tf](main.tf). 

**Important:**
- Control plane nodes must be an odd number (1, 3, 5, etc.) to prevent split-brain issues
- Drain and cordon nodes before decreasing node counts
- Maximum 50 nodepools total (combined control plane and agent)

### Enabling Features

Uncomment relevant sections in [main.tf](main.tf) to enable:
- WireGuard encryption for CNI
- Custom control plane/agent configurations
- Monitoring for etcd, kube-controller-manager, etc.

## Architecture

- **Provider**: Hetzner Cloud
- **Kubernetes Distribution**: K3s
- **OS**: OpenSUSE MicroOS (ARM64)
- **CNI**: Configurable (default from kube-hetzner)
- **High Availability**: 3 control plane nodes with etcd

## Resources

- [Kube-Hetzner Documentation](https://github.com/kube-hetzner/terraform-hcloud-kube-hetzner)
- [Hetzner Cloud Locations](https://docs.hetzner.com/general/others/data-centers-and-connection/)
- [Hetzner Cloud Server Types](https://www.hetzner.com/cloud)
- [K3s Documentation](https://docs.k3s.io/)

## Troubleshooting

### SSH Connection Issues

If experiencing SSH authentication problems:
- Verify SSH agent is running
- Increase `ssh_max_auth_tries` in [main.tf](main.tf)
- Ensure SSH keys are properly configured

### State Lock Issues

If state is locked:
```bash
# Force unlock (use with caution)
terraform force-unlock <lock-id>
```

## License

This project configuration is based on the [kube-hetzner](https://github.com/kube-hetzner/terraform-hcloud-kube-hetzner) module.

## Support

For issues related to:
- **This configuration**: Open an issue in this repository
- **Kube-Hetzner module**: See [upstream repository](https://github.com/kube-hetzner/terraform-hcloud-kube-hetzner/issues)
- **Hetzner Cloud**: Contact [Hetzner support](https://docs.hetzner.com/)
