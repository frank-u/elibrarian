#! /bin/bash
virtualenv -p /usr/bin/python3 ../env && source ../env/bin/activate && pip install --upgrade pip && pip install -r ../requirements/base.txt
