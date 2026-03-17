from ansible.plugins.callback.default import CallbackModule as DefaultCallbackModule

DOCUMENTATION = """
    name: foremanctl
    type: stdout
    short_description: foremanctl stdout callback
    description:
        - Suppresses default Ansible output for plays tagged with
          foremanctl_suppress_default_output, displaying only task msg rather than ansible default output.
    extends_documentation_fragment:
      - default_callback
      - result_format_callback
    requirements:
      - set as stdout in configuration
"""

class CallbackModule(DefaultCallbackModule):
    """Foremanctl callback."""

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'foremanctl'

    FALLBACK_TO_DEFAULT = True

    def v2_playbook_on_start(self, playbook):
        plays = playbook.get_plays()
        tags = plays[0].tags
        if 'foremanctl_suppress_default_output' in tags:
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
            if msg := result._result.get('msg'):
                self._display.display(msg)

    def v2_playbook_on_stats(self, stats):
        if self.FALLBACK_TO_DEFAULT:
            super().v2_playbook_on_stats(stats)
