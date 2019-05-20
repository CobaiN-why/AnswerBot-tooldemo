#! /bin/bash
source activate answerbot_python
nohup uwsgi --ini /home/ubuntu/answerbot-tool/src/uwsgi.ini > output 2>&1 &

echo "answerbot start..."

exit 0
