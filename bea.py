#!/usr/bin/env python3
# Blogger Export Analyzer
# Copyright (c) 2012-2013 Yu-Jie Lin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import argparse
import datetime
import re
import shelve
from itertools import chain, groupby, islice

from lxml import etree, html

__program__ = 'bea'
__description__ = 'Blogger Export Analyzer'
__author__ = 'Yu-Jie Lin'
__email__ = 'livibetter@gmail.com'
__copyright__ = 'Copyright 2012-2013, Yu Jie Lin'
__license__ = 'MIT'
__version__ = '0.2.1'
__website__ = 'http://s.yjl.im/bea'


CACHE_VERSION = 1


def list_it(d, tag, item):

  if tag in d:
    d[tag].append(item)
  else:
    d[tag] = [item]


def to_dict(e):

  tag = e.tag.replace('{%s}' % e.nsmap[e.prefix], '')
  children = e.getchildren()
  d = dict(e.attrib)
  if not children:
    if d and tag not in ['title']:
      if tag not in ['category', 'extendedProperty', 'image', 'in-reply-to',
                     'link', 'thumbnail']:
        # tags have text content
        d['text'] = e.text
      return d, tag
    if tag in ['published', 'updated']:
      return datetime.datetime.strptime(e.text.replace(':', ''), '%Y-%m-%dT%H%M%S.%f%z'), tag
    return e.text, tag

  for _c, _tag in (to_dict(c) for c in children):
    # list-type
    if _tag == 'category':
      if 'scheme' in _c and '#kind' in _c['scheme']:
        d['scheme'] = _c['term'].split('#')[1]
        continue
      list_it(d, 'label', _c['term'])
    if _tag == 'entry':
      scheme = _c['scheme']
      del _c['scheme']
      if scheme in ['comment', 'post']:
        text = html.fromstring('<div>' + (_c['content'] or '') + '</div>').xpath('string()')
        _c['text'] = text
        words = text.split()
        chars = sum(len(w) for w in words)
        _c['words'] = len(words)
        _c['chars'] = chars
        if scheme == 'post':
          # published doesn't have microseconds, but updated has, add new
          # value with no microseconds
          _c['updated_no_us'] = _c['updated'].replace(microsecond=0)
          _c['updated_after'] = _c['updated_no_us'] - _c['published']
      if 'control' in _c and _c['control']['draft'] == 'yes':
        del _c['control']
        list_it(d, 'draft', _c)
        continue
        # TODO possible other control value?
      list_it(d, scheme, _c)
    elif _tag == 'content':
      d[_tag] = _c['text']
    # ignored tags, not really useful for analysis
    elif _tag not in ['extendedProperty', 'image', 'link', 'thumbnail']:
      d[_tag] = _c
  return d, tag


def section(text, level=1):

  c = ['=', '-', '.'][level]
  print()
  print('{c} {} {:{c}<{}}'.format(text, '', 78 - 3 - len(text), c=c))
  print()


def ddd(text, max_l):

  if len(text) > max_l:
    return text[:max_l - 3] + '...'
  return text


WORD_FREQ_RE = re.compile(r'\b[0-9a-z-\'.]+\b', re.I)


def word_freq(text):

  wf = {}
  g = (w.group().lower() for w in WORD_FREQ_RE.finditer(text) if w.group())
  for k, g in groupby(sorted(g)):
    wf[k] = sum(1 for _ in g)

  return wf


def merge_word_freq(wf, wf1):

  for w, c in wf1.items():
    wf[w] = c + wf.get(w, 0)


def calc_others(top_list, total):
  '''Calculate the others amount from top list'''

  others = total - sum(count for count, item in top_list)
  return (others, '<Others>')


def gen_toplist(_list, count, total=None):
  '''Return a top list of a sorted list'''

  if total is None:
    total = sum(count for count, item in _list)
  _list = _list[:count]
  _list.append(calc_others(_list, total))
  return _list


# ========
# Sections
# ========


def s_filter(args):

  if not args.pubdate:
    return

  section('Filter')

  diff = '-----'
  if args.pubdate[0] and args.pubdate[1]:
    diff = (args.pubdate[1] - args.pubdate[0]).days
  print('{0[0]!s:<30} <- {1:5} days -> {0[1]!s:>30}'.format(args.pubdate, diff))


def s_general(f):

  section('General')

  years = (f['post'][0]['published'] - f['post'][-1]['published']).days / 365
  months = 12 * years
  total_posts = len(f['post'])
  total_comments = len(f['comment'])
  total_drafts = len(f.get('draft', []))
  print('{:10,} Posts    {:10,.3f} per year {:8,.3f} per month'.format(
      total_posts, total_posts / years, total_posts / months))
  print('{:10,} Comments {:10,.3f} per year {:8,.3f} per months {:6,.3f} per post'.format(
      total_comments, total_comments / years, total_comments / months, total_comments / total_posts))
  print('{:10,} Pages'.format(len(f['page'])))
  print('{:10,} Drafts'.format(total_drafts))
  print('{:10,} Labels'.format(len(f['label'])))
  print()

  print('{:<30} <- {:4.1f} years -> {:>30}'.format('First post', years, 'Last post'))
  print('{:<30} <- {:3.0f} months -> {:>30}'.format(
    ddd(f['post'][-1]['title'], 30), months, ddd(f['post'][0]['title'], 30)))
  print('{!s:<30} <- {:5} days -> {!s:>30}'.format(
        f['post'][-1]['published'].strftime('%Y-%m-%d %H:%M:%S %Z'),
        (f['post'][0]['published'] - f['post'][-1]['published']).days,
        f['post'][0]['published'].strftime('%Y-%m-%d %H:%M:%S %Z')))


def s_posts(f):

  section('Posts')

  total_posts = len(f['post'])

  updated_posts = tuple(p for p in f['post'] if p['updated_after'])
  total_updated_after = sum(p['updated_after'].total_seconds() for p in updated_posts)
  avg_updated_after = datetime.timedelta(seconds=total_updated_after / len(updated_posts))
  print('{:6,} Posts {:6,} Updated (after {} in average)'.format(total_posts, len(updated_posts), avg_updated_after))
  print()

  total_words = sum(p['words'] for p in f['post'])
  total_chars = sum(p['chars'] for p in f['post'])
  total_labels = sum(len(p.get('label', [])) for p in f['post'])
  print('{:10,} Words  {:10,.3f} per post'.format(total_words, total_words / total_posts))
  print('{:10,} Chars  {:10,.3f} per post'.format(total_chars, total_chars / total_posts))
  print('{:10,} Labels {:10,.3f} per post'.format(total_labels, total_labels / total_posts))
  print()

  num_most_used = int(total_words / total_posts)
  section('{} most used words'.format(num_most_used), level=2)
  wf = {}
  for p in f['post']:
    merge_word_freq(wf, word_freq(p['text']))
  wf = sorted(wf.items(), key=lambda wf: wf[1], reverse=True)[:num_most_used]

  # Find a comforable length: median + 3
  w_len = sorted(len(k) for k, c in wf)
  w_len = min(w_len[int(len(w_len) / 2)] + 3, max(w_len))

  N = int(79 / (6 + w_len + 1))
  for idx, wc in enumerate(wf, 1):
    print('{:5,} {:{w_len}}'.format(wc[1], ddd(wc[0], w_len), w_len=w_len), end='')
    print(' ' if idx % N else '\n', end='')
  print()


def s_posts_comments_grouper(posts, comments, key_fmt):

  kf = lambda p: p['published'].strftime(key_fmt)
  ig_p = groupby(sorted(posts, key=kf), key=kf)
  ig_c = groupby(sorted(comments, key=kf), key=kf)

  icount = lambda i: sum(1 for _ in i)
  d_p = dict((k, icount(g)) for k, g in ig_p)
  d_c = dict((k, icount(g)) for k, g in ig_c)
  keys = d_p.keys() | d_c.keys()
  return dict((key, (d_p.get(key, 0), d_c.get(key, 0))) for key in keys)


def s_two_columns_chart(data, keys, column_names):

  max_c1_count = max(item[0] for item in data.values())
  max_c2_count = max(item[1] for item in data.values())

  c0_size = max(len(column_names[0]), max(len(key) for key in keys))
  half = int((78 - c0_size - 2) / 2)
  c0_size += 78 - half * 2 - 2 - c0_size
  column_sizes = [c0_size, half, half]

  value_size = len(str(max_c1_count)), len(str(max_c2_count))
  bar_size = tuple(half - v - 1 for v in value_size)
  del c0_size, half

  print('{0[0]:^{1[0]}} {0[1]:<{1[1]}}|{0[2]:>{1[2]}}'.format(column_names, column_sizes))
  for key in keys:
    count = data[key] if key in data else [0, 0]
    print('{:^{key_size}} {:{value_size[0]}} {:>{bar_size[0]}}|{:<{bar_size[1]}} {:{value_size[1]}}'.format(
          key,
          count[0],
          '#' * int(bar_size[0] * count[0] / max_c1_count),
          '#' * int(bar_size[1] * count[1] / max_c2_count),
          count[1],
          key_size=column_sizes[0],
          value_size=value_size,
          bar_size=bar_size
          ))


def s_posts_comments(f):

  section('Posts and Comments Published Time')

  posts = f['post']
  comments = f['comment']

  section('By Year and Month', level=2)

  m_pc = s_posts_comments_grouper(posts, comments, '%Y-%m')

  m_pc_keys = m_pc.keys()
  m_min = min(m_pc_keys).split('-')
  m_max = max(m_pc_keys).split('-')
  min_year, min_month = int(m_min[0]), int(m_min[1])
  max_year, max_month = int(m_max[0]), int(m_max[1])
  del m_pc_keys, m_min, m_max

  keys = tuple('%d-%02d' % (year, month)
               for year in range(min_year, max_year + 1)
               for month in range(1, 12 + 1))
  keys = keys[min_month - 1:-(12 - max_month) or None]
  s_two_columns_chart(m_pc, keys, ('YYYY-MM', 'Posts', 'Comments'))

  section('By Year', level=2)

  m_pc = s_posts_comments_grouper(posts, comments, '%Y')

  m_pc_keys = m_pc.keys()
  min_year, max_year = int(min(m_pc_keys)), int(max(m_pc_keys))
  del m_pc_keys

  keys = tuple(str(key) for key in range(min_year, max_year + 1))
  s_two_columns_chart(m_pc, keys, ('Year', 'Posts', 'Comments'))

  section('By Month of Year', level=2)

  m_pc = s_posts_comments_grouper(posts, comments, '%m')
  keys = tuple('%02d' % key for key in range(1, 12 + 1))
  s_two_columns_chart(m_pc, keys, ('Month', 'Posts', 'Comments'))

  section('By Day of Month', level=2)

  m_pc = s_posts_comments_grouper(posts, comments, '%d')
  keys = tuple('%02d' % key for key in range(1, 31 + 1))
  s_two_columns_chart(m_pc, keys, ('Day', 'Posts', 'Comments'))

  section('By Hour of Day', level=2)

  keys = tuple('%02d' % key for key in range(1, 24 + 1))
  s_two_columns_chart(m_pc, keys, ('Hour', 'Posts', 'Comments'))


def s_punchcard(f):

  section('Punchcard')

  posts = f['post']
  comments = f['comment']

  m_pc = s_posts_comments_grouper(posts, comments, '%w-%H')

  punches = ' .oO00'
  len_punches = len(punches) - 1

  secnames = ('Post Published Time', 'Comment Posted Time')
  daynames = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
  dayorder = (1, 2, 3, 4, 5, 6, 0)

  for t in range(len(secnames)):
    section(secnames[t], level=2)
    max_count = max(item[t] for item in m_pc.values())
    print('    +', '-' * (24 * 3), '+', sep='')
    for d in range(7):
      p = (
        punches[int(len_punches *
                    m_pc.get('%d-%02d' % (dayorder[d], h), (0, 0))[t] /
                    max_count)] for h in range(24)
      )
      print(daynames[d],
            ' | ',
            '  '.join(p),
            ' |',
            sep='')
    print('    +', '-' * (24 * 3), '+', sep='')
    print('     ', ''.join('%3d' % i for i in range(24)), sep='')


def s_comments(f):

  section('Comments')

  comments = [c for c in f['comment'] if 'in-reply-to' in c]
  total_comments = len(comments)
  posts = f['post']
  total_posts = len(posts)

  commented_posts = len(set(c['in-reply-to']['ref'] for c in comments))
  print('{:5} comments commented on {:5} ({:5.1f}%) of {:5} posts'.format(
    total_comments,
    commented_posts,
    100 * commented_posts / total_posts,
    total_posts))
  print()

  print('{:5} out of {} Comments are not counted in this section.'.format(
    len(f['comment']) - total_comments,
    len(f['comment'])))

  genlist = lambda kf: gen_toplist(list(islice(sorted(
      [(sum(1 for _ in g), k) for k, g in groupby(sorted(comments, key=kf), key=kf)],
      reverse=True), 10)), 10, total_comments)

  section('Top Commenters', level=2)
  _list = genlist(lambda c: c['author']['name'])
  for count, name in _list:
    print('{:5} ({:5.1f}%): {}'.format(count, 100 * count / total_comments, name))

  section('Most Commented Posts', level=2)
  _list = genlist(lambda c: c['in-reply-to']['ref'])
  for count, ref in _list:
    if ref.startswith('tag:blogger.com'):
      title = ddd(next(p for p in posts if p['id'] == ref)['title'], 78 - 5 - 9 - 2)
    else:
      title = ref
    print('{:5} ({:5.1f}%): {}'.format(count, 100 * count / total_comments, title))

  section('Most Commented Posts Over Days Since Published aka. Popular Posts', level=2)
  kf = lambda c: c['in-reply-to']['ref']
  # FIXME BAD, SUPER BAD
  g = sorted(
      [(count / (datetime.datetime.now(post['published'].tzinfo) - post['published']).days, post) for count, post in (
        (sum(1 for _ in g), next(p for p in posts if p['id'] == k)) for k, g in groupby(sorted(comments, key=kf), key=kf))],
      key=lambda item: item[0],
      reverse=True
  )
  for count, post in islice(g, 10):
    title = ddd(post['title'], 78 - 5 - 2)
    print('{:.3f}: {}'.format(count, title))


def s_labels(f):

  section('Labels')

  genlist = lambda reverse=True: sorted(
      ((sum(1 for _ in g), k) for k, g in groupby(sorted(chain.from_iterable(p.get('label', []) for p in f['post'])))),
      reverse=reverse)

  labels = genlist()
  total_labels = len(f['label'])
  total_labeled = sum(count for count, label in labels)
  print('{:10,} Labels labled {:10,} times {:10.3f} Labeled per label'.format(total_labels, total_labeled, total_labeled / total_labels))

  section('Most Labeled Labels', level=2)
  _list = gen_toplist(labels, 10)
  for count, label in _list:
    print('{:5} ({:5.1f}%): {}'.format(count, 100 * count / total_labeled, label))

  section('Least Labeled Rate', level=2)
  labels = genlist(False)
  for count, labels2 in islice(groupby(labels, key=lambda l: l[0]), 10):
    labels_count = sum(1 for _ in labels2)
    print('{:5} ({:5.1f}%) Labels labeled {:3} times'.format(labels_count, 100 * labels_count / total_labels, count))


# ====
# Main
# ====


def date_type(d):

  if d:
    return datetime.datetime.strptime(d, '%Y-%m-%dT%H:%M:%S%z')
  return None


def main():

  parser = argparse.ArgumentParser(description=__description__)
  parser.add_argument('-v', '--version', action='version',
                      version='%(prog)s ' + __version__)
  parser.add_argument('xml', help='Exported XML file')
  parser.add_argument('-d', '--dump', action='store_true',
                      help='dump cache to readable file')
  parser.add_argument('--pubdate', nargs=2, type=date_type,
                      metavar='YYYY-MM-DDTHH:MM:SS+HHMM')
  args = parser.parse_args()

  filename = args.xml
  filename_cache = filename + '.cache'
  cache = shelve.open(filename_cache)
  if 'feed' in cache and cache.get('CACHE_VERSION', None) == CACHE_VERSION:
    f = cache['feed']
  else:
    d = etree.parse(filename)
    r = d.getroot()
    f, _ = to_dict(r)
    cache['feed'] = f
    cache['CACHE_VERSION'] = CACHE_VERSION
  if args.dump:
    with open(filename + '.dump.py', 'w') as dump_file:
      import pprint
      pprint.pprint(f, dump_file)

  # filter
  if args.pubdate:
    d1, d2 = args.pubdate
    for key in ('post', 'page', 'comment'):
      if d1:
        f[key] = list(p for p in f[key] if p['published'] >= d1)
      if d2:
        f[key] = list(p for p in f[key] if p['published'] <= d2)

  # remove comments which don't have post to belong to
  post_ids = list(p['id'] for p in f['post'])
  f['comment'] = list(c for c in f['comment'] if c['in-reply-to']['ref'] in post_ids)
  del post_ids

  # generate list of labels
  f['label'] = list(set(chain.from_iterable(p.get('label', []) for p in f['post'])))

  print('= {:=<37s}{:=>37s} ='.format('{} {} '.format(__program__, __version__), ' ' + __website__))
  print()
  print(' ', f['title'], 'by', f['author']['name'])
  print(' ', ddd(next(s for s in f['settings'] if 'BLOG_DESCRIPTION' in s['id'])['content'], 76))

  s_filter(args)

  s_general(f)
  s_posts(f)
  s_comments(f)
  s_posts_comments(f)
  s_punchcard(f)
  s_labels(f)


if __name__ == '__main__':
  main()
