from celery import shared_task


@shared_task
def send_msg_to_bot(chat_id, msg):
    from connection.command_runer import CommandRunner
    CommandRunner.send_notification(chat_id, msg)
