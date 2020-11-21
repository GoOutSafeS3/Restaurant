#!/bin/sh

case "$1" in
    "unittests-report")
        pytest --cov=restaurants --cov-report term-missing --cov-report html --html=report.html
        ;;
    "unittests")
        pytest --cov=restaurants
        ;;
    "setup")
        pip3 install -r requirements.txt
        pip3 install pytest pytest-cov
        pip3 install pytest-html
        ;;
    "docker-build")
        docker build . -t restaurants
        ;;
    "docker")
        if [ -z "$2" ] 
        then
            docker run -it -p 8080:8080 restaurants 
        else
            docker run -it -p 8080:8080 -e "CONFIG=$2" restaurants
        fi
        ;;
    *)
        python3 restaurants/app.py "$1"
        ;;
esac