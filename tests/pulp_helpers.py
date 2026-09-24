import json


def parse_pulp_mounts(inspect_output):
    containers = json.loads(inspect_output)
    if isinstance(containers, dict):
        containers = [containers]
    return {
        container['Name'].lstrip('/'): [mount['Destination'] for mount in container.get('Mounts', [])]
        for container in containers
    }
