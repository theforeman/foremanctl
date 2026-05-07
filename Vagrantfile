require 'yaml'

Vagrant.configure("2") do |config|
  if Vagrant.has_plugin?('vagrant-hostmanager')
    config.hostmanager.enabled = true
    config.hostmanager.manage_host = true
    config.hostmanager.manage_guest = true
    config.hostmanager.include_offline = true
  end
  config.vm.synced_folder ".", "/vagrant"

  config.vm.provision("etc_hosts", type: 'ansible') do |ansible|
    ansible.playbook = "development/playbooks/etc_host.yml"
    ansible.compatibility_mode = "2.0"
  end

  config.vm.provision('disk_resize', type: 'ansible') do |ansible_provisioner|
    ansible_provisioner.playbook = 'development/playbooks/resize_disk.yaml'
  end

  config.vm.define "quadlet" do |override|
    override.vm.box = ENV.fetch("FOREMANCTL_BASE_BOX", "centos/stream9")
    override.vm.hostname = "quadlet.example.com"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = 10240
      libvirt.cpus = 4
      libvirt.machine_virtual_size = 50
    end
  end

  config.vm.define "client" do |override|
    override.vm.box = "centos/stream9"
    override.vm.hostname = "client.example.com"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = 1024
    end
  end

  config.vm.define "database" do |override|
    override.vm.box = "centos/stream9"
    override.vm.hostname = "database.example.com"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = 2048
    end
  end

  # Load user-local box definitions from boxes.yaml (gitignored)
  boxes_yaml = File.join(__dir__, 'boxes.yaml')
  if File.exist?(boxes_yaml)
    user_boxes = YAML.safe_load(File.read(boxes_yaml)) || {}
    user_boxes.each do |name, settings|
      next if settings.nil?
      config.vm.define name do |override|
        override.vm.box = ENV.fetch("FOREMANCTL_BASE_BOX", settings.fetch('box', 'centos/stream9'))
        override.vm.hostname = settings.fetch('hostname', "#{name}.example.com")

        override.vm.provider "libvirt" do |libvirt, _provider|
          libvirt.memory = settings.fetch('memory', 4096)
          libvirt.cpus = settings.fetch('cpus', 1)
          libvirt.machine_virtual_size = settings['disk_size'] if settings.key?('disk_size')
        end
      end
    end
  end
end
