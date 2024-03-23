# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/ewjoachim/raincoat/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                           |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| raincoat/\_\_init\_\_.py       |       10 |        0 |        0 |        0 |    100% |           |
| raincoat/\_\_main\_\_.py       |        6 |        0 |        2 |        0 |    100% |           |
| raincoat/cli.py                |       52 |        0 |       30 |        0 |    100% |           |
| raincoat/color.py              |       20 |        0 |        2 |        0 |    100% |           |
| raincoat/constants.py          |        3 |        0 |        0 |        0 |    100% |           |
| raincoat/exceptions.py         |        7 |        0 |        2 |        0 |    100% |           |
| raincoat/github\_utils.py      |        9 |        0 |        2 |        0 |    100% |           |
| raincoat/glue.py               |       18 |        0 |        4 |        0 |    100% |           |
| raincoat/grep.py               |       43 |        0 |       16 |        0 |    100% |           |
| raincoat/match/\_\_init\_\_.py |       62 |        0 |       16 |        1 |     99% |  29->exit |
| raincoat/match/django.py       |       68 |        0 |       24 |        0 |    100% |           |
| raincoat/match/pygithub.py     |       39 |        0 |        2 |        0 |    100% |           |
| raincoat/match/pypi.py         |       44 |        0 |        6 |        0 |    100% |           |
| raincoat/match/python.py       |       77 |        0 |       32 |        0 |    100% |           |
| raincoat/metadata.py           |        9 |        0 |        2 |        0 |    100% |           |
| raincoat/parse.py              |       50 |        0 |       10 |        0 |    100% |           |
| raincoat/source.py             |       97 |        2 |       28 |        0 |     98% |   105-106 |
| raincoat/utils.py              |       31 |        0 |       10 |        0 |    100% |           |
|                      **TOTAL** |  **645** |    **2** |  **188** |    **1** | **99%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/ewjoachim/raincoat/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/ewjoachim/raincoat/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ewjoachim/raincoat/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/ewjoachim/raincoat/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fewjoachim%2Fraincoat%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/ewjoachim/raincoat/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.