from celery import Celery
import celeryconfig


celery_app = Celery('core')
# Load the config from the configuration dictionary
celery_app.config_from_object(celeryconfig)
# Discover and load task modules
celery_app.autodiscover_tasks(['tasks.message_parsing',
                               'tasks.execute_node',
                               'tasks.agent_conversation'])


if __name__ == '__main__':
    # This block can be used for running Celery from the command line.
    celery_app.start()
