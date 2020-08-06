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
    with open(pathlib.Path(template_file).resolve()) as file:
        return file.read()


def process_response(resp: Response) -> dict:
    """Response handling routine."""
    if not (400 > resp.status_code >= 200):
        raise Exception(f'Server resp {resp.status_code}, err: {resp.body}')
    return json.loads(resp.body)


def parse_datetime(value: str) -> datetime.datetime:
    """
    Parse date.

    '2020-04-23 16:14:45' -> datetime object
    """
    return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')


def delete_old_versions(template_id: str, keep: int, *, sg: sendgrid.SendGridAPIClient) -> None:
    """
    Delete old not active versions of template.

    :param template_id: id of sendgrid template
    :param keep: the number of previous versions to keep (default: 0)
    :param sg: sendgrid client
    :return:
    """
    template = process_response(sg.client.templates._(template_id).get())
    versions_to_delete = sorted(
        filter(lambda v: not v['active'], template['versions']),
        key=lambda v: parse_datetime(v['updated_at']),
        reverse=True,
    )[keep - 1:]
    for version in versions_to_delete:
        logging.info(f'Delete version id=`{version["id"]}` template=`{template["id"]}`')
        sg.client.templates._(template['id']).versions._(version['id']).delete()


def processor(inventory_data: list, api_key: str, template_prefix=None) -> None:
    """Run templates sync."""
    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    template_prefix = f'[{template_prefix}] ' if template_prefix else ''

    for template in inventory_data:
        template_name = f'{template_prefix}{template["name"]}'
        logger.info(f'Start to update template=`{template_name}`')

        data = {
            'subject': template['subject'],
            'template_id': template['template_id'],
            'active': template.get('active', 1),
            'plain_content': template.get('plain_content', '<%body%>'),
            'html_content': template_resolver(template['html_template']),
        }

        if not template.get('template_id'):
            r = sg.client.templates.post(request_body={'name': template_name,
                                                       'generation': template.get('generation', 'dynamic')})
            template_id = process_response(r)['id']
            logger.warning(f'Added template=`{template_name}` id={template_id}, add to inventory before next update')
            template.update({'template_id': template_id})
            data.update({'template_id': template_id})

        if not template.get('version_id'):
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

        keep = int(template.get('keep', 0))
        if keep > 0:
            logging.info(f'Delete old versions of template=`{template_name}`')
            delete_old_versions(template['template_id'], keep, sg=sg)


def inventory_map(inventory_data: list) -> dict:
    """Generate inventory map."""
    external_map = {}
    for template in inventory_data:
        external_map.update({template['ext_id'] if template.get('ext_id') else template['name']: template.get('template_id')})

    logger.debug('Mapping %s', pprint.pformat(external_map))
    return pprint.pprint(external_map)
