"""
Script to emulate a sv harvester client that sends requests through the AMQP server
"""

import argparse
import csv
import json
import os

import pika
from pika import DeliveryMode
from pika.exchange_type import ExchangeType


def _parse_args():
    parser = argparse.ArgumentParser()
    # Required positional argument
    parser.add_argument(
        "--file",
        help="Researcher identifiers file",
        required=False,
        type=str,
        default=os.getenv("RESEARCH_IDS_FILE"),
    )
    return parser.parse_args()


def _publish_requests(args):
    harvesters = os.getenv("HARVESTERS", "idref,scanr,hal,openalex").split(",")
    credentials = pika.PlainCredentials(
        os.getenv("AMQP_USER", "guest"), os.getenv("AMQP_PASSWORD", "guest")
    )
    parameters = pika.ConnectionParameters(
        host=os.getenv("AMQP_HOST", "localhost"),
        port=os.getenv("AMQP_PORT", 5672),
        credentials=credentials,
    )
    connection = pika.BlockingConnection(parameters)
    routing_key = "task.entity.references.retrieval"

    channel = connection.channel()

    channel.confirm_delivery()

    exchange_name = "publications"
    channel.exchange_declare(
        exchange_name,
        ExchangeType.topic,
        durable=True,
    )

    count = 0
    print(f"Reading file {args.file}")
    if not os.path.exists(args.file):
        print(f"File {args.file} does not exist")
        return
    with open(f"{args.file}", "r", encoding="UTF-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            count += 1
            print(f"row : {count}")
            name = row.get("name", None)
            if name is None:
                name = f"{row.get('last_name', '')}, {row.get('first_name', '')}"
            payload = {
                "type": "person",
                "reply": True,
                "identifiers_safe_mode": False,
                "events": ["created", "updated", "deleted", "unchanged"],
                "harvesters": harvesters,
                "fields": {
                    "name": name,
                    "identifiers": [
                        {"type": key, "value": row[key]}
                        for key in row
                        if key
                        in ["idref", "id_hal_i", "id_hal_s", "orcid", "scopus_eid"]
                        and row[key]
                    ],
                },
            }
            channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=json.dumps(payload).encode(),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=DeliveryMode.Persistent,
                ),
                mandatory=True,
            )


if __name__ == "__main__":
    args = _parse_args()
    _publish_requests(args)
