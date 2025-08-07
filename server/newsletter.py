#!/usr/bin/python3

import os


DIR = os.path.dirname(__file__)


def generate_page():
    with open(os.path.join(DIR, "template.html")) as f:
        template = ''.join(f.readlines())
        print(template)

if __name__=='__main__':
    generate_page()
