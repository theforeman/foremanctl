Vagrant.configure("2") do |config|
  config.vm.box = "centos/stream9"
  config.vm.synced_folder ".", "/vagrant"

  config.vm.provision("etc_hosts", type: 'ansible') do |ansible|
    ansible.playbook = "development/playbooks/etc_host.yml"
    ansible.compatibility_mode = "2.0"
  end

  config.vm.provision('disk_resize', type: 'ansible') do |ansible_provisioner|
    ansible_provisioner.playbook = 'development/playbooks/resize_disk.yaml'
  end

  config.vm.define "quadlet" do |override|
    override.vm.hostname = "quadlet.example.com"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = 10240
      libvirt.cpus = 4
      libvirt.machine_virtual_size = 30
    end
  end

  config.vm.define "client" do |override|
    override.vm.hostname = "client.example.com"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = 1024
    end
  end

  config.vm.define "database" do |override|
    override.vm.hostname = "database.example.com"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = 2048
    end
  end
end
