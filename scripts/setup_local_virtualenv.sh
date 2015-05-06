#! /bin/bash
virtualenv -p /usr/bin/python3 ../env && source ../env/bin/activate && pip install -r ../requirements/base.txt
cd ..
npm install
bower install