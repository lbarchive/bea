#!/usr/bin/env python3
# Blogger Export Analyzer
# Copyright (c) 2012 Yu-Jie Lin
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import datetime
import itertools
from lxml import etree
from lxml import html
import os
import re
import shelve
import sys

__program__ = 'Blogger Export Analyzer'
__author__ = 'Yu-Jie Lin'
__copyright__ = 'Copyright 2012, Yu Jie Lin'
__license__ = 'MIT'
__version__ = '0.0.4.2'


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

  for c in children:
    _c, _tag = to_dict(c)
    # ignored tags, not really useful for analysis
    if _tag in ['extendedProperty', 'image', 'link', 'thumbnail']:
      continue
    # list-type
    elif _tag in ['category', 'entry', 'link']:
      if _tag == 'category':
        if 'scheme' in _c and '#kind' in _c['scheme']:
          d['scheme'] = _c['term'].split('#')[1]
          continue
        list_it(d, 'label', _c['term'])
        continue
      if _tag == 'entry':
        scheme =  _c['scheme']
        del _c['scheme']
        if scheme in ['comment', 'post']:
          text = html.fromstring('<div>' + _c['content'] + '</div>').xpath('string()')
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
        if 'control' in _c:
          if _c['control']['draft'] == 'yes':
            del _c['control']
            list_it(d, 'draft', _c)
            continue
          # TODO possible other control value?
        list_it(d, scheme, _c)
      else:
        list_it(d, _tag, _c)
    elif _tag == 'content':
      d[_tag] = _c['text']
    else:
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
  for k, g in itertools.groupby(sorted(w.group().lower() for w in WORD_FREQ_RE.finditer(text) if w.group())):
    wf[k] = sum(1 for _ in g)
  
  return wf


def merge_word_freq(wf, wf1):

  for w, c in wf1.items():
    wf[w] = c + wf.get(w, 0)


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
  print('{!s:<30} <- {:5} days -> {!s:>30}'.format(f['post'][-1]['published'],
        (f['post'][0]['published'] - f['post'][-1]['published']).days,
        f['post'][0]['published']))


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
  i = 0
  for w, c in wf:
    print('{:5,} {:{w_len}}'.format(c, ddd(w, w_len), w_len=w_len), end='')
    i += 1
    print('\n' if i % N == 0 else ' ', end='')
  print()


def s_posts_comments_grouper(posts, comments, key_fmt):

  kf = lambda p: p['published'].strftime(key_fmt)
  ig_p = itertools.groupby(sorted(posts, key=kf), key=kf)
  ig_c = itertools.groupby(sorted(comments, key=kf), key=kf)

  icount = lambda i: sum(1 for _ in i)
  d_p = dict((k, icount(g)) for k, g in ig_p)
  d_c = dict((k, icount(g)) for k, g in ig_c)
  keys = d_p.keys() | d_c.keys()
  return dict((key, (d_p.get(key, 0), d_c.get(key, 0))) for key in keys)


def s_two_columns_chart(data, keys, column_names):

  max_c1_count, min_c1_count = (max(item[0] for item in data.values()),
                                min(item[0] for item in data.values()))
  max_c2_count, min_c2_count = (max(item[1] for item in data.values()),
                                min(item[1] for item in data.values()))

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
          '#'*int(bar_size[0] * count[0] / max_c1_count),
          '#'*int(bar_size[1] * count[1] / max_c2_count),
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

  keys = tuple('%d-%02d' % (year, month) \
               for year in range(min_year, max_year + 1) \
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


def s_comments(f):

  section('Comments')

  comments = list(filter(lambda c: 'in-reply-to' in c, f['comment']))
  total_comments = len(comments)
  print('{:5} out of {} Comments are not counted in this section.'.format(len(f['comment']) - total_comments, len(f['comment'])))

  posts = f['post']

  section('Top Commenters', level=2)
  kf = lambda c: c['author']['name']
  i = 0
  for count, name in sorted(
      [(sum(1 for _ in g), k) for k, g in itertools.groupby(sorted(comments, key=kf), key=kf)],
      reverse=True):
    print('{:5} ({:5.1f}%): {}'.format(count, 100 * count / total_comments, name))
    i += 1
    if i >= 10:
      break
    
  section('Most Commented Posts', level=2)
  kf = lambda c: c['in-reply-to']['ref']
  i = 0
  # FIXME BAD, BAD
  for count, ref in sorted(
      [(sum(1 for _ in g), k) for k, g in itertools.groupby(sorted(comments, key=kf), key=kf)],
      reverse=True):
    title = ddd(list(filter(lambda p: p['id'] == ref, posts))[0]['title'], 78 - 5 - 9 - 2)
    print('{:5} ({:5.1f}%): {}'.format(count, 100 * count / total_comments, title))
    i += 1
    if i >= 10:
      break
 
  section('Most Commented Posts Over Days Since Published aka. Popular Posts', level=2)
  kf = lambda c: c['in-reply-to']['ref']
  i = 0
  # FIXME BAD, SUPER BAD
  for count, post in sorted(
      [(count / (datetime.datetime.now(post['published'].tzinfo) - post['published']).days, post) for count, post in (
        (sum(1 for _ in g), list(filter(lambda p: p['id'] == k, posts))[0]) for k, g in itertools.groupby(sorted(comments, key=kf), key=kf))],
      key=lambda item: item[0],
      reverse=True):
    title = ddd(post['title'], 78 - 5 - 2)
    print('{:.3f}: {}'.format(count, title))
    i += 1
    if i >= 10:
      break
 

def s_labels(f):

  section('General')

  labels = sorted(((sum(1 for _ in g), k) for k, g in itertools.groupby(sorted(itertools.chain.from_iterable(p.get('label', []) for p in f['post'])))), reverse=True)
  total_labels = len(f['label'])
  total_labeled = sum(count for count, label in labels)
  print('{:10,} Labels labled {:10,} times {:10.3f} Labeled per label'.format(total_labels, total_labeled, total_labeled / total_labels))

  section('Most Labeled Labels', level=2)
  i = 0
  for count, label in labels:
    print('{:5} ({:5.1f}%): {}'.format(count, 100 * count / total_labeled, label))
    i += 1
    if i >= 10:
      break

  section('Least Labeled Rate', level=2)
  labels = sorted(((sum(1 for _ in g), k) for k, g in itertools.groupby(sorted(itertools.chain.from_iterable(p.get('label', []) for p in f['post'])))))
  i = 0
  for count, labels2 in itertools.groupby(labels, key=lambda l: l[0]):
    labels_count = sum(1 for _ in labels2)
    print('{:5} ({:5.1f}%) Labels labeled {:3} times'.format(labels_count, 100 * labels_count / total_labels, count))
    i += 1
    if i >= 10:
      break


def main():

  filename = sys.argv[1]
  filename_cache = filename + '.cache'
  cache = shelve.open(filename_cache)
  if 'feed' in cache and cache.get('CACHE_VERSION', None) == CACHE_VERSION:
    f = cache['feed']
  else:
    d = etree.parse(filename)
    r = d.getroot()
    f, t = to_dict(r)
    cache['feed'] = f
    cache['CACHE_VERSION'] = CACHE_VERSION
    # XXX not really a json file, just for syntax highlighting
    with open(filename + '.json', 'w') as json_file:
      import pprint
      pprint.pprint(f, json_file)

  # generate list of labels, if not preset. Sometime between 12/03/2012 and
  # 07/01/2012, labels are removed from exported file.
  if 'label' not in f:
    f['label'] = list(set(itertools.chain.from_iterable(p.get('label', []) for p in f['post'])))

  section('{} {}'.format(__program__, __version__), 0)
  print(' ', f['title'], 'by', f['author']['name'])
  print(' ', ddd(list(filter(lambda s: 'BLOG_DESCRIPTION' in s['id'], f['settings']))[0]['content'], 76))

  s_general(f)
  s_posts(f)
  s_comments(f)
  s_posts_comments(f)
  s_labels(f)


if __name__ == '__main__':
  main()
