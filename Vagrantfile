Vagrant.configure("2") do |config|
  config.vm.box = "centos/stream9"
  config.vm.synced_folder ".", "/vagrant"

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "development/playbooks/etc_host.yml"
    ansible.compatibility_mode = "2.0"
  end

  config.vm.define "quadlet" do |override|
    override.vm.hostname = "quadlet.example.com"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = 10240
      libvirt.cpus = 4
    end
  end

  config.vm.define "client" do |override|
    override.vm.hostname = "client.example.com"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = 1024
    end
  end
end
