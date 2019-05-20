# -*- coding: UTF-8 -*-

import os

project_dir = "/home/ubuntu/answerbot-tool"
res_dir = os.path.join(project_dir, "res")


def get_base_path():
    return os.path.dirname(os.path.abspath(__file__))
