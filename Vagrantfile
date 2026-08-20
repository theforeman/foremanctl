require 'rbconfig'
require 'fileutils'

DOMAIN = ENV.fetch('VAGRANT_DOMAIN', 'example.com'.freeze)

MACOS_ARM64 = RbConfig::CONFIG['host_os'] =~ /darwin/ && RbConfig::CONFIG['host_cpu'] =~ /arm|aarch64/
ENV['VAGRANT_DEFAULT_PROVIDER'] ||= MACOS_ARM64 ? 'qemu' : 'libvirt'

CENTOS_STREAM10_AARCH64_IMAGE_URL = 'https://cloud.centos.org/centos/10-stream/aarch64/images/CentOS-Stream-GenericCloud-10-latest.aarch64.qcow2'.freeze

FOREMANCTL_CACHE_DIR = File.join(Dir.home, '.cache', 'foremanctl').freeze

def fetch_quadlet_aarch64_image
  image_path = File.join(FOREMANCTL_CACHE_DIR, 'CentOS-Stream-GenericCloud-10-latest.aarch64.qcow2')
  unless File.exist?(image_path)
    FileUtils.mkdir_p(FOREMANCTL_CACHE_DIR)
    system('curl', '-fL', '-o', image_path, CENTOS_STREAM10_AARCH64_IMAGE_URL) || raise("Failed to download #{CENTOS_STREAM10_AARCH64_IMAGE_URL}")
  end
  image_path
end

def quadlet_qemu_keypair
  private_key_path = File.join(FOREMANCTL_CACHE_DIR, 'quadlet_qemu_ed25519')
  unless File.exist?(private_key_path)
    FileUtils.mkdir_p(FOREMANCTL_CACHE_DIR)
    system('ssh-keygen', '-t', 'ed25519', '-N', '', '-C', 'foremanctl-quadlet-qemu', '-f', private_key_path, '-q') || raise('Failed to generate ssh keypair for the qemu quadlet VM')
  end
  [private_key_path, "#{private_key_path}.pub"]
end

Vagrant.configure("2") do |config|
  config.vm.synced_folder ".", "/vagrant"

  if ENV['VAGRANT_DEFAULT_PROVIDER'] == 'qemu' && Vagrant.has_plugin?('vagrant-hostmanager')
    # Resolves quadlet.example.com on the host, the same job libvirt's virtual
    # network + dnsmasq does for free on Linux. Mirrors forklift's own
    # Vagrantfile (vagrant/lib/forklift/box_distributor.rb), which uses this
    # plugin with the same custom ip_resolver pattern for non-default NICs.
    config.hostmanager.enabled = true
    config.hostmanager.manage_host = true
    config.hostmanager.include_offline = true
    config.hostmanager.ip_resolver = proc do |vm, _resolving_vm|
      next unless vm.ssh_info && vm.ssh_info[:host]

      result = ''
      vm.communicate.execute('ip addr show eth0') { |type, data| result << data if type == :stdout }
      (ip = /inet (\d+\.\d+\.\d+\.\d+)/.match(result)) && ip[1]
    end
  end

  config.vm.provision("etc_hosts", type: 'ansible') do |ansible|
    ansible.playbook = "development/playbooks/etc_host.yml"
    ansible.compatibility_mode = "2.0"
  end

  config.vm.provision('disk_resize', type: 'ansible') do |ansible_provisioner|
    ansible_provisioner.playbook = 'development/playbooks/resize_disk.yaml'
  end

  config.vm.provider "libvirt" do |libvirt|
    libvirt.management_network_domain = DOMAIN
  end

  config.vm.define "quadlet" do |override|
    override.vm.hostname = "quadlet.#{DOMAIN}"

    if ENV['VAGRANT_DEFAULT_PROVIDER'] == 'qemu'
      # vagrant-qemu's default synced folder implementation uses SMB, which
      # prompts for host credentials and can't run non-interactively.
      override.vm.synced_folder ".", "/vagrant", disabled: true

      # Give quadlet a real routable IP via socket_vmnet (started by
      # `forge bootstrap-vagrant`), matching how libvirt's virtual network
      # gives it one on Linux, instead of NAT/port-forwarding the web ports.
      # DHCP, not a static IP: vagrant-qemu 0.6.3 doesn't apply a static IP
      # requested here when advanced_network is combined with a custom
      # cloud_init block (like ours, for the ssh keypair) -- same as
      # libvirt, which is DHCP-assigned too.
      override.vm.network "private_network", type: "dhcp"

      override.vm.provision('container_binfmt', type: 'ansible') do |ansible|
        ansible.playbook = 'development/playbooks/container_binfmt.yaml'
      end
    else
      override.vm.box = ENV.fetch("FOREMANCTL_BASE_BOX", "centos/stream9")
      if override.vm.box == "centos/stream10"
        override.vm.box_url = "https://cloud.centos.org/centos/10-stream/x86_64/images/CentOS-Stream-Vagrant-10-latest.x86_64.vagrant-libvirt.box"
      end
    end

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = ENV.fetch("FOREMANCTL_QUADLET_MEMORY", "10240").to_i
      libvirt.cpus = ENV.fetch("FOREMANCTL_QUADLET_CPUS", "4").to_i
      libvirt.machine_virtual_size = ENV.fetch("FOREMANCTL_QUADLET_DISK", "50").to_i
    end

    if ENV['VAGRANT_DEFAULT_PROVIDER'] == 'qemu'
      override.vm.provider "qemu" do |qe, qemu_override|
        private_key_path, public_key_path = quadlet_qemu_keypair

        qemu_override.ssh.username = "vagrant"
        qemu_override.ssh.private_key_path = private_key_path

        qe.image_path = fetch_quadlet_aarch64_image
        qe.memory = "10G"
        qe.smp = 4

        qe.advanced_network = true
        qe.net_mode = :socket_vmnet

        qemu_override.vm.cloud_init content_type: "text/cloud-config", inline: <<~CLOUD_CONFIG
          users:
            - name: vagrant
              sudo: ALL=(ALL) NOPASSWD:ALL
              shell: /bin/bash
              ssh_authorized_keys:
                - #{File.read(public_key_path).strip}
        CLOUD_CONFIG
      end
    end
  end

  config.vm.define "client" do |override|
    override.vm.box = "centos/stream9"
    override.vm.hostname = "client.#{DOMAIN}"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = ENV.fetch("FOREMANCTL_CLIENT_MEMORY", "1024").to_i
      libvirt.cpus = ENV.fetch("FOREMANCTL_CLIENT_CPUS", "1").to_i
      libvirt.machine_virtual_size = ENV.fetch("FOREMANCTL_CLIENT_DISK", "20").to_i
    end
  end

  config.vm.define "database" do |override|
    override.vm.box = "centos/stream9"
    override.vm.hostname = "database.#{DOMAIN}"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = ENV.fetch("FOREMANCTL_DATABASE_MEMORY", "2048").to_i
      libvirt.cpus = ENV.fetch("FOREMANCTL_DATABASE_CPUS", "1").to_i
      libvirt.machine_virtual_size = ENV.fetch("FOREMANCTL_DATABASE_DISK", "30").to_i
    end
  end

  config.vm.define "proxy" do |override|
    override.vm.box = "centos/stream9"
    override.vm.hostname = "proxy.#{DOMAIN}"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = ENV.fetch("FOREMANCTL_PROXY_MEMORY", "4096").to_i
      libvirt.cpus = ENV.fetch("FOREMANCTL_PROXY_CPUS", "4").to_i
      libvirt.machine_virtual_size = ENV.fetch("FOREMANCTL_PROXY_DISK", "40").to_i
    end
  end

  # Load user-local box definitions from boxes.yaml (gitignored)
  boxes_yaml = File.join(__dir__, 'boxes.yaml')
  if File.exist?(boxes_yaml)
    user_boxes = YAML.safe_load(File.read(boxes_yaml)) || {}
    user_boxes.compact.each do |name, settings|
      config.vm.define name do |override|
        override.vm.box = settings.fetch('box') { ENV.fetch('FOREMANCTL_BASE_BOX', 'centos/stream9') }

        override.vm.provider "libvirt" do |libvirt, _provider|
          libvirt.memory = settings.fetch('memory', 3072)
          libvirt.cpus = settings.fetch('cpus', 1)
          libvirt.machine_virtual_size = settings.fetch('disk_size', 50)
        end
      end
    end
  end
end
