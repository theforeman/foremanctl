DOCUMENTATION = """
    name: foremanctl
    type: stdout
    short_description: default Ansible screen output
    description:
        - This is the default output callback for ansible-playbook.
    extends_documentation_fragment:
      - default_callback
      - result_format_callback
    requirements:
      - set as stdout in configuration
"""

from ansible.plugins.callback.default import CallbackModule as DefaultCallbackModule
from os.path import basename


class CallbackModule(DefaultCallbackModule):
    CALLBACK_NAME = 'foremanctl'
    FALLBACK_TO_DEFAULT = True

    def v2_playbook_on_start(self, playbook):
        playbook_filename = basename(playbook._file_name)
        if playbook_filename == 'features.yaml':
            self.FALLBACK_TO_DEFAULT = False
        if self.FALLBACK_TO_DEFAULT:
            super().v2_playbook_on_start(playbook)

    def v2_playbook_on_play_start(self, play):
        if self.FALLBACK_TO_DEFAULT:
            super().v2_playbook_on_play_start(play)

    def v2_playbook_on_task_start(self, task, is_conditional):
        if self.FALLBACK_TO_DEFAULT:
            super().v2_playbook_on_task_start(task, is_conditional)

    def v2_runner_on_ok(self, result):
        if self.FALLBACK_TO_DEFAULT:
            super().v2_runner_on_ok(result)
        else:
            if msg := result.result.get('msg'):
                self._display.display(msg)

    def v2_playbook_on_stats(self, stats):
        if self.FALLBACK_TO_DEFAULT:
            super().v2_playbook_on_stats(stats)
