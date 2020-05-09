class Config(object):
    JOBS = [
        {
            'id': 'job1',
            'func': 'db:job_delete_inactive',
            'args': (),
            'trigger': 'interval',
            'minutes': 30
        }
    ]

    SCHEDULER_API_ENABLED = True

    SECRET_KEY = '67845632098111'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'liberovao@yandex.ru'

    MAIL_USERNAME = ''

    MAIL_PASSWORD = ''

    MAIL_PORT = 465

    MAIL_USE_SSL = True

    MAIL_SUPPRESS_SEND = True

    TESTING = False
