DOMAIN = ENV.fetch('VAGRANT_DOMAIN', 'example.com'.freeze)

Vagrant.configure("2") do |config|
  config.vm.synced_folder ".", "/vagrant"

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
    override.vm.box = ENV.fetch("FOREMANCTL_BASE_BOX", "centos/stream9")
    if override.vm.box == "centos/stream10"
      override.vm.box_url = "https://cloud.centos.org/centos/10-stream/x86_64/images/CentOS-Stream-Vagrant-10-latest.x86_64.vagrant-libvirt.box"
    end
    override.vm.hostname = "quadlet.#{DOMAIN}"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = ENV.fetch("FOREMANCTL_QUADLET_MEMORY", "10240").to_i
      libvirt.cpus = ENV.fetch("FOREMANCTL_QUADLET_CPUS", "4").to_i
      libvirt.machine_virtual_size = ENV.fetch("FOREMANCTL_QUADLET_DISK", "50").to_i
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
