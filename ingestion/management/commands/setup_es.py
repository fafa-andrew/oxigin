import logging
from django.core.management.base import BaseCommand

from ingestion.elasticsearch_service import create_story_index, delete_story_index

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sets up the elasticsearch index'

    def handle(self, *args, **options):
        logger.debug('running script')

        delete_story_index()
        create_story_index()
