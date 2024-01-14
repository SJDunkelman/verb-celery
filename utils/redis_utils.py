import redis
import json
import config

redis_client = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)


def publish_message(channel: str, message_data: dict):
    message_data = json.dumps(message_data).encode('utf-8')
    redis_client.publish(channel, message_data)


def subscribe_to_channel(channel: str):
    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(channel)
    return pubsub


if __name__ == "__main__":
    # Example usage
    publish_message('messages', "Run a campaign")
