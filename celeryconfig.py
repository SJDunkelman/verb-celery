from kombu import Exchange, Queue
import config

broker_url = config.CELERY_BROKER_URL
result_backend = config.REDIS_URL
task_serializer = "json"
result_serializer = "json"
timezone = "Europe/London"
enable_utc = True

task_queues = (
    Queue('messages_queue', Exchange('messages'), routing_key='messages'),
    Queue('agent_conversation_queue', Exchange('agent_conversation'), routing_key='agent_conversation'),
    Queue('node_processing_queue', Exchange('node_processing'), routing_key='node_processing'),
    # Add other queues if necessary
)

# Default settings for tasks
task_default_queue = 'messages_queue'
task_default_exchange_type = 'direct'
task_default_routing_key = 'messages'
