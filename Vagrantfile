if ARGV.any? { |arg| %w[up provision reload].include?(arg) } && ENV['ANSIBLE_COLLECTIONS_PATH'].nil?
  abort("Do not use vagrant directly, use: ./forge vms start\n")
end

DOMAIN = ENV.fetch('VAGRANT_DOMAIN', 'example.com'.freeze)

CENTOS_COMPOSES = {
  '9' => '20260930.0',
  '10' => '20260930.0',
}.freeze

# Official CentOS libvirt images include swap; Vagrant Cloud boxes do not.
# A local box name prevents Vagrant from resolving centos/stream* through registry metadata.
def set_box(vm, box)
  stream = box[/^centos\/stream(\d+)$/, 1]
  unless stream
    vm.box = box
    return
  end

  compose = CENTOS_COMPOSES.fetch(stream)
  vm.box = "centos-stream#{stream}-libvirt"
  vm.box_check_update = false
  vm.box_url = "https://odcs.stream.centos.org/stream-#{stream}/production/CentOS-Stream-#{stream}-#{compose}/compose/BaseOS/x86_64/images/CentOS-Stream-Vagrant-Libvirt-#{stream}-#{compose}.x86_64.vagrant-libvirt.box"
end

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
    set_box(override.vm, ENV.fetch("FOREMANCTL_BASE_BOX", "centos/stream10"))
    override.vm.hostname = "quadlet.#{DOMAIN}"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = ENV.fetch("FOREMANCTL_QUADLET_MEMORY", "12288").to_i
      libvirt.cpus = ENV.fetch("FOREMANCTL_QUADLET_CPUS", "4").to_i
      libvirt.machine_virtual_size = ENV.fetch("FOREMANCTL_QUADLET_DISK", "50").to_i
    end
  end

  config.vm.define "client" do |override|
    set_box(override.vm, ENV.fetch("FOREMANCTL_BASE_BOX", "centos/stream10"))
    override.vm.hostname = "client.#{DOMAIN}"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = ENV.fetch("FOREMANCTL_CLIENT_MEMORY", "1024").to_i
      libvirt.cpus = ENV.fetch("FOREMANCTL_CLIENT_CPUS", "1").to_i
      libvirt.machine_virtual_size = ENV.fetch("FOREMANCTL_CLIENT_DISK", "20").to_i
    end
  end

  config.vm.define "database" do |override|
    set_box(override.vm, ENV.fetch("FOREMANCTL_BASE_BOX", "centos/stream10"))
    override.vm.hostname = "database.#{DOMAIN}"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = ENV.fetch("FOREMANCTL_DATABASE_MEMORY", "2048").to_i
      libvirt.cpus = ENV.fetch("FOREMANCTL_DATABASE_CPUS", "1").to_i
      libvirt.machine_virtual_size = ENV.fetch("FOREMANCTL_DATABASE_DISK", "30").to_i
    end
  end

  config.vm.define "proxy" do |override|
    set_box(override.vm, ENV.fetch("FOREMANCTL_BASE_BOX", "centos/stream10"))
    override.vm.hostname = "proxy.#{DOMAIN}"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = ENV.fetch("FOREMANCTL_PROXY_MEMORY", "3072").to_i
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
        set_box(override.vm, settings.fetch('box') { ENV.fetch('FOREMANCTL_BASE_BOX', 'centos/stream10') })

        override.vm.provider "libvirt" do |libvirt, _provider|
          libvirt.memory = settings.fetch('memory', 3072)
          libvirt.cpus = settings.fetch('cpus', 1)
          libvirt.machine_virtual_size = settings.fetch('disk_size', 50)
        end
      end
    end
  end
end
