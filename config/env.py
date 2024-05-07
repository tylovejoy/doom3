import os


def get_env(var, default=None):
    return os.environ[var] or default


config = {
    "LOGGING_URL": os.environ["LOGGING_URL"]
    # 'app_name': get_env('APP_NAME'),
    # 'jobs_num': get_env('JOBS_NUM'),
    # 'host': get_env('HOST'),
    # 'port': get_env('PORT'),
}
