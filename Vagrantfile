DOMAIN = ENV.fetch('VAGRANT_DOMAIN', 'example.com'.freeze)

Vagrant.configure("2") do |config|
  config.vm.synced_folder ".", "/vagrant", disabled: true

  config.vm.provider "libvirt" do |libvirt|
    libvirt.management_network_domain = DOMAIN
  end

  config.vm.define "quadlet" do |override|
    override.vm.box = ENV.fetch("FOREMANCTL_BASE_BOX", "centos/stream9")
    override.vm.hostname = "quadlet.#{DOMAIN}"

    override.vm.provider "libvirt" do |libvirt, provider|
      libvirt.memory = 10240
      libvirt.cpus = 4
    end
  end
end
