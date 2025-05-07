import hashlib
import json
import logging

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, BulkIndexError
from django.conf import settings

logger = logging.getLogger(__name__)
es = Elasticsearch(
    settings.ES_URL,
    verify_certs=False
)

STORIES_INDEX = "stories"

story_index_settings = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "source": {"type": "keyword"},
            "url": {"type": "keyword"},
            "title_html": {"type": "text"},
            "title_text": {"type": "text"},
            "summary_html": {"type": "text"},
            "summary_text": {"type": "text"},
            "content_html": {"type": "text"},
            "content_text": {"type": "text"},
            "author": {"type": "keyword"},
            "categories": {"type": "keyword"},
            "guid": {"type": "keyword"},
            "published_at": {"type": "date"},
            "fetched_at": {"type": "date"},
            "image_url": {"type": "keyword"},
            "language": {"type": "keyword"}
        }
    }
}


def create_story_index():
    if not es.indices.exists(index=STORIES_INDEX):
        es.indices.create(index=STORIES_INDEX, body=story_index_settings)
        logger.debug(f"Index '{STORIES_INDEX}' created.")
    else:
        logger.debug(f"Index '{STORIES_INDEX}' already exists.")


def delete_story_index():
    if es.indices.exists(index=STORIES_INDEX):
        es.indices.delete(index=STORIES_INDEX)
        logger.debug(f"Index '{STORIES_INDEX}' deleted")


def index_story(story):
    doc_id = get_doc_id(story)
    es.index(index=STORIES_INDEX, id=doc_id, document=story)


def bulk_index_stories(stories):
    if not stories:
        return

    actions = [
        {
            "_index": STORIES_INDEX,
            "_id": get_doc_id(story),
            "_source": story,
        }
        for story in stories
    ]

    try:
        bulk(es, actions)
        logger.debug(f"Indexed {len(stories)} stories.")
    except BulkIndexError as e:
        for error in e.errors:
            print(error)


def get_doc_id(story):
    unique_id = {
        "guid": story["guid"],
        "published_at": story["published_at"],
    }

    id_json = json.dumps(unique_id, sort_keys=True)
    id_hash = hashlib.sha256(id_json.encode()).hexdigest()
    return id_hash
