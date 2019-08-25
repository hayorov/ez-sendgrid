import datetime
import json
import logging
import pathlib
import pprint

import sendgrid
from decouple import config
from python_http_client.client import Response

loglevel = config('LOGLEVEL', 'INFO')

logging.basicConfig(level=loglevel, handlers=[logging.StreamHandler()],
                    format='%(asctime)s [%(levelname)s] %(message)s')

logger = logging.getLogger(__name__)


def template_resolver(template_file: str) -> str:
    """Resolve template path into context."""
    with open(pathlib.Path(template_file)) as file:
        return file.read()


def process_response(resp: Response) -> dict:
    """Response handling routine."""
    if not (400 > resp.status_code >= 200):
        raise Exception(f'Server resp {resp.status_code}, err: {resp.body}')
    return json.loads(resp.body)


def processor(inventory_data: list, api_key: str, template_prefix=None) -> None:
    """Run templates sync."""
    sg = sendgrid.SendGridAPIClient(api_key=api_key)

    for template in inventory_data:
        if template_prefix:
            template_prefix = f'[{template_prefix}] '
        template_name = f'{template_prefix}{template["name"]}'

        try:
            data = {
                'subject': template['subject'],
                'template_id': template['template_id'],
                'active': template.get('active', 1),
                'plain_content': template.get('plain_content', '<%body%>'),
                'html_content': template_resolver(template['html_template']),
            }

            if not template['template_id']:
                r = sg.client.templates.post(request_body={'name': template_name,
                                                           'generation': template.get('generation', 'dynamic')})
                template_id = process_response(r)['id']
                logger.warning(f'Added template=`{template_name}` id={template_id}, add to inventory before next update')
                template.update({'template_id': template_id})
                data.update({'template_id': template_id})

            if not template['version_id']:
                logger.debug(data)
                data.update({'name': datetime.datetime.now().isoformat()})
                r = sg.client.templates._(template['template_id']).versions.post(request_body=data)
                version_id = process_response(r)['id']
                logging.info(f'Added version id={version_id} template=`{template_name}`')
                template.update({'version_id': version_id})
            else:
                logger.debug(pprint.pformat(data))
                r = sg.client.templates._(template['template_id']).versions._(template['version_id']).patch(request_body=data)
                version_id = process_response(r)['id']
                logging.info(f'Updated version id=`{version_id}` template=`{template_name}`')
        except Exception:
            logger.exception(f'Unable to update template=`{template_name}`')


def inventory_map(inventory_data: list) -> dict:
    """Generate inventory map."""
    external_map = {}
    for template in inventory_data:
        external_map.update({template['ext_id'] if template['ext_id'] else template['name']: template['template_id']})

    logger.debug('Mapping %s', pprint.pformat(external_map))
    return pprint.pprint(external_map)
