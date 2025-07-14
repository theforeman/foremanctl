CENTOS_8_BOX_URL = "https://cloud.centos.org/centos/8-stream/x86_64/images/CentOS-Stream-Vagrant-8-20220913.0.x86_64.vagrant-libvirt.box"
CENTOS_9_BOX_URL = "https://cloud.centos.org/centos/9-stream/x86_64/images/CentOS-Stream-Vagrant-9-latest.x86_64.vagrant-libvirt.box"

Vagrant.configure("2") do |config|
  config.vm.box = "centos/stream9"
  config.vm.synced_folder ".", "/vagrant"

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "development/playbooks/etc_host.yaml"
    ansible.compatibility_mode = "2.0"
  end

  config.vm.define "quadlet" do |override|
    override.vm.hostname = "quadlet.example.com"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = 10240
      libvirt.cpus = 4
      provider.vm.box_url = CENTOS_9_BOX_URL
    end
  end

  config.vm.define "client" do |override|
    override.vm.hostname = "client.example.com"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = 1024
      provider.vm.box_url = CENTOS_9_BOX_URL
    end
  end
end
