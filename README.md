Blogger Export Analyzer
=======================

Blogger Export Analyzer (BEA) is a simple analyzer for Blogger Export XML file. BEA is intended to be used for generating one long page of analysis.


Usage
-----

Go to Blogger blog's dashboard, *Settings* » *Other* » *Blog tools*, click on *Export blog* to download an export XML file, then run:

    ./bea.py [options] blog-MM-DD-YYYY.xml

Options
-------

### `-d`, `--dump`

Dump cache content into a file in prettyprint format.

### `--pubdate d1 d2`

`pubdate` allows you to filter on published dates of posts, pages, and comments. The date format is

    %Y-%m-%dT%H:%M:%S%z

A sample date string is like `2012-01-01T00:00:00-0800`.

You can use empty string `''` to indicate infinite endpoint.

Sample output
-------------

You can see [sample output][].

[sample output]: https://bitbucket.org/livibetter/bea/wiki/Sample%20output

License
-------

    Copyright (c) 2012-2013 Yu-Jie Lin
    This program is licensed under the MIT License, see COPYING
