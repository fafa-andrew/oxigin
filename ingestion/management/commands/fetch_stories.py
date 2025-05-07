import logging
from django.core.management.base import BaseCommand
from ingestion.fetcher import Fetcher
from ingestion.elasticsearch_service import bulk_index_stories

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch RSS stories and index then into Elasticsearch'

    def handle(self, *args, **options):
        logger.debug('Fetching new stories...')

        fetcher = Fetcher()
        stories = fetcher.fetch_all_feeds()

        logger.debug(f'FOUND {len(stories)} stories')

        if stories:
            bulk_index_stories(stories)

        logger.debug('Finished fetching and indexing stories')
