import logging
import pathlib
import sys

import fire
import yaml
from decouple import config

from ez_sendgrid.uploader import processor, inventory_map

logger = logging.getLogger(__name__)


class Util(object):
    """Manage your SendGrid templates easy. CI/CD friendly."""

    def sync(self, api_key=None, inventory=None, template_prefix=''):
        """Sync template with Sendgrid.
        Args:
            api_key: Sendgrid API Key.
            inventory: Path to inventory file in YAML.
            template_prefix (optional): Prefix for each template name.
                Defaults to ''.
        """
        if not inventory:
            inventory = config('INVENTORY_FILE', cast=pathlib.Path)
        else:
            inventory = pathlib.Path(inventory)
        if not api_key:
            api_key = config('SENDGRID_API_KEY')

        with open(inventory.resolve(), 'r') as stream:
            inventory_data = yaml.safe_load(stream)

        return processor(inventory_data, api_key, template_prefix)

    def map(self, inventory):
        """Generate inventory map.
        Args:
            inventory: Path to inventory file in YAML.
        """
        inventory = pathlib.Path(inventory)

        with open(inventory.resolve(), 'r') as stream:
            inventory_data = yaml.safe_load(stream)

        return inventory_map(inventory_data)


def main():
    try:
        fire.Fire(Util)
    except Exception:
        logger.exception('ez-sendgrid exits with non-zero code.')
        sys.exit(1)


if __name__ == '__main__':
    main()
