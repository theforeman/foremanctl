"""Check Vagrant box selection without starting Vagrant or a virtual machine."""

import json
import subprocess
import unittest
from pathlib import Path


class VagrantBoxTest(unittest.TestCase):
    def box_settings(self, box):
        script = """
require 'json'
module Vagrant
  def self.configure(_version)
  end
end
load ARGV.fetch(0)
vm = Struct.new(:box, :box_url, :box_check_update).new
set_box(vm, ARGV.fetch(1))
puts JSON.generate(box: vm.box, url: vm.box_url, update: vm.box_check_update)
"""
        result = subprocess.run(
            ["ruby", "-e", script, str(Path(__file__).resolve().parents[2] / "Vagrantfile"), box],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_centos_stream_uses_supported_download_aliases(self):
        for stream in ("9", "10"):
            with self.subTest(stream=stream):
                self.assertEqual(
                    self.box_settings(f"centos/stream{stream}"),
                    {
                        "box": f"centos-stream{stream}-libvirt",
                        "url": (
                            f"https://cloud.centos.org/centos/{stream}-stream/x86_64/images/"
                            f"CentOS-Stream-Vagrant-Libvirt-{stream}-latest.x86_64.vagrant-libvirt.box"
                        ),
                        "update": False,
                    },
                )

    def test_custom_boxes_are_unchanged(self):
        self.assertEqual(
            self.box_settings("generic/debian13"),
            {"box": "generic/debian13", "url": None, "update": None},
        )


if __name__ == "__main__":
    unittest.main()
