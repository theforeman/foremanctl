# Foreman Documentation Review: Migration to foremanctl and Containers

## Review Overview
**Purpose**: Identify documentation changes needed for the migration from traditional Foreman deployment to foremanctl and containerized deployment.

**Review Date**: 2025-11-03
**Target**: [theforeman/foremanctl](https://github.com/theforeman/foremanctl)

---

## Key Areas of Focus

### 1. Installation Methods
- **Traditional Installation** → **foremanctl Installation**
- **Package-based Deployment** → **Container-based Deployment**
- **Manual Configuration** → **Automated Container Orchestration**

### 2. Configuration Management
- **File-based Configuration** → **Container Environment Variables**
- **Service Management** → **Container Lifecycle Management**
- **Database Setup** → **Containerized Database Services**

### 3. Administrative Procedures
- **System-level Administration** → **Container-level Administration**
- **Service Troubleshooting** → **Container Troubleshooting**
- **Performance Tuning** → **Container Resource Management**

---

## Critical Design Decisions Required for foremanctl

### **1. Feature Support Design Decisions**

**Note 8: Red Hat Lightspeed Client Integration**
- **Design Decision Required**: Whether foremanctl will support Red Hat Lightspeed client integration at all
- Container architecture may affect how insights-client operates and integrates

**Note 10: Pull-based Transport for Remote Execution**
- **Design Decision Pending**: Awaiting completion of feature design work per [foremanctl PR #188](https://github.com/theforeman/foremanctl/pull/188)
- Need to determine MQTT broker implementation in containerized architecture

**Note 11: Power Management (BMC)**
- **Design Decision Required**: Awaiting BMC feature design definition for foremanctl
- BMC functionality requires low-level hardware access which may be affected by containerization

### **2. Infrastructure and Architecture Design Decisions**

**Note 7: External Database Integration**
- **Design Decision Pending**: External database support is still being designed for foremanctl
- Need to finalize external database configuration approaches
- https://github.com/theforeman/foremanctl/pull/141

**Note 12: Outgoing Email Configuration**
- **Design Decision Required**: Not sure at this time how container-based design affects SMTP integration
- Need to determine if SMTP configuration is handled at container level or host level

**Note 13: Identity Management Realm Integration**
- **Design Decision Required**: Updates needed based on design of how FreeIPA realm integration is handled in foremanctl
- Complex host-level authentication and certificate management in containerized environment

**Note 15: DHCP and DNS Configuration Management**
- **Design Need Identified**: Critical need to design how DHCP and DNS configuration files will be managed in foremanctl
- Need to determine configuration approach:
  - Container environment variables
  - Configuration file volume mounts
  - Container orchestration configuration management
  - Other containerized configuration approaches

### **3. Certificate and Security Design Decisions**

Tracker: https://github.com/theforeman/foremanctl/issues/297

**Note 14: SSL Certificate Management**
- **Design Decision Required**: Complete re-review of all SSL certificate procedures based on foremanctl design
- Certificate mounting, volume management, and container security contexts need design decisions

**Note 19: Capsule SSL Certificates**
- **Design Decision Required**: Update based on foremanctl design for handling certificates with containerized Smart Proxy architecture
- Distributed certificate management across containerized Smart Proxy infrastructure

### **4. Feature Enhancement Design Decisions**

**Note 17: Container Export/Import for Core Installation**
- **Design Decision Required**: Add script or functionality into foremanctl to automate container export/import process
- Built-in functionality preferred over manual procedures

**Note 18: Capsule Container Image Distribution**
- **Design Decision Required**: Design foremanctl element to help with pulling container images from Satellite during Capsule install
- Consider automated registration assistance to get Capsule repositories from Satellite

### **5. Load Balancing Architecture Design Decisions**

**Note 20: Container-Native Load Balancing**
- **Design Decision Required**: Fundamental architecture redesign for container-native load balancing
- Evaluate container orchestration platforms for native load balancing vs. external load balancers
- Service mesh considerations for inter-container communication

### **Summary of Critical Design Areas**

1. **Feature Compatibility**: Which traditional features will be supported in containerized foremanctl
2. **Configuration Management**: How configuration will be managed in container environment
3. **Certificate Management**: How SSL certificates will be handled in distributed container architecture
4. **Service Integration**: How external services (SMTP, DHCP, DNS, Identity Management) will integrate
5. **Infrastructure Architecture**: Container-native vs. traditional approaches for load balancing, networking, storage

These design decisions represent the most critical architectural and functional choices that must be made during foremanctl development to guide the documentation updates effectively.

---

## Review Notes

### Installation Documentation

#### Note 1:
**Topic**: System User Account Requirements for Container Migration
**Current State**: Traditional Foreman installation creates and manages specific system user accounts on the host system. The current system requirements specify conflicts with external identity providers for these user accounts:
- `apache` (or `httpd`)
- `foreman`
- `foreman-proxy`
- `postgres`
- `pulp`
- `puppet`
- `redis`
- `tomcat`

**Required Changes**:
- Review how these user accounts are handled in containerized deployment
- Determine which users are needed on the container host vs. inside containers
- Update documentation to reflect container-specific user management
- Address UID/GID mapping between containers and host system
- Review security implications of user namespace mapping

**Impact Level**: High
**Affected Files**:
- `guides/common/modules/ref_system-requirements.adoc:61-78`
- All installation guides that reference user creation
- Security and permission documentation

**Additional Considerations**: Container deployment may eliminate the need for some system users on the host, but requires careful consideration of container security contexts and volume mounting permissions.

---

### Configuration Documentation

#### Note 2:
**Topic**: Storage Requirements Changes for Container Deployment
**Current State**: Traditional Foreman installation has specific storage requirements:
- `/usr` - 10 GB (Installation Size), Not Applicable (Runtime)
- `/opt/puppetlabs` - 500 MB (Installation Size), Not Applicable (Runtime)
- `/var/lib/containers` - 20 GB (Installation), 30 GB (Runtime) - only listed for {insights-iop}
- `/var/lib/pulp` - 1 MB (Installation), 300 GB (Runtime)
- `/var/log` - 10 MB (Installation), 10 GB (Runtime)
- `/var/lib/postgresql` - 1 GB (Installation), 20 GB (Runtime)

**Required Changes**:
- **Increase** `/var/lib/containers` storage requirements significantly for full containerized deployment
- **Review and likely remove** `/usr` requirement (10 GB) as containers package their own userspace
- **Remove** `/opt/puppetlabs` requirement (500 MB) as Puppet will be containerized
- **Update** the storage requirements table to reflect container-first deployment
- **Add** container-specific storage considerations and volume mount requirements

**Impact Level**: High
**Affected Files**:
- `guides/common/modules/ref_storage-requirements.adoc:19` (/usr requirement)
- `guides/common/modules/ref_storage-requirements.adoc:21` (/opt/puppetlabs requirement)
- `guides/common/modules/ref_storage-requirements.adoc:28` (/var/lib/containers requirement)
- All installation guides that reference storage planning

**Additional Considerations**: Container deployment fundamentally changes storage patterns - containers store images, layers, and runtime data in `/var/lib/containers`, while traditional filesystem requirements like `/usr` and `/opt/puppetlabs` become irrelevant. Need to establish new baseline storage requirements for foremanctl deployment.

**Additional /tmp Considerations for Container Migration**:
- Current requirement: `/tmp` must be mounted with `exec` option for `puppetserver` service to work
- Container operations use `/tmp` for image imports/exports (e.g., `skopeo copy oci-archive:/tmp/${name}.tar`)
- Dynamic partitioning creates `/tmp/diskpart.cfg` during provisioning
- SOS reports stored in `/var/tmp/`
- Container deployment may change how `/tmp` is used - containers may handle executable operations internally
- Need to review if host `/tmp` exec requirement still applies with containerized Puppet

---

### Administrative Documentation

#### Note 3:
**Topic**: Chapter 3.1 Step 1 - DHCP Capsule Ping Configuration Evaluation
**Current State**: The "Opening required ports" procedure includes optional step to disable DHCP ping functionality:
- `# {foreman-installer} --foreman-proxy-dhcp-ping-free-ip false`
- By default, DHCP {SmartProxy} performs ICMP ping and TCP echo connection attempts to check if IP addresses are free
- This is used in subnets with DHCP IPAM to find available IP addresses
- Firewall requirements include ICMP ping for "Free IP checking (optional)"

**Required Changes**:
- Review if this functionality works the same way in containerized DHCP proxy
- Verify that container networking allows ICMP ping operations from containers
- Update firewall requirements if container networking changes ping behavior
- Clarify if foremanctl deployment affects DHCP IP address checking mechanism
- Test DHCP IPAM functionality in container environment

**Impact Level**: Medium
**Affected Files**:
- `guides/common/modules/proc_opening-required-ports.adoc:21-28`
- `guides/common/modules/ref_project-server-port-and-firewall-requirements.adoc:54`
- `guides/common/modules/ref_smart-proxy-port-and-firewall-requirements.adoc:54`

**Additional Considerations**: Container networking may affect how DHCP proxy components can perform ICMP ping operations to check IP availability. Need to verify that containerized services can still perform network discovery functions.

---

#### Note 4:
**Topic**: Chapter 3.1 Step 3 - Drop Puppetmaster Firewall Service
**Current State**: The "Opening required ports" procedure includes puppetmaster as a required firewall service:
- Firewall configuration: `--add-service=puppetmaster`
- Listed alongside dns, dhcp, tftp, http, https services
- Required for traditional Puppet server communication
- References deprecated `@host.puppetmaster` variable (should use `host_puppet_server`)

**Required Changes**:
- **Remove** `--add-service=puppetmaster` from firewall configuration steps
- Update firewall documentation to reflect containerized Puppet architecture
- Remove references to traditional puppetmaster service
- Update any remaining `@host.puppetmaster` variable references to `host_puppet_server`
- Clarify new container networking requirements for Puppet communication

**Impact Level**: High
**Affected Files**:
- `guides/common/modules/proc_opening-required-ports.adoc:62`
- `guides/common/modules/ref_example-template-snippets.adoc:16`
- `guides/common/modules/ref_host-specific-variables.adoc:58`
- All firewall configuration procedures referencing puppetmaster

**Additional Considerations**: With Puppet containerized in foremanctl, the traditional puppetmaster service and associated firewall rules become obsolete. Container networking will handle Puppet communication differently, potentially requiring new port/service configurations.

---

#### Note 5:
**Topic**: Chapter 4 - Tuning Satellite Server - Complete Section Requires Future Evaluation
**Current State**: The entire "Tuning Performance" documentation (`doc-Tuning_Performance/master.adoc`) provides traditional server-based performance optimization guidance covering:
- Puma server tunings (Ruby application server for Foreman requests)
- Apache httpd performance tuning
- Dynflow tuning (background job processing)
- Pull-based remote execution transport tuning
- PostgreSQL database tuning (via `/etc/foreman-installer/custom-hiera.yaml`)
- Redis tuning
- Smart proxy configuration tuning
- Hardware and OS configuration recommendations
- System requirements for tuning

**Required Changes**:
- **Complete re-evaluation** of entire Chapter 4 for container deployment architecture
- **Replace** traditional server tuning with container resource management guidance
- **Update** database tuning approaches for containerized PostgreSQL
- **Revise** application server tuning for containerized Puma
- **Add** container-specific performance optimization (CPU limits, memory limits, resource requests)
- **Update** scaling guidance for container orchestration
- **Replace** foreman-installer configuration with foremanctl configuration methods
- **Add** container monitoring and performance metrics guidance

**Impact Level**: High
**Affected Files**:
- `guides/doc-Tuning_Performance/master.adoc` (entire document)
- `guides/common/assembly_configuring-project-for-performance.adoc`
- `guides/common/modules/con_puma-tunings.adoc`
- `guides/common/modules/con_apache-httpd-performance-tuning.adoc`
- `guides/common/modules/con_postgresql-tuning.adoc`
- `guides/common/modules/con_redis-tuning.adoc`
- `guides/common/modules/con_smart-proxy-configuration-tuning.adoc`
- All related tuning procedure modules

**Additional Considerations**: Traditional server performance tuning becomes largely obsolete with containerization. The entire paradigm shifts from OS-level service tuning to container resource management, orchestration scaling, and container-specific optimization strategies. This represents one of the most comprehensive documentation overhauls needed for the foremanctl migration.

---

#### Note 6:
**Topic**: Chapter 5 - Drop Puppet References and Update Installer Commands
**Current State**: Multiple Puppet references and traditional installer commands throughout Chapter 5 (Administering Project) documentation:
- Puppet references in load balancer configurations (`assembly_configuring-smartproxyservers-with-*-puppet.adoc`)
- Puppet integration documentation (`doc-Managing_Configurations_Puppet`)
- Puppet run restoration procedures (`proc_restoring-manual-changes-overwritten-by-a-puppet-run.adoc`)
- Puppet server references in provisioning diagrams
- SCAP content deployment using Puppet (`proc_propagating-scap-content-using-puppet-deployment.adoc`)

**Required Changes**:
- **Drop** all Puppet-specific references from Chapter 5 administration procedures
- **Remove** Puppet integration documentation or mark as legacy
- **Remove** Puppet-related load balancer configurations
- **Update** provisioning diagrams to remove Puppet server components
- **Remove** Puppet-based SCAP content deployment procedures

**Impact Level**: High
**Affected Files**:
- `guides/doc-Configuring_Load_Balancer/master.adoc:34,36,38,40,52`
- `guides/doc-Installing_Server/master.adoc:71`
- `guides/common/modules/proc_restoring-manual-changes-overwritten-by-a-puppet-run.adoc`
- `guides/common/modules/proc_propagating-scap-content-using-puppet-deployment.adoc`
- Provisioning diagram files (`*.plantuml`)

**Additional Considerations**: With containerized Puppet in foremanctl, traditional Puppet administration procedures become obsolete. Focus should shift to container-based configuration management.

---

#### Note 7:
**Topic**: Chapter 5.5 & 5.5.1 - Update Installer Commands and External Database References
**Current State**: Traditional installer commands and references that need foremanctl updates:
- `{foreman-installer} --full-help` references (`guides/common/modules/ref_cli-help.adoc:17`)
- `{installer-scenario} --full-help` commands (`proc_configuring-project-installation.adoc:16`)
- Logging configuration using `{foreman-installer} --full-help` (`proc_increasing-the-logging-level-for-foreman.adoc:24,28`)
- External database configuration via installer scenarios
- Deployment utility help references (`proc_running-project-deployment-utility.adoc:38`)

**Required Changes**:
- **Update** from `satellite-installer` to `foremanctl` commands
- **Drop** `--full-help` documentation references (no longer applicable)
- **Remove** `--scenario` references (containerized architecture change)
- **Update** external database configuration procedures for foremanctl
- **Note** that external database integration is still being designed for foremanctl
- **Evaluate** and update log file locations and access methods for containerized services
- **Update** help command references to use foremanctl syntax

**Impact Level**: High
**Affected Files**:
- `guides/common/modules/ref_cli-help.adoc:17`
- `guides/common/modules/proc_configuring-project-installation.adoc:16`
- `guides/common/modules/proc_increasing-the-logging-level-for-foreman.adoc:24,28`
- `guides/common/modules/proc_running-project-deployment-utility.adoc:38`
- `guides/common/modules/ref_glossary-of-terms-used-in-project.adoc:47`
- `guides/common/modules/proc_configuring-oauth.adoc:11`
- `guides/common/modules/proc_configuring-smart-proxy-for-host-registration-and-provisioning.adoc:66`
- All external database preparation and configuration procedures

**Additional Considerations**: External database support is still being designed for foremanctl, so documentation should reflect this transitional state and avoid definitive configuration procedures until the design is finalized.

---

#### Note 8:
**Topic**: Chapter 6.1 - Configuring Satellite Server as Red Hat Lightspeed Client - Requires Design Decision Evaluation
**Current State**: Documentation covers configuring Satellite Server as Red Hat Insights client (rebranded to Red Hat Lightspeed):
- Uses `{foreman-installer} --register-with-insights` to register server
- Configures `insights-client` tool on Satellite Server for system monitoring and diagnosis
- Includes verification commands (`insights-client --status`)
- Provides unregistration procedures (`insights-client --unregister`)
- Related: Installing and configuring Insights for OpenShift Platform (insights-iop) for local analytics

**Required Changes**:
- **Evaluate** whether foremanctl supports Red Hat Lightspeed client functionality
- **Update** registration method from `{foreman-installer} --register-with-insights` to foremanctl equivalent
- **Determine** if insights-client can be integrated with containerized Satellite architecture
- **Review** insights-iop compatibility with foremanctl deployment
- **Update** verification and management procedures for container environment
- **Note constraints**: insights-iop currently incompatible with external databases

**Impact Level**: Medium - Dependent on Design Decision
**Affected Files**:
- `guides/common/modules/proc_configuring-project-server-as-insights-client.adoc`
- `guides/common/assembly_installing-and-configuring-insights-iop.adoc`
- `guides/common/modules/con_installing-and-configuring-insights-iop.adoc`
- `guides/common/modules/proc_installing-insights-iop-on-a-connected-project-context-server.adoc`
- `guides/common/modules/proc_installing-insights-iop-with-the-project-context-iso-image.adoc`
- `guides/common/modules/proc_installing-insights-iop-by-using-export-and-import.adoc`
- All related Lightspeed/Insights integration procedures

**Additional Considerations**:
- **Design Decision Required**: Whether foremanctl will support Red Hat Lightspeed client integration
- Container architecture may affect how insights-client operates and integrates
- Current insights-iop external database incompatibility may conflict with foremanctl's external database design
- Documentation updates depend entirely on whether this functionality is supported in foremanctl architecture

---

#### Note 9:
**Topic**: Chapter 6.2.2 - Command Naming Updates from satellite-installer to foremanctl
**Current State**: Section 6.2.2 contains references to traditional satellite-installer commands that need updating for foremanctl deployment.

**Required Changes**:
- **Update** command references from `satellite-installer` to `foremanctl` equivalent commands
- **Maintain** existing functionality and procedures (no functional changes)
- **Update** command syntax and parameters to match foremanctl conventions

**Impact Level**: Low
**Affected Files**:
- Chapter 6.2.2 related files with satellite-installer command references

**Additional Considerations**: This is a straightforward command naming update with no functional changes to the underlying procedures or capabilities.

---

#### Note 10:
**Topic**: Configuring Pull-based Transport for Remote Execution - Awaiting Feature Design Completion
**Current State**: Comprehensive documentation exists for pull-based transport for remote execution:
- Configuration on Smart Proxies using `{foreman-installer} --foreman-proxy-plugin-remote-execution-script-mode pull-mqtt`
- Host-side configuration using `yggdrasil` pull client and `katello-pull-transport-migrate` package
- MQTT transport mechanism on port 1883 for job notifications
- Performance tuning and host limit configuration procedures
- Troubleshooting procedures for remote job timeouts after yggdrasil updates
- Transport mode concepts (push-based SSH vs pull-based MQTT)

**Required Changes**:
- **Update** after feature design work is completed per [foremanctl PR #188](https://github.com/theforeman/foremanctl/pull/188)
- **Modify** installer command syntax from `{foreman-installer}` to `foremanctl` equivalent
- **Review** MQTT broker implementation in containerized architecture
- **Update** host client installation and configuration procedures if changed
- **Verify** firewall requirements remain the same for containerized deployment
- **Test** compatibility of `yggdrasil` pull client with foremanctl architecture

**Impact Level**: Medium - Dependent on Feature Design
**Affected Files**:
- `guides/common/modules/proc_configuring-pull-based-transport-for-remote-execution.adoc`
- `guides/common/modules/con_transport-modes-for-remote-execution.adoc`
- `guides/common/modules/proc_configuring-a-host-to-use-the-pull-client.adoc`
- `guides/common/modules/con_pull-based-rex-transport-tuning.adoc`
- `guides/common/modules/proc_increasing-host-limit-for-pull-based-rex-transport.adoc`
- `guides/common/modules/proc_decreasing-performance-impact-of-the-pull-based-rex-transport.adoc`
- `guides/common/modules/proc_troubleshooting-remote-jobs-timing-out-after-yggdrasil-update.adoc`

**Additional Considerations**:
- Documentation updates depend on the completion of feature design work in foremanctl PR #188
- Container architecture may affect MQTT broker deployment and configuration
- Host-side client installation procedures may change with new architecture
- Current SSH fallback behavior and mixed-mode scenarios need verification in containerized environment

---

#### Note 11:
**Topic**: Enabling Power Management on Hosts - Awaiting BMC Feature Design Definition
**Current State**: Documentation exists for enabling power management on hosts using baseboard management controller (BMC) functionality:
- Enable BMC module using `{foreman-installer} --foreman-proxy-bmc "true" --foreman-proxy-bmc-default-provider`
- Supports multiple BMC providers: `freeipmi`, `ipmitool`, `redfish`
- Subnet configuration for BMC Smart Proxy assignment
- Host-level BMC interface configuration with authentication credentials
- IPMI and similar protocol support for power management tasks
- Integration with Smart Proxy servers for distributed power management

**Required Changes**:
- **Update** after BMC feature design enabling is defined for foremanctl
- **Modify** installer command syntax from `{foreman-installer}` to `foremanctl` equivalent
- **Review** BMC module deployment in containerized architecture
- **Verify** BMC provider compatibility with container environment
- **Update** Smart Proxy integration procedures for containerized deployment
- **Test** IPMI/Redfish protocol access from containerized services

**Impact Level**: Medium - Dependent on BMC Feature Design
**Affected Files**:
- `guides/common/modules/proc_enabling-power-management-on-hosts.adoc`
- `guides/common/modules/proc_configuring-a-bmc-interface.adoc`
- Related Smart Proxy power management configuration files
- Network interface management documentation referencing BMC

**Additional Considerations**:
- BMC functionality requires low-level hardware access which may be affected by containerization
- Power management protocols (IPMI, Redfish) need verification of compatibility with container networking
- Smart Proxy BMC integration may require different deployment approaches in containerized environment
- Documentation updates depend on architectural decisions about BMC feature support in foremanctl

---

#### Note 12:
**Topic**: Configuring Satellite Server for Outgoing Emails - Sendmail Deprecation and Container SMTP Impact
**Current State**: Documentation provides email configuration options for outgoing emails:
- SMTP server configuration (recommended method)
- Sendmail command support (already marked as deprecated with `snip_deprecated-feature.adoc`)
- Email settings including delivery methods, SMTP authentication, and server configuration
- Integration with Postfix service for email delivery testing
- Support for TLS authentication and certificate management
- Test email delivery procedures

**Required Changes**:
- **Remove** sendmail support entirely from foremanctl (already deprecated)
- **Remove** sendmail-related configuration options and procedures
- **Focus** exclusively on SMTP server integration for outgoing emails
- **Review** how container-based design affects SMTP integration and configuration
- **Update** email delivery testing procedures for containerized environment
- **Clarify** certificate management for SMTP TLS in container context

**Impact Level**: Medium - Architecture Uncertainty
**Affected Files**:
- `guides/common/modules/proc_configuring-satellite-for-outgoing-emails.adoc`
- `guides/common/modules/ref_email-settings.adoc`
- `guides/common/modules/proc_testing-email-delivery.adoc`
- `guides/common/assembly_configuring-email-notifications.adoc`

**Additional Considerations**:
- **Sendmail deprecation**: Since sendmail is deprecated, foremanctl should not support it at all
- **Container SMTP uncertainty**: Not sure at this time how container-based design affects SMTP integration
- May need to determine if SMTP configuration is handled at container level or host level
- Certificate management for TLS authentication may work differently in containerized environment
- Postfix service references may need updates for container deployment

---

#### Note 13:
**Topic**: 6.9 - Configuring Satellite to Manage Lifecycle of Host Registered to Identity Management Realm
**Current State**: Comprehensive documentation exists for FreeIPA realm integration with automatic lifecycle management:
- Installation and configuration of `ipa-client` package on Satellite/Smart Proxy servers
- FreeIPA client configuration and realm proxy user creation (`foreman-prepare-realm`)
- Keytab file distribution and configuration across Smart Proxies
- Installer configuration using `{foreman-installer} --foreman-proxy-realm` options
- Certificate authority trust configuration for FreeIPA CA certificates
- Web UI realm creation and Smart Proxy assignment
- Host group integration with realm information
- Automatic membership rules based on `userclass` attribute
- Host-Based Access Controls (HBAC) and sudo policy integration

**Required Changes**:
- **Review** how FreeIPA realm integration works in containerized foremanctl environment
- **Update** installer command syntax from `{foreman-installer}` to `foremanctl` equivalent
- **Evaluate** keytab file distribution and management in container deployment
- **Review** certificate authority trust establishment in containerized services
- **Assess** Smart Proxy realm functionality in container architecture
- **Update** service restart procedures for containerized environment
- **Verify** FreeIPA client functionality from within containers

**Impact Level**: High - Complex Integration Dependent on Design
**Affected Files**:
- `guides/common/modules/con_configuring-project-to-manage-the-lifecycle-of-a-host-registered-to-a-freeipa-realm.adoc`
- `guides/common/assembly_configuring-project-to-manage-the-lifecycle-of-a-host-registered-to-a-freeipa-realm.adoc`
- Related realm and authentication configuration files

**Additional Considerations**:
- **Design dependency**: Updates needed based on design of how this is handled in foremanctl
- FreeIPA integration involves complex host-level authentication and certificate management
- Container deployment may affect keytab file access and IPA client functionality
- Automatic membership rules and HBAC policies may require different approaches in containerized environment
- Smart Proxy realm functionality requires careful evaluation for container compatibility

---

#### Note 14:
**Topic**: 6.10/6.11/6.12 - SSL Certificate Management Sections - Complete Re-review Required
**Current State**: Comprehensive SSL certificate management documentation covering three major areas:
- **6.10**: Configuring Satellite/Foreman Server with custom SSL certificate
- **6.11**: Configuring Smart Proxy/Capsule Server with custom SSL certificate
- **6.12**: Renewing certificates (self-signed CA and custom SSL certificates)

**Current Procedures Include**:
- Custom SSL certificate creation using OpenSSL commands
- Certificate deployment via `{foreman-installer}` with `--certs-server-cert`, `--certs-server-key`, `--certs-server-ca-cert` parameters
- Certificate storage in `/root/{cert-name}_cert/` directories
- Certificate renewal procedures for both server and Smart Proxy
- Host certificate deployment procedures
- Certificate Authority bundle management

**Required Changes**:
- **Complete re-review** of all SSL certificate procedures based on foremanctl design
- **Update** installer command syntax from `{foreman-installer}` to `foremanctl` equivalent
- **Redesign** certificate storage and management for containerized environment
- **Review** certificate mounting and volume management in containers
- **Update** certificate file paths and directory structures for container deployment
- **Revise** certificate renewal procedures for containerized services
- **Verify** certificate authority trust establishment in container context
- **Update** host certificate deployment for container-based Smart Proxies

**Impact Level**: High - Fundamental Architecture Change Required
**Affected Files**:
- `guides/common/assembly_configuring-satellite-custom-server-certificate.adoc`
- `guides/common/assembly_configuring-capsule-custom-server-certificate.adoc`
- `guides/common/assembly_renewing-certificates.adoc`
- `guides/common/modules/proc_creating-a-custom-ssl-certificate.adoc`
- `guides/common/modules/proc_deploying-a-custom-ssl-certificate-to-foreman-server.adoc`
- `guides/common/modules/proc_deploying-a-custom-ssl-certificate-to-smart-proxy-server.adoc`
- `guides/common/modules/proc_deploying-a-custom-ssl-certificate-to-hosts.adoc`
- `guides/common/modules/proc_renewing-a-custom-ssl-certificate-on-server.adoc`
- `guides/common/modules/proc_renewing-a-custom-ssl-certificate-on-smart-proxy.adoc`
- `guides/common/modules/con_configuring-foreman-server-with-a-custom-ssl-certificate.adoc`
- `guides/common/modules/con_renewing-certificates.adoc`

**Additional Considerations**:
- SSL certificate management in containers requires fundamentally different approaches
- Certificate mounting, volume management, and container security contexts need design decisions
- Traditional file system-based certificate storage may not apply to containerized deployment
- Certificate renewal in containerized environments involves different restart/reload procedures
- Load balancer SSL certificate configuration may change with container networking
- Container-to-container SSL communication patterns may differ from traditional host-based communication

---

#### Note 15:
**Topic**: Appendix A - "Restoring Manual Changes Overwritten by a Puppet Run" - Section Can Be Dropped
**Current State**: Documentation provides procedures for restoring manual configuration changes that were overwritten by Puppet runs:
- Restoration procedures for DHCP configuration files (`/etc/dhcp/dhcpd.conf`)
- Restoration procedures for DNS configuration files
- Use of `puppet filebucket restore` commands to recover overwritten files
- Instructions for using `--foreman-proxy-dns-managed false` and `--foreman-proxy-dhcp-managed false` installer options
- Log file analysis to identify md5sum of overwritten files
- File comparison procedures to merge required changes

**Required Changes**:
- **Drop this entire section** - not applicable to foremanctl architecture
- Puppet will not manage DHCP and DNS configuration files in the same way with containerized deployment
- Traditional Puppet file management and filebucket restoration becomes obsolete

**Impact Level**: Low - Section Removal
**Affected Files**:
- `guides/common/modules/proc_restoring-manual-changes-overwritten-by-a-puppet-run.adoc`
- References in installation guides and appendices

**Additional Considerations**:
- **Design Need Identified**: This section highlights a critical need to design how DHCP and DNS configuration files will be managed in foremanctl
- Container-based DHCP and DNS services require different configuration management approaches
- Configuration persistence, updates, and manual modifications need new mechanisms in containerized environment
- Need to determine if configuration will be handled via:
  - Container environment variables
  - Configuration file volume mounts
  - Container orchestration configuration management
  - Other containerized configuration approaches

---

#### Note 16:
**Topic**: "Configuring the Base Operating System with Offline Repositories" - Requires setup_containers Script
**Current State**: Documentation provides procedures for configuring offline repositories from ISO images:
- Mounting RHEL 9 ISO images and configuring BaseOS/AppStream repositories
- Mounting Satellite/Foreman server ISO image
- Manual repository configuration with baseurl directives
- Traditional yum repository setup for disconnected environments

**Required Changes**:
- **Add setup_containers script execution** similar to insights-iop installation procedure
- **Update** for foremanctl containerized architecture in offline/disconnected environments
- **Include** container image setup and population from ISO sources
- **Add** container registry configuration for offline container images

**Impact Level**: Medium - Container Setup Required
**Affected Files**:
- `guides/common/modules/proc_configuring-the-base-operating-system-with-offline-repositories.adoc`
- Related offline/disconnected installation procedures

**Additional Considerations**:
- **Similar to insights-iop**: The insights-iop installation uses `/media/sat6/setup_containers` script for container setup in disconnected environments
- foremanctl will need equivalent container setup procedures for offline deployments
- Container images and registries need to be configured for disconnected foremanctl installations
- ISO-based container image distribution may be required for air-gapped environments
- **Process Improvement Needed**: Look at making this section have fewer steps and building more functionality into scripts for better user experience

---

#### Note 17:
**Topic**: 6.1.2 - Installing Red Hat Lightspeed Export/Import - Need Satellite/foremanctl Version
**Current State**: Documentation provides export/import procedure specifically for Red Hat Lightspeed (insights-iop) installation in disconnected environments:
- Container image export from connected systems using skopeo
- Automated scripts for downloading specific insights-iop container images
- Transfer procedures for archive files to disconnected systems
- Automated scripts for importing container images on disconnected systems
- Includes images like `iop-ingress-rhel9`, `iop-advisor-frontend-rhel9`, `iop-host-inventory-rhel9`, etc.
- Uses `oci-archive` format for container image transfer

**Required Changes**:
- **Create equivalent export/import procedure for Satellite/foremanctl** core installation (not just Lightspeed)
- **Add script or functionality into foremanctl** to automate the export/import process
- **Include all core Satellite/foremanctl container images** in export/import procedures
- **Integrate with foremanctl installation process** for disconnected environments

**Impact Level**: High - Core Functionality for Disconnected Deployments
**Affected Files**:
- Need new procedure file for Satellite/foremanctl export/import
- `guides/common/modules/proc_installing-insights-iop-by-using-export-and-import.adoc` (as reference model)
- Related disconnected installation guides

**Additional Considerations**:
- **Critical for air-gapped environments**: foremanctl needs equivalent container export/import capability
- **Built-in functionality preferred**: Add script or functionality into foremanctl to automate this process rather than requiring manual procedures
- **Core vs. optional images**: Need to identify which container images are essential for base foremanctl functionality
- **Version compatibility**: Export/import procedures must handle version matching between source and target systems
- **Storage requirements**: Container image archives may require significant disk space for transfer

---

#### Note 18:
**Topic**: Installing Capsule Server - Hybrid Packages + Containers Architecture with Image Distribution
**Current State**: Current Capsule/Smart Proxy installation follows traditional package-based approach:
- Register base OS to Satellite Server for repository access
- Configure repositories for Smart Proxy packages
- Install Smart Proxy packages using package managers (`{smartproxy-installer-package}`)
- Configure using `{foreman-installer}` with various parameters
- SSL certificate configuration and enablement in UI
- Pure package-based deployment model

**Required Changes**:
- **Account for hybrid packages + containers architecture** in Smart Proxy installation
- **Design foremanctl element to help with pulling container images** from Satellite during Capsule install
- **Consider automated registration assistance** to get Capsule repositories from Satellite if needed
- **Update installer commands** from `{foreman-installer}` to `foremanctl` equivalent for Smart Proxy configuration
- **Container image distribution mechanism** from central Satellite to distributed Smart Proxies
- **Hybrid deployment model** supporting both container and package components

**Impact Level**: High - Distributed Architecture Design Required
**Affected Files**:
- `guides/common/assembly_installing-capsule-server.adoc`
- `guides/common/modules/proc_registering-capsule-to-satellite-server.adoc`
- `guides/common/modules/proc_installing-smart-proxy-server-packages.adoc`
- `guides/common/modules/proc_installing-smart-proxy-server.adoc`
- All Smart Proxy configuration procedures

**Additional Considerations**:
- **Distributed container architecture**: Smart Proxies may need container images from central Satellite registry
- **Image synchronization**: Mechanism for keeping Smart Proxy container images updated
- **Bandwidth considerations**: Efficient image distribution to remote Smart Proxy locations
- **Version consistency**: Ensuring container image versions match between Satellite and Smart Proxies
- **Hybrid deployment complexity**: Managing both containerized and package-based components
- **Network requirements**: Container registry access and authentication between Satellite and Smart Proxies
- **Offline Smart Proxy support**: Container image distribution in disconnected Smart Proxy scenarios

---

#### Note 19:
**Topic**: 3.4 - Configuring Capsule Server with SSL Certificates - Design Updates Required for foremanctl
**Current State**: Comprehensive SSL certificate configuration for Capsule/Smart Proxy servers using traditional installer approach:
- **Default certificate configuration** using `{certs-generate}` command on Project Server
- **Custom certificate configuration** with CA-signed certificates
- Certificate archive generation and transfer (`{smartproxy-example-com}-certs.tar`)
- `{foreman-installer}` command execution with certificate parameters on Smart Proxy
- File-based certificate storage in `/root/{smart-proxy-context}_cert/` directories
- Certificate deployment using installer commands returned by `{certs-generate}`

**Required Changes**:
- **Update based on foremanctl design** for handling certificates with containerized Smart Proxy architecture
- **Replace `{certs-generate}` command** with foremanctl equivalent for certificate generation
- **Update installer command syntax** from `{foreman-installer}` to `foremanctl` equivalent
- **Redesign certificate distribution** mechanism for containerized Smart Proxy deployment
- **Update certificate storage and mounting** approaches for container environments
- **Revise certificate deployment procedures** for hybrid packages + containers architecture

**Impact Level**: High - Distributed Certificate Management Architecture Change
**Affected Files**:
- `guides/common/modules/proc_configuring-capsule-default-certificate.adoc`
- `guides/common/assembly_configuring-capsule-custom-server-certificate.adoc`
- `guides/common/modules/proc_deploying-a-custom-ssl-certificate-to-smart-proxy-server.adoc`
- All Smart Proxy SSL certificate configuration procedures
- Certificate reset and renewal procedures for Smart Proxies

**Additional Considerations**:
- **Distributed certificate management**: Certificate generation, distribution, and renewal across distributed Smart Proxy infrastructure
- **Container certificate mounting**: How certificates are mounted and accessed within containerized Smart Proxy services
- **Certificate authority distribution**: Managing CA certificates across containerized Smart Proxy deployments
- **Automated certificate renewal**: Certificate lifecycle management in containerized distributed environment
- **Security context implications**: Container security contexts and certificate access permissions
- **Volume management**: Certificate storage using container volumes vs. traditional file system storage
- **Network security**: Secure certificate distribution channels between Project Server and Smart Proxies

---

#### Note 20:
**Topic**: Load-Balanced Capsule Server Architecture - Container-Native Load Balancing Design Considerations
**Current State**: Traditional TCP load balancing setup with specific limitations and requirements:
- **Architecture**: {ProjectServer} + 2+ {SmartProxyServers} + TCP Load Balancer + Multiple hosts
- **Supported services**: Host registration, content delivery, Puppet configuration
- **Load balancer requirements**: HAProxy with TCP forwarding, SSL passthrough (no SSL offloading)
- **Port configuration**: HTTP(80), HTTPS(443), Anaconda(8000), Puppet(8140), PuppetCA(8141), SmartProxy({smartproxy_port})
- **Content synchronization**: Manual content view synchronization across all Smart Proxies required
- **Puppet limitations**: Certificate Authority restricted to single Smart Proxy, complex port routing for CA requests
- **SSL certificate complexity**: Each Smart Proxy requires distinct SSL certificates (default or custom)
- **No existing Smart Proxy support**: Must create new Smart Proxies specifically for load balancing

**Required Changes for foremanctl**:
- **Container-native load balancing**: Design load balancing for containerized Smart Proxy services
- **Container orchestration integration**: Leverage container orchestration platforms for native load balancing
- **Service mesh considerations**: Evaluate service mesh technologies for inter-container communication
- **Container registry load balancing**: Distribute container image pulls across multiple Smart Proxy registries
- **Automated content synchronization**: Replace manual content view sync with automated container image distribution
- **Simplified certificate management**: Streamline SSL certificate distribution and renewal in load-balanced container environment
- **Container health checks**: Implement container-aware health checking for load balancer backends
- **Dynamic service discovery**: Enable automatic Smart Proxy discovery and registration with load balancers

**Impact Level**: High - Fundamental Architecture Redesign Required
**Affected Files**:
- `guides/doc-Configuring_Load_Balancer/master.adoc` (entire guide)
- `guides/common/assembly_overview-of-load-balancing-in-project.adoc`
- `guides/common/assembly_installing-the-load-balancer.adoc`
- `guides/common/assembly_preparing-smartproxyservers-for-load-balancing.adoc`
- All load balancing SSL certificate configuration assemblies
- `guides/common/modules/ref_ports-configuration-for-the-load-balancer.adoc`
- Client registration procedures for load balancer

**Additional Considerations**:
- **Container orchestration native features**: Kubernetes/OpenShift provide native load balancing that may replace external load balancers
- **Service mesh integration**: Technologies like Istio could handle inter-service communication, SSL termination, and traffic management
- **Microservices architecture**: Container-native approach may decompose Smart Proxy into microservices with different load balancing needs
- **Horizontal pod autoscaling**: Container platforms can automatically scale Smart Proxy services based on load
- **Ingress controllers**: Container-native ingress handling may replace traditional HAProxy setup
- **Container networking**: CNI networking may affect port configurations and load balancing mechanisms
- **Persistent storage**: Container volume management for synchronized content across load-balanced instances
- **Rolling updates**: Container deployment strategies may eliminate need for sequential Smart Proxy upgrades

---

#### Note 21:
**Topic**: Comprehensive Installer Command References - Complete Documentation Review Required
**Current State**: Extensive use of `{foreman-installer}`, `{installer-scenario}`, and `satellite-installer` commands throughout documentation requiring systematic review and updates for foremanctl migration.

**Categories of Installer Usage Requiring Review**:

**1. Server Installation and Configuration**:
- `guides/common/modules/con_configuring-project-server.adoc`
- `guides/common/modules/con_configuring-project-server-with-external-database.adoc`
- `guides/common/modules/con_installing-server.adoc`
- `guides/common/modules/proc_configuring-project-installation.adoc`
- `guides/common/modules/proc_installing-from-the-offline-repositories.adoc`

**2. Smart Proxy/Capsule Installation and Configuration**:
- `guides/common/modules/proc_installing-smart-proxy-server.adoc`
- `guides/common/modules/proc_configuring-capsule-default-certificate.adoc`
- `guides/common/modules/proc_configuring-smart-proxy-server-with-*-ssl-certificates-*.adoc` (multiple files)
- `guides/common/modules/proc_configuring-remaining-smart-proxy-servers-*.adoc` (multiple files)

**3. SSL Certificate Management**:
- `guides/common/modules/proc_deploying-a-custom-ssl-certificate-to-foreman-server.adoc`
- `guides/common/modules/proc_deploying-a-custom-ssl-certificate-to-smart-proxy-server.adoc`
- `guides/common/modules/proc_renewing-a-custom-ssl-certificate-on-server.adoc`
- `guides/common/modules/proc_renewing-a-custom-ssl-certificate-on-smart-proxy.adoc`
- `guides/common/modules/proc_resetting-custom-ssl-certificate-to-default-self-signed-certificate-on-project.adoc`

**4. Plugin Installation and Management**:
- `guides/common/modules/proc_installing-*-plugin.adoc` (Amazon EC2, Google GCE, Microsoft Azure, VMware, Shellhooks, Discovery, Proxmox, Resource Quota, Salt, SCC Manager, Webhooks, Kernelcare, Remote Execution, Snapshot Management, Red Hat Cloud)
- `guides/common/modules/proc_enabling-*` procedures (Bootdisk, LibVirt, Puppet, Remote Execution, Template Sync, OpenSCAP, OS Tree Content, Power Management, Cockpit)
- `guides/common/modules/proc_uninstalling-*-plugin.adoc` (various plugins)

**5. Performance Tuning and Configuration**:
- `guides/common/modules/con_performance-tuning-quick-start.adoc`
- `guides/common/modules/con_postgresql-tuning.adoc`
- `guides/common/modules/con_dynflow-tuning.adoc`
- `guides/common/modules/con_puma-workers-and-threads-autotuning.adoc`
- `guides/common/modules/proc_configuring-puma-workers.adoc`
- `guides/common/modules/proc_manually-tuning-puma-workers-and-threads-count.adoc`
- `guides/common/modules/proc_tuning-with-predefined-profiles.adoc`
- `guides/common/modules/proc_tuning-apache-httpd-child-processes.adoc`

**6. Authentication and Identity Management**:
- `guides/common/modules/con_oauth-authentication-overview.adoc`
- `guides/common/modules/proc_configuring-oauth.adoc`
- `guides/common/modules/proc_configuring-host-based-access-control-for-freeipa-users-logging-in-to-project.adoc`
- `guides/common/modules/proc_configuring-the-freeipa-authentication-source-on-projectserver.adoc`
- `guides/common/modules/proc_configuring-the-active-directory-authentication-source-on-projectserver.adoc`
- `guides/common/modules/proc_enrolling-projectserver-in-your-freeipa-domain.adoc`
- `guides/common/modules/proc_registering-project-as-a-client-of-keycloak.adoc`

**7. Service Integration (DHCP, DNS, TFTP)**:
- `guides/common/modules/proc_enabling-the-installer-managed-dhcp-service.adoc`
- `guides/common/modules/proc_enabling-the-installer-managed-dns-service.adoc`
- `guides/common/modules/proc_enabling-the-installer-managed-tftp-service.adoc`
- `guides/common/modules/proc_configuring-server-for-use-with-tftp.adoc`
- `guides/common/modules/proc_configuring-server-or-proxy-for-use-with-isc-dhcp.adoc`
- `guides/common/modules/proc_disabling-*-for-integration.adoc` (DHCP, DNS, TFTP)
- `guides/common/modules/proc_integrating-*` procedures (Infoblox, PowerDNS, Route 53, LibVirt, RFC 2136)

**8. Remote Execution Configuration**:
- `guides/common/modules/proc_configuring-pull-based-transport-for-remote-execution.adoc`
- `guides/common/modules/proc_configuring-kerberos-authentication-for-remote-execution.adoc`
- `guides/common/modules/proc_setting-an-alternative-directory-for-remote-execution-jobs-in-push-mode.adoc`
- `guides/common/modules/proc_setting-the-job-rate-limit-on-smartproxy.adoc`
- `guides/common/modules/proc_increasing-host-limit-for-pull-based-rex-transport.adoc`
- `guides/common/modules/proc_decreasing-performance-impact-of-the-pull-based-rex-transport.adoc`

**9. Logging and Monitoring Configuration**:
- `guides/common/modules/proc_configuring-logging-type-and-layout.adoc`
- `guides/common/modules/proc_increasing-the-logging-level-for-*.adoc` (Foreman, Candlepin, Pulp, Puppet Agent, Puppet Server, Redis, Smart Proxy, Foreman Installer)
- `guides/common/modules/proc_selective-debugging-with-individual-loggers.adoc`
- `guides/common/modules/proc_configuring-pcp-data-collection.adoc`

**10. External Database Configuration**:
- `guides/common/modules/con_migrating-from-internal-databases-to-external-databases.adoc`
- `guides/common/modules/proc_migrating-to-external-databases.adoc`
- `guides/common/modules/proc_upgrading-the-external-database-operating-system.adoc`

**11. Load Balancing Configuration**:
- All load balancing Smart Proxy configuration procedures
- Load balancer setup and port configuration procedures

**12. Insights and Red Hat Cloud Integration**:
- `guides/common/modules/proc_configuring-project-server-as-insights-client.adoc`
- `guides/common/modules/proc_installing-insights-iop-*.adoc` procedures
- `guides/common/modules/proc_tracking-subscription-usage-by-using-the-subscriptions-service.adoc`

**13. Specialized Configurations**:
- `guides/common/modules/proc_configuring-ipxe-environment.adoc`
- `guides/common/modules/proc_configuring-smartproxies-for-use-with-freeipa.adoc`
- `guides/common/modules/proc_configuring-smartproxy-for-uefi-http-booting.adoc`
- `guides/common/modules/proc_configuring-project-with-an-alternate-cname.adoc`
- `guides/common/modules/proc_configuring-your-project-to-run-ansible-roles.adoc`
- `guides/common/modules/proc_configuring-satellite-for-outgoing-emails.adoc`

**14. System Maintenance and Updates**:
- `guides/common/modules/proc_renaming-server.adoc`
- `guides/common/modules/proc_renaming-smart-proxy.adoc`
- `guides/common/modules/proc_starting-and-stopping-server.adoc`
- `guides/common/modules/proc_updating-foreman-server.adoc`
- `guides/common/modules/proc_updating-smart-proxy-server.adoc`
- `guides/common/modules/proc_upgrading-*.adoc` procedures

**Impact Level**: High - Complete Documentation Overhaul Required
**Scope**: 100+ files containing installer command references requiring systematic review and update

**Required Changes**:
- **Replace all `{foreman-installer}` references** with `foremanctl` equivalents
- **Update all `{installer-scenario}` references** with appropriate foremanctl commands, removing `--scenario` parameters and replacing with foremanctl-appropriate configuration
- **Update installer option parameters** to match foremanctl command structure
- **Revise installer help references** (`--help`) to use foremanctl documentation and drop `--full-help` references
- **Update installer log file paths** and locations for containerized environment
- **Review installer package references** for foremanctl installation requirements

**Additional Considerations**:
- **Systematic approach required**: Each installer reference must be individually reviewed and updated
- **Command structure changes**: foremanctl may have fundamentally different command structure than traditional installer
- **Configuration management approach**: Container-based configuration may require different approaches than traditional installer parameters
- **Testing requirements**: Each updated procedure will require validation in foremanctl environment
- **Documentation coordination**: Updates must be coordinated across all documentation areas to ensure consistency

---

## Systematic Review Checklist

### Primary Documentation Areas
- [ ] **Installation Guides**
  - [ ] `guides/doc-Installing_Server/` - Traditional installation
  - [ ] `guides/doc-Installing_Server_foremanctl/` - foremanctl installation
  - [ ] `guides/doc-Installing_Server_Disconnected/` - Disconnected installation

- [ ] **Configuration Guides**
  - [ ] `guides/doc-Configuring_User_Authentication/`
  - [ ] `guides/doc-Configuring_Load_Balancer/`
  - [ ] `guides/doc-Configuring_virt_who_VM_Subscriptions/`

- [ ] **Management Guides**
  - [ ] `guides/doc-Managing_Hosts/`
  - [ ] `guides/doc-Managing_Configurations_Ansible/`
  - [ ] `guides/doc-Managing_Configurations_Puppet/`
  - [ ] `guides/doc-Managing_Configurations_Salt/`

### Key Files to Review
- [ ] **Installation Procedures**
  - [ ] `guides/common/modules/proc_installing-project-server-packages.adoc`
  - [ ] `guides/common/modules/proc_configuring-project-installation.adoc`

- [ ] **Build and Deployment**
  - [ ] `Dockerfile`
  - [ ] `Makefile`
  - [ ] `web/nanoc.yaml`

### Migration Impact Categories

#### High Priority Changes
- Installation method transitions
- Core configuration changes
- Service management updates

#### Medium Priority Changes
- Administrative procedure updates
- Troubleshooting guide revisions
- Performance tuning adjustments

#### Low Priority Changes
- Reference documentation updates
- Example configurations
- Appendix materials

---

## Key Questions for Each Review Section

1. **Does this procedure work the same way with foremanctl?**
2. **Are there container-specific considerations?**
3. **Do the file paths/locations change?**
4. **Are there new prerequisites or dependencies?**
5. **Does the troubleshooting approach differ?**
6. **Are there security implications that need documentation?**

---

## Summary of Changes Needed

### High Impact Changes
| Topic | Description | Files Affected | Estimated Effort |
|-------|-------------|----------------|------------------|
|       |             |                |                  |

### Medium Impact Changes
| Topic | Description | Files Affected | Estimated Effort |
|-------|-------------|----------------|------------------|
|       |             |                |                  |

### Low Impact Changes
| Topic | Description | Files Affected | Estimated Effort |
|-------|-------------|----------------|------------------|
|       |             |                |                  |

---

## Action Items
- [ ] Complete systematic review of all documentation areas
- [ ] Prioritize changes by impact level
- [ ] Create detailed change specifications
- [ ] Coordinate with foremanctl development team
- [ ] Plan documentation update timeline

---

## Notes and Observations
*Use this section for general observations, patterns, or insights discovered during the review process.*
