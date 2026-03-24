# Foremanctl Developer Guide

## Welcome to Foremanctl!

This guide is designed to help you understand the foremanctl project from a developer's perspective. Whether you're a new hire or a contributor, this document will walk you through the architecture, codebase structure, and development practices.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Repository Structure](#repository-structure)
4. [Technology Stack](#technology-stack)
5. [Development Environment Setup](#development-environment-setup)
6. [Key Components Deep Dive](#key-components-deep-dive)
7. [Code Paths and Flow](#code-paths-and-flow)
8. [Feature System](#feature-system)
9. [Testing](#testing)
10. [Development Workflows](#development-workflows)
11. [Adding New Features](#adding-new-features)
12. [Debugging and Troubleshooting](#debugging-and-troubleshooting)
13. [Release Process](#release-process)
14. [Contributing Guidelines](#contributing-guidelines)

---

## Project Overview

### What is Foremanctl?

Foremanctl is a modern deployment tool for Foreman and Katello that leverages containerization and automation to simplify server lifecycle management deployments.

### Key Goals

1. **Containerization**: Move from traditional package-based installation to container-based deployment
2. **Simplification**: Reduce complexity compared to the legacy Puppet-based `foreman-installer`
3. **Modularity**: Enable features on-demand through a flexible plugin system
4. **Modern Infrastructure**: Leverage Podman, systemd, and Ansible for a cloud-native approach

### Target Versions

- **Foreman**: 3.18
- **Katello**: 4.20
- **Pulp**: 3.85
- **Candlepin**: 4.6
- **Platform**: EL9 (CentOS Stream 9, RHEL 9)

### Project Principles

- **Convention over configuration**: Sensible defaults with override options
- **Idempotency**: Safe to run deployment multiple times
- **State persistence**: Remember user choices across deployments
- **Modular design**: Clear separation of concerns between components

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│  ┌──────────────┐              ┌──────────────┐            │
│  │  foremanctl  │              │    forge     │            │
│  │ (production) │              │ (development)│            │
│  └──────┬───────┘              └──────┬───────┘            │
│         │                             │                     │
│         └─────────────┬───────────────┘                     │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Obsah (Ansible Wrapper)                         │
│  - Playbook selection                                        │
│  - Parameter management                                      │
│  - State persistence                                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Ansible Playbooks                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   deploy     │  │pull-images   │  │   checks     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Ansible Roles                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │postgresql│ │  redis   │ │candlepin │ │  pulp    │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │ foreman  │ │  httpd   │ │  hammer  │                   │
│  └──────────┘ └──────────┘ └──────────┘                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Container Runtime (Podman)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Podman Quadlets (Systemd Service Units)             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ PostgreSQL  │  │   Redis     │  │  Candlepin  │        │
│  │ Container   │  │  Container  │  │  Container  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Pulp     │  │  Foreman    │  │   Apache    │        │
│  │  Container  │  │  Container  │  │  Container  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Flow

1. **User invokes `foremanctl deploy`**
2. **Obsah** parses parameters and selects playbook
3. **Ansible** executes deployment playbook with roles
4. **Roles** create Podman secrets and quadlet files
5. **Systemd** generates service units from quadlets
6. **Podman** pulls images and starts containers
7. **Services** initialize databases and start application

### Component Interactions

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  httpd   │────▶│ foreman  │────▶│postgresql│
│ (Apache) │     │  (Rails) │     │          │
└──────────┘     └────┬─────┘     └──────────┘
                      │
                 ┌────┼────┬─────────┐
                 ▼    ▼    ▼         ▼
            ┌─────┐ ┌────┐ ┌──────┐ ┌──────┐
            │redis│ │pulp│ │candlepin│ │dynflow│
            └─────┘ └────┘ └──────┘ └──────┘
```

**Data Flow:**
- **HTTP Request** → Apache (SSL termination) → Foreman (Rails app)
- **Foreman** → PostgreSQL (application data)
- **Foreman** → Redis (caching, job queues)
- **Foreman** → Candlepin (subscription management)
- **Foreman** → Pulp (content management)
- **Foreman** → Dynflow (background job processing)

---

## Repository Structure

```
foremanctl/
├── README.md                    # Basic project information
├── DEVELOPMENT.md               # Quick development guide
├── USER_GUIDE.md                # User documentation (comprehensive)
├── DEVELOPER_GUIDE.md           # This file
├── VERSION                      # Version number
├── Makefile                     # Build automation
├── Vagrantfile                  # VM configuration for testing
├── setup-environment            # Python virtualenv setup script
│
├── foremanctl                   # Production deployment entry point
├── forge                        # Development environment entry point
│
├── docs/                        # Additional documentation
│   ├── certificates.md          # Certificate management details
│   ├── deployment.md            # Deployment architecture
│   ├── development-environment.md  # Dev env details
│   ├── feature-metadata.md      # Feature system design
│   ├── parameters.md            # Parameter mapping
│   └── container-image-builds.md   # Container build info
│
├── src/                         # Production Ansible code
│   ├── ansible.cfg              # Ansible configuration
│   ├── features.yaml            # Feature definitions
│   │
│   ├── playbooks/               # Ansible playbooks
│   │   ├── deploy/              # Main deployment playbook
│   │   ├── pull-images/         # Image pulling playbook
│   │   ├── checks/              # Pre-deployment checks
│   │   └── _*/                  # Internal/helper playbooks
│   │
│   ├── roles/                   # Ansible roles (one per service)
│   │   ├── foreman/             # Foreman application
│   │   ├── postgresql/          # PostgreSQL database
│   │   ├── redis/               # Redis cache
│   │   ├── candlepin/           # Candlepin subscriptions
│   │   ├── pulp/                # Pulp content management
│   │   ├── httpd/               # Apache web server
│   │   ├── hammer/              # Hammer CLI
│   │   ├── foreman_proxy/       # Smart Proxy
│   │   ├── certificates/        # Certificate generation
│   │   ├── certificate_checks/  # Certificate validation
│   │   ├── checks/              # System checks
│   │   ├── pre_install/         # Pre-installation tasks
│   │   ├── post_install/        # Post-installation tasks
│   │   └── systemd_target/      # Systemd target creation
│   │
│   ├── vars/                    # Variable files
│   │   ├── base.yaml            # Base variables
│   │   ├── defaults.yml         # Default values
│   │   ├── database.yml         # Database configuration
│   │   ├── foreman.yml          # Foreman configuration
│   │   ├── images.yml           # Container image definitions
│   │   ├── default_certificates.yml  # Default cert paths
│   │   ├── installer_certificates.yml # Installer cert paths
│   │   ├── flavors/             # Flavor definitions
│   │   │   └── katello.yml      # Katello flavor
│   │   └── tuning/              # Tuning profiles
│   │       ├── development.yml  # Development tuning
│   │       ├── default.yml      # Default tuning
│   │       ├── medium.yml       # Medium tuning
│   │       └── large.yml        # Large tuning
│   │
│   └── filter_plugins/          # Custom Ansible filters
│       └── foremanctl.py        # Feature-to-plugin mapping
│
├── development/                 # Development environment code
│   ├── ansible.cfg              # Ansible config for dev
│   ├── requirements.txt         # Python dependencies
│   ├── requirements.yml         # Ansible collections
│   │
│   ├── playbooks/               # Development playbooks
│   │   ├── deploy-dev/          # Dev environment deployment
│   │   ├── vms/                 # VM management
│   │   ├── test/                # Test execution
│   │   ├── smoker/              # Smoker tests
│   │   └── setup-repositories/  # Repo setup
│   │
│   ├── roles/                   # Development-specific roles
│   │   ├── foreman_development/ # Foreman dev setup
│   │   ├── foreman_installer_certs/ # Cert handling
│   │   └── git_repository/      # Git repo cloning
│   │
│   └── scripts/
│       └── vagrant.py           # Vagrant inventory script
│
├── inventories/                 # Ansible inventories
│   ├── localhost                # Localhost inventory
│   └── broker.py                # Dynamic inventory
│
├── tests/                       # Test suite
│   ├── conftest.py              # Pytest configuration
│   ├── *_test.py                # Test modules (17 files)
│   ├── playbooks_test.py        # Playbook tests
│   └── fixtures/                # Test fixtures
│
├── .github/                     # GitHub configuration
│   └── workflows/               # CI/CD workflows
│       ├── test.yml             # Test workflow
│       └── release.yml          # Release workflow
│
└── .packit.yml                  # Packit configuration for COPR
```

### Key Files Explained

| File/Directory | Purpose |
|----------------|---------|
| `foremanctl` | Bash wrapper that sets environment variables and calls `obsah` for production deployments |
| `forge` | Bash wrapper for development environment (similar to foremanctl) |
| `src/features.yaml` | Defines all available features and their dependencies |
| `src/playbooks/deploy/deploy.yaml` | Main deployment orchestration playbook |
| `src/vars/images.yml` | Container image URLs and tags |
| `src/filter_plugins/foremanctl.py` | Python plugin for feature-to-plugin name translation |
| `tests/` | Pytest-based test suite for validation |

---

## Technology Stack

### Core Technologies

1. **Ansible** (ansible-core 2.14+)
   - Automation engine
   - Idempotent configuration management
   - Role-based organization

2. **Podman** (4.0+)
   - Daemonless container runtime
   - OCI-compliant
   - Systemd integration via quadlets

3. **Systemd**
   - Service lifecycle management
   - Dependency management
   - Automatic restart on failure

4. **Python** (3.9+)
   - Ansible filter plugins
   - Test framework (pytest)
   - Inventory scripts

5. **Obsah**
   - Ansible playbook wrapper
   - Parameter persistence
   - Playbook selection

### Container Images

All services run as containers:

- **Foreman**: Ruby on Rails application
- **PostgreSQL**: Database (or external)
- **Redis**: Cache and message broker
- **Candlepin**: Subscription management (Java/Tomcat)
- **Pulp**: Content management (Python/Django)
- **Apache httpd**: Reverse proxy and SSL termination

### Dependencies

**Ansible Collections:**
- `containers.podman`: Podman module support
- `theforeman.foreman`: Foreman resource management

**Python Packages:**
- `ansible-core`: Core Ansible
- `pytest`: Testing framework
- `pyyaml`: YAML parsing

---

## Development Environment Setup

### Prerequisites

1. **Host System**: Linux (Fedora/CentOS Stream/RHEL recommended)
2. **Vagrant**: 2.2+ (for VM creation)
3. **Vagrant Libvirt**: Vagrant provider plugin
4. **Ansible**: 2.14+
5. **Virtualization**: Enabled in BIOS

### Step 1: Clone Repository

```bash
git clone https://github.com/theforeman/foremanctl.git
cd foremanctl
```

### Step 2: Setup Python Environment

```bash
# Create virtual environment and install dependencies
./setup-environment

# Activate virtual environment
source .venv/bin/activate
```

This script:
- Creates a Python virtual environment in `.venv/`
- Installs `ansible-core` and dependencies
- Installs required Ansible collections

### Step 3: Start Development VM

```bash
# Start Vagrant VM
./forge vms start
```

This creates a CentOS Stream 9 VM using Vagrant/Libvirt.

### Step 4: Deploy Development Environment

```bash
# Deploy Foreman in development mode
./forge deploy-dev --foreman-initial-admin-password=changeme --tuning development
```

**What this does:**
- Clones Foreman repository from GitHub
- Sets up Ruby and Node.js environments
- Deploys containerized backend services
- Configures development server
- Seeds the database

### Step 5: Access Development Environment

```bash
# SSH into VM
vagrant ssh

# Navigate to Foreman
cd /home/vagrant/foreman

# Start Rails development server
bundle exec foreman start
```

Access at: `http://<hostname>:3000`

### Development VM Management

```bash
# Stop VM
./forge vms stop

# Destroy VM
./forge vms destroy

# Check VM status
vagrant status
```

---

## Key Components Deep Dive

### 1. Obsah (Deployment Orchestrator)

**Location**: External dependency (called by `foremanctl` and `forge`)

**Purpose**:
- Wraps Ansible playbook execution
- Manages parameter persistence
- Provides CLI interface

**Environment Variables Set by foremanctl:**

```bash
OBSAH_NAME=foremanctl              # Tool name
OBSAH_BASE=/path/to/foremanctl     # Base directory
OBSAH_DATA=${OBSAH_BASE}/src       # Playbook directory
OBSAH_INVENTORY=${OBSAH_BASE}/inventories  # Inventory location
OBSAH_STATE=${OBSAH_BASE}/.var/lib/foremanctl  # State persistence
OBSAH_PERSIST_PARAMS=true          # Save parameters
```

### 2. Features System

**File**: `src/features.yaml`

Defines modular features that can be enabled/disabled.

**Structure:**
```yaml
feature-name:
  description: Human-readable description
  internal: true/false  # User-visible or internal
  foreman:
    plugin_name: foreman_plugin_name
  foreman_proxy:
    plugin_name: proxy_plugin_name
  hammer: hammer_plugin_name
  dependencies:
    - other-feature
```

**Example:**
```yaml
remote-execution:
  description: Remote Execution plugin for Foreman
  foreman:
    plugin_name: foreman_remote_execution
  foreman_proxy:
    plugin_name: remote_execution_ssh
  dependencies:
    - dynflow
```

**Filter Plugin**: `src/filter_plugins/foremanctl.py`

Translates features to plugin names:

```python
def foreman_plugins(value):
    """Converts list of features to foreman plugin names"""
    dependencies = list(get_dependencies(filter_features(value)))
    plugins = [FEATURE_MAP.get(feature, {}).get('foreman', {}).get('plugin_name')
               for feature in filter_features(value + dependencies)]
    return compact_list(plugins)
```

**Usage in playbooks:**
```yaml
foreman_plugins: "{{ enabled_features | features_to_foreman_plugins }}"
```

### 3. Ansible Roles

Each service has a dedicated role following a consistent structure:

**Standard Role Structure:**
```
role_name/
├── tasks/
│   └── main.yaml          # Main task list
├── templates/             # Jinja2 templates
│   ├── config.yaml.j2     # Configuration files
│   └── service.conf.j2
├── defaults/
│   └── main.yaml          # Default variables
├── handlers/
│   └── main.yaml          # Service restart handlers
└── README.md              # Role documentation
```

**Example: foreman role** (`src/roles/foreman/tasks/main.yaml`)

Key tasks:
1. Pull container image
2. Create Podman secrets (database URL, admin credentials, certificates)
3. Deploy Foreman container as quadlet
4. Deploy Dynflow worker containers
5. Run database migrations
6. Start services
7. Wait for service health
8. Configure Pulp proxy integration

### 4. Podman Quadlets

**What are quadlets?**
- Systemd service units generated from container specifications
- Stored in `/etc/containers/systemd/`
- Automatically converted to systemd services

**Example quadlet creation:**
```yaml
- name: Deploy Foreman Container
  containers.podman.podman_container:
    name: "foreman"
    image: "{{ foreman_container_image }}:{{ foreman_container_tag }}"
    state: quadlet
    sdnotify: true
    network: host
    secrets:
      - 'foreman-database-url,type=env,target=DATABASE_URL'
    quadlet_options:
      - |
        [Install]
        WantedBy=default.target foreman.target
```

This generates `/etc/containers/systemd/foreman.container`, which systemd converts to `foreman.service`.

### 5. Podman Secrets

Configuration stored as Podman secrets instead of files on disk.

**Create secret:**
```yaml
- name: Create secret for DATABASE_URL
  containers.podman.podman_secret:
    state: present
    name: foreman-database-url
    data: "postgresql://user:pass@host:5432/db"
```

**Mount in container:**
```yaml
secrets:
  - 'foreman-database-url,type=env,target=DATABASE_URL'  # As env var
  - 'foreman-settings-yaml,type=mount,target=/etc/foreman/settings.yaml'  # As file
```

**View secrets:**
```bash
podman secret ls
podman secret inspect --showsecret foreman-database-url
```

### 6. Systemd Target

**File**: Created by `systemd_target` role

All services belong to `foreman.target`:

```ini
[Unit]
Description=Foreman Service Target
Wants=foreman.service
Wants=foreman-postgresql.service
Wants=foreman-redis.service
# ... other services

[Install]
WantedBy=multi-user.target
```

**Benefits:**
- Start/stop all services together: `systemctl start foreman.target`
- Dependency management
- Organized service grouping

---

## Code Paths and Flow

### Deployment Flow (foremanctl deploy)

```
1. User executes: foremanctl deploy --foreman-initial-admin-password=changeme
   ↓
2. foremanctl script sets environment variables
   ↓
3. Calls: obsah deploy
   ↓
4. Obsah determines playbook: src/playbooks/deploy/deploy.yaml
   ↓
5. Ansible loads variables:
   - src/vars/defaults.yml
   - src/vars/flavors/katello.yml (for flavor)
   - src/vars/default_certificates.yml (for certificate_source)
   - src/vars/images.yml (container images)
   - src/vars/tuning/development.yml (for tuning profile)
   - src/vars/database.yml
   - src/vars/foreman.yml
   - src/vars/base.yaml
   ↓
6. Execute roles in order:
   - pre_install: Basic system setup
   - checks: System requirement validation
   - certificates: Generate SSL certificates (if default source)
   - certificate_checks: Validate certificates exist and are valid
   - postgresql: Deploy PostgreSQL (if internal database)
   - redis: Deploy Redis
   - candlepin: Deploy Candlepin
   - httpd: Deploy Apache
   - pulp: Deploy Pulp
   - foreman: Deploy Foreman
   - systemd_target: Create foreman.target
   - foreman_proxy: Deploy Smart Proxy (if feature enabled)
   - hammer: Deploy Hammer CLI (if feature enabled)
   - post_install: Post-deployment tasks
   ↓
7. Each role:
   - Pulls container images
   - Creates Podman secrets
   - Creates quadlet files in /etc/containers/systemd/
   - Systemd daemon-reload
   - Starts services
   ↓
8. Foreman role runs database migrations
   ↓
9. Services start and become available
   ↓
10. Post-install validation checks
```

### Feature Resolution Flow

When user specifies `--add-feature=remote_execution`:

```
1. Feature name added to enabled_features list
   ↓
2. Filter plugin processes: enabled_features | features_to_foreman_plugins
   ↓
3. foremanctl.py:foreman_plugins() function:
   a. Filter out base features (foreman, hammer, foreman-proxy)
   b. Filter out content/* features
   c. Get dependencies for remote_execution: [dynflow]
   d. Recursively resolve all dependencies
   e. Extract plugin_name from features.yaml:
      - remote_execution → foreman_remote_execution
      - dynflow → (none for foreman, only foreman_proxy)
   f. Return list: ['foreman_remote_execution']
   ↓
4. Variable foreman_plugins set to ['katello', 'foreman_remote_execution', ...]
   ↓
5. Foreman container env var: FOREMAN_ENABLED_PLUGINS="katello foreman_remote_execution"
   ↓
6. Foreman container loads these plugins on startup
```

### Database Connection Flow

**Internal Database:**
```
1. postgresql role creates PostgreSQL container
2. Creates databases: foreman, candlepin, pulp
3. Each service role creates database URL secret:
   foreman-database-url: postgresql://foreman:password@localhost:5432/foreman
4. Services connect to localhost:5432
```

**External Database:**
```
1. User provides: --database-mode=external --database-host=db.example.com
2. postgresql role skipped (when: database_mode == 'internal')
3. Each service role creates database URL with external host:
   foreman-database-url: postgresql://foreman:password@db.example.com:5432/foreman
4. Services connect to external database
```

---

## Feature System

### Overview

The feature system allows modular composition of Foreman functionality.

### Feature Categories

1. **Base Features** (always present, not user-selectable):
   - `foreman`: Main Foreman server
   - `foreman-proxy`: Smart Proxy
   - `hammer`: CLI tool

2. **User Features** (user can enable):
   - `katello`: Content management
   - `remote-execution`: Remote command execution
   - `ansible`: Ansible integration
   - `discovery`: Bare-metal discovery
   - `openscap`: Security compliance
   - etc.

3. **Internal Features** (automatically enabled as dependencies):
   - `dynflow`: Background job processing
   - `foreman-tasks`: Task management

4. **Content Features** (specialized content types):
   - `content/rpm`: RPM repositories
   - `content/container`: Container images

### Feature Definition Example

```yaml
katello:
  description: Content and Subscription Management plugin for Foreman
  foreman:
    plugin_name: katello
  dependencies:
    - foreman-tasks

foreman-tasks:
  internal: true
  foreman:
    plugin_name: foreman-tasks
  hammer: foreman_tasks
  dependencies:
    - dynflow

dynflow:
  internal: true
  foreman_proxy:
    plugin_name: dynflow
```

### Dependency Resolution

Dependencies are resolved recursively:

```python
def get_dependencies_for_feature(feature):
    dependencies = set()
    for dependency in FEATURE_MAP.get(feature, {}).get('dependencies', []):
        if dependency not in dependencies:
            dependencies.update(get_dependencies_for_feature(dependency))
        dependencies.add(dependency)
    return dependencies
```

**Example**: Enabling `katello` automatically enables:
- `foreman-tasks` (direct dependency)
- `dynflow` (dependency of foreman-tasks)

### Adding a New Feature

1. **Define in src/features.yaml:**
   ```yaml
   my-new-feature:
     description: My awesome new feature
     foreman:
       plugin_name: foreman_my_feature
     foreman_proxy:
       plugin_name: smart_proxy_my_feature
     hammer: hammer_cli_foreman_my_feature
     dependencies:
       - some-other-feature
   ```

2. **No code changes needed** - the filter plugin handles conversion automatically

3. **Test deployment:**
   ```bash
   foremanctl deploy --add-feature=my-new-feature
   ```

4. **Verify plugin loaded:**
   ```bash
   podman exec foreman foreman-rake plugin:list
   ```

---

## Testing

### Test Structure

Tests are located in `tests/` directory with 17 test modules:

```
tests/
├── conftest.py                   # Pytest fixtures and configuration
├── candlepin_test.py             # Candlepin service tests
├── certificates_test.py          # Certificate generation tests
├── client_test.py                # Client functionality tests
├── foreman_test.py               # Foreman service tests
├── foreman_api_test.py           # Foreman API tests
├── foreman_compute_resources_test.py  # Compute resource tests
├── foreman_plugins_test.py       # Plugin tests
├── foreman_proxy_test.py         # Smart Proxy tests
├── foreman_target_test.py        # Systemd target tests
├── hammer_test.py                # Hammer CLI tests
├── httpd_test.py                 # Apache tests
├── playbooks_test.py             # Playbook validation tests
├── postgresql_test.py            # PostgreSQL tests
├── pulp_test.py                  # Pulp tests
├── redis_test.py                 # Redis tests
└── fixtures/                     # Test fixtures
```

### Running Tests

**Prerequisites:**
1. Active deployment (VM must be running and deployed)

**Run all tests:**
```bash
./forge test
```

**Run specific test module:**
```bash
pytest tests/foreman_test.py -v
```

**Run specific test:**
```bash
pytest tests/foreman_test.py::test_foreman_service_running -v
```

### Test Categories

1. **Service Tests**: Verify containers are running and healthy
   ```python
   def test_foreman_service_running(host):
       service = host.service("foreman")
       assert service.is_running
       assert service.is_enabled
   ```

2. **API Tests**: Validate Foreman API endpoints
   ```python
   def test_foreman_api_ping(foreman):
       response = foreman.get('/api/v2/ping')
       assert response.status_code == 200
   ```

3. **Configuration Tests**: Verify correct configuration
   ```python
   def test_database_connection(host):
       cmd = host.run("podman exec foreman rails runner 'puts ActiveRecord::Base.connection.active?'")
       assert "true" in cmd.stdout
   ```

4. **Integration Tests**: End-to-end workflows
   ```python
   def test_create_organization(foreman):
       org = foreman.create_organization(name="Test Org")
       assert org['name'] == "Test Org"
   ```

### Smoker Tests

[Smoker](https://github.com/theforeman/smoker) provides additional integration testing:

```bash
./forge smoker
```

Smoker tests include:
- Complete workflows (create org, upload content, etc.)
- Multi-step scenarios
- Real-world usage patterns

### Writing New Tests

**Example test file:**

```python
# tests/my_feature_test.py
import pytest

def test_my_feature_enabled(host):
    """Verify my feature plugin is loaded"""
    cmd = host.run(
        "podman exec foreman foreman-rake plugin:list | grep my_feature"
    )
    assert cmd.exit_status == 0

def test_my_feature_api(foreman):
    """Test my feature API endpoint"""
    response = foreman.get('/api/v2/my_feature')
    assert response.status_code == 200
    assert 'my_feature' in response.json()

@pytest.mark.skipif("not config.getoption('--enable-my-feature')")
def test_my_feature_advanced(foreman):
    """Advanced test only when feature enabled"""
    # Test implementation
    pass
```

### Test Fixtures

Common fixtures in `conftest.py`:

```python
@pytest.fixture
def host():
    """Testinfra host connection"""
    return testinfra.get_host('ssh://vagrant@hostname')

@pytest.fixture
def foreman():
    """Foreman API client"""
    return ForemanClient(
        url='https://hostname',
        username='admin',
        password='changeme'
    )
```

---

## Development Workflows

### Making Changes to Roles

**Workflow:**

1. **Modify role tasks/templates:**
   ```bash
   vim src/roles/foreman/tasks/main.yaml
   ```

2. **Test locally in development VM:**
   ```bash
   ./forge deploy-dev
   ```

3. **Verify changes:**
   ```bash
   vagrant ssh
   systemctl status foreman.service
   ```

4. **Run tests:**
   ```bash
   ./forge test
   ```

5. **Commit changes:**
   ```bash
   git add src/roles/foreman/
   git commit -m "Fix: Update foreman configuration"
   ```

### Adding New Role

**Steps:**

1. **Create role structure:**
   ```bash
   mkdir -p src/roles/mynewservice/{tasks,templates,defaults,handlers}
   ```

2. **Create main task file:**
   ```bash
   vim src/roles/mynewservice/tasks/main.yaml
   ```

3. **Add to deployment playbook:**
   ```yaml
   # src/playbooks/deploy/deploy.yaml
   roles:
     - mynewservice
   ```

4. **Create tests:**
   ```bash
   vim tests/mynewservice_test.py
   ```

5. **Test and iterate**

### Debugging Deployment Issues

**Check Ansible logs:**
```bash
tail -f .var/lib/foremanctl/foremanctl.log
```

**Re-run deployment with verbose output:**
```bash
ANSIBLE_STDOUT_CALLBACK=debug foremanctl deploy
```

**Check specific service:**
```bash
systemctl status foreman.service
journalctl -u foreman.service -f
```

**Inspect container:**
```bash
podman exec -it foreman bash
```

**Check secrets:**
```bash
podman secret ls
podman secret inspect --showsecret foreman-settings-yaml
```

### Development Environment Customization

**Enable additional plugins:**
```bash
./forge deploy-dev \
  --foreman-development-enabled-plugin katello \
  --foreman-development-enabled-plugin foreman_ansible \
  --foreman-development-enabled-plugin foreman_discovery
```

**Deploy with features:**
```bash
./forge deploy-dev \
  --add-feature hammer \
  --add-feature foreman-proxy
```

**Target remote host:**
```bash
./forge deploy-dev --target-host=my-server.example.com
```

---

## Adding New Features

### Step-by-Step Guide

#### 1. Define Feature in features.yaml

```yaml
# src/features.yaml
my_awesome_feature:
  description: My Awesome Feature for Foreman
  foreman:
    plugin_name: foreman_my_awesome
  foreman_proxy:
    plugin_name: smart_proxy_my_awesome
  hammer: hammer_cli_foreman_my_awesome
  dependencies:
    - some_dependency_feature
```

#### 2. (Optional) Add Feature-Specific Role Tasks

If the feature requires additional setup beyond just enabling the plugin:

```bash
mkdir -p src/roles/foreman/tasks/feature/
vim src/roles/foreman/tasks/feature/foreman_my_awesome.yaml
```

```yaml
---
- name: Configure my awesome feature
  containers.podman.podman_secret:
    state: present
    name: foreman-my-awesome-config
    data: "{{ lookup('ansible.builtin.template', 'my_awesome.yaml.j2') }}"
```

#### 3. Add Configuration Template (if needed)

```bash
vim src/roles/foreman/templates/my_awesome.yaml.j2
```

```yaml
---
:my_awesome:
  :enabled: true
  :setting1: {{ my_awesome_setting1 }}
```

#### 4. Add Default Variables

```bash
vim src/roles/foreman/defaults/main.yaml
```

```yaml
my_awesome_setting1: "default_value"
```

#### 5. Create Tests

```bash
vim tests/my_awesome_test.py
```

```python
import pytest

def test_my_awesome_plugin_enabled(host):
    cmd = host.run("podman exec foreman foreman-rake plugin:list | grep my_awesome")
    assert cmd.exit_status == 0

def test_my_awesome_api_endpoint(foreman):
    response = foreman.get('/api/v2/my_awesome')
    assert response.status_code == 200
```

#### 6. Document the Feature

Add to `docs/feature-metadata.md` or relevant documentation.

#### 7. Test Deployment

```bash
foremanctl deploy --add-feature=my_awesome_feature
```

#### 8. Verify

```bash
# Check plugin loaded
podman exec foreman foreman-rake plugin:list

# Run tests
pytest tests/my_awesome_test.py -v
```

---

## Debugging and Troubleshooting

### Common Development Issues

#### Issue: Ansible playbook fails

**Debug steps:**

1. Check Ansible log:
   ```bash
   cat .var/lib/foremanctl/foremanctl.log
   ```

2. Run with increased verbosity:
   ```bash
   ansible-playbook -vvv src/playbooks/deploy/deploy.yaml
   ```

3. Check specific task:
   ```bash
   ansible-playbook src/playbooks/deploy/deploy.yaml --start-at-task="Create secret for DATABASE_URL"
   ```

#### Issue: Container fails to start

**Debug steps:**

1. Check systemd service status:
   ```bash
   systemctl status foreman.service
   journalctl -u foreman.service -n 100
   ```

2. Check container logs:
   ```bash
   podman logs foreman
   ```

3. Inspect container:
   ```bash
   podman inspect foreman
   ```

4. Try manual container run:
   ```bash
   podman run -it --rm --entrypoint=/bin/bash <image>
   ```

#### Issue: Database migration fails

**Debug steps:**

1. Check database connectivity:
   ```bash
   podman exec foreman rails runner 'puts ActiveRecord::Base.connection.active?'
   ```

2. Check migration status:
   ```bash
   podman exec foreman foreman-rake db:migrate:status
   ```

3. Run migration manually:
   ```bash
   podman exec foreman foreman-rake db:migrate
   ```

4. Check database logs:
   ```bash
   podman logs foreman-postgresql
   ```

#### Issue: Feature not loading

**Debug steps:**

1. Verify feature in enabled list:
   ```bash
   podman exec foreman printenv FOREMAN_ENABLED_PLUGINS
   ```

2. Check plugin actually loads:
   ```bash
   podman exec foreman foreman-rake plugin:list
   ```

3. Check feature definition:
   ```bash
   cat src/features.yaml | grep -A 10 "my-feature"
   ```

4. Test filter plugin:
   ```python
   python3 << EOF
   import sys
   sys.path.insert(0, 'src/filter_plugins')
   from foremanctl import foreman_plugins

   enabled_features = ['foreman', 'katello', 'my-feature']
   print(foreman_plugins(enabled_features))
   EOF
   ```

### Debugging Tools

**Ansible debugging:**
```yaml
- name: Debug variable
  ansible.builtin.debug:
    var: my_variable
    verbosity: 0
```

**Container debugging:**
```bash
# Enter running container
podman exec -it foreman bash

# Check environment variables
podman exec foreman env

# Check mounted secrets
podman exec foreman ls -la /etc/foreman/

# Check processes
podman exec foreman ps aux
```

**Database debugging:**
```bash
# Connect to PostgreSQL
podman exec -it foreman-postgresql psql -U postgres

# Check foreman database
\c foreman
\dt
SELECT * FROM settings LIMIT 10;
```

### Performance Debugging

**Check resource usage:**
```bash
podman stats

systemctl status foreman.target
```

**Check database pool exhaustion:**
```bash
podman exec foreman foreman-rake db:pool:status
```

**Check Pulp workers:**
```bash
systemctl status foreman-pulpcore-worker@*.service
```

---

## Release Process

### Versioning

Version stored in `VERSION` file (uses git describe format).

### Release Steps

1. **Update VERSION file:**
   ```bash
   echo "3.18.0" > VERSION
   ```

2. **Update RELEASE.md with changelog**

3. **Commit and tag:**
   ```bash
   git add VERSION RELEASE.md
   git commit -m "Release 3.18.0"
   git tag v3.18.0
   git push origin master v3.18.0
   ```

4. **GitHub Actions automatically:**
   - Runs tests (`.github/workflows/test.yml`)
   - Builds RPM package
   - Publishes to COPR (`.github/workflows/release.yml`)

5. **Packit integration:**
   - Configured in `.packit.yml`
   - Automatically submits to `@theforeman/foremanctl` COPR
   - Builds for EL9

### COPR Repository

Packages published to:
```
https://copr.fedorainfracloud.org/coprs/g/theforeman/foremanctl/
```

Users install via:
```bash
dnf copr enable @theforeman/foremanctl rhel-9-x86_64
dnf install foremanctl
```

---

## Contributing Guidelines

### Code Style

**Ansible:**
- Use YAML anchors for reuse
- Keep playbooks under 300 lines
- Use roles for modularity
- Follow ansible-lint recommendations

**Python:**
- PEP 8 style guide
- Type hints where applicable
- Docstrings for public functions

### Commit Messages

Follow conventional commits:

```
feat: Add support for external Redis
fix: Correct certificate path in httpd role
docs: Update deployment architecture diagram
test: Add tests for hammer CLI
refactor: Simplify feature dependency resolution
```

### Pull Request Process

1. **Fork repository**
2. **Create feature branch:**
   ```bash
   git checkout -b feature/my-new-feature
   ```

3. **Make changes and commit**

4. **Run tests locally:**
   ```bash
   ./forge test
   ```

5. **Push to fork:**
   ```bash
   git push origin feature/my-new-feature
   ```

6. **Create pull request on GitHub**

7. **Address review feedback**

8. **Merge after approval**

### Testing Requirements

All PRs must:
- Pass existing tests
- Add tests for new functionality
- Not decrease test coverage

### Documentation Requirements

Update documentation when:
- Adding new features
- Changing user-facing behavior
- Modifying architecture
- Adding new parameters

---

## Appendix

### Useful Commands Reference

```bash
# Development
./setup-environment                    # Setup Python venv
source .venv/bin/activate              # Activate venv
./forge vms start                      # Start dev VM
./forge deploy-dev                     # Deploy dev environment
./forge test                           # Run tests
./forge smoker                         # Run smoker tests

# Deployment
foremanctl deploy                      # Deploy production
foremanctl pull-images                 # Pull images only
foremanctl checks                      # Run checks only

# Service Management
systemctl status foreman.target        # Check all services
systemctl start foreman.target         # Start all services
systemctl stop foreman.target          # Stop all services
systemctl restart foreman.service      # Restart specific service

# Container Management
podman ps                              # List containers
podman logs foreman                    # View logs
podman exec -it foreman bash           # Enter container
podman secret ls                       # List secrets
podman secret inspect --showsecret NAME  # View secret

# Debugging
journalctl -u foreman.service -f       # Follow service logs
cat .var/lib/foremanctl/foremanctl.log # Ansible log
podman inspect foreman                 # Container details
systemctl cat foreman.service          # View systemd unit
```

### Architecture Diagrams

See `docs/deployment.md` for additional architecture details.

### Related Projects

- **Foreman**: https://github.com/theforeman/foreman
- **Katello**: https://github.com/Katello/katello
- **Pulp**: https://github.com/pulp/pulpcore
- **Candlepin**: https://github.com/candlepin/candlepin
- **Foreman Ansible Modules**: https://github.com/theforeman/foreman-ansible-modules

### Getting Help

- **GitHub Issues**: https://github.com/theforeman/foremanctl/issues
- **Community Forum**: https://community.theforeman.org/
- **IRC**: #theforeman on Libera.Chat
- **Documentation**: https://theforeman.org/documentation.html

---

**Happy Coding!**

This guide is a living document. If you find issues or have suggestions for improvement, please open a pull request or issue on GitHub.

**Last Updated**: 2026-03-23
**Version**: For Foreman 3.18 / foremanctl
