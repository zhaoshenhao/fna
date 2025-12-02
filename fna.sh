#!/bin/bash
#   Linux chkconfig:
#   chkconfig: 2345 56 10
#   2345 56
#   2345 10
#   description: FNA start/stop/restart script
# Source function library.
SERVICE_NAME="FNA Web"
SERVICE_USER="compusky"
WORK_DIR="/home/compusky/fna"
export PYTHONPATH=${WORK_DIR}:${WORK_DIR}/fna:${WORK_DIR}/web

start() {
  if [[ `/usr/bin/whoami` == $SERVICE_USER ]]; then
    cd "${WORK_DIR}"
    conda init
    conda activate fna
    export PYTHONPATH=$(pwd):$(pwd)/fna:$(pwd)/webui
    nohup gunicorn --workers=2 fna.wsgi &
  else
    echo "You are not ${SERVICE_USER}."
  fi
}

stop() {
  cd $FOLDER
  kill -s TERM $( pidof /home/compusky/miniconda3/envs/fna/bin/python )
}

status() {
  echo "Running process: $( pidof /home/compusky/miniconda3/envs/fna/bin/python )"
}

#Body main
case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    echo "Restarting $SERVICE_NAME..."
    stop
    sleep 10
    start
    ;;
  state)
    echo "${SERVICE_NAME} status:"
    status
    ;;
  *)
    echo $"Usage: $0 {start|stop|restart|state}"
    exit 1
esac
exit 0
