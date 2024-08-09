# Quadlet Testing

This repository is testing a deployment of Foreman and Katello using Podman quadlet's and Ansible.

## Deployment

This setup usess Vagrant to create a basic VM for running the deployment on:

```
vagrant up quadlet
ansible-playbook playbooks/setup.yaml
ansible-playbook playbooks/deploy.yaml
```


## Testing

To run tests:

Ensure you have a deployment
```
vagrant up quadlet
ansible-playbook playbooks/setup.yaml
ansible-playbook playbooks/deploy.yaml
```

Now run the tests:

```
./run_tests
```
