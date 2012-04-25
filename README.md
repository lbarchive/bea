Blogger Export Analyzer
=======================

Blogger Export Analyzer (BEA) is a simple analyzer for Blogger Export XML file. BEA is intended to be used for generating one long page of analysis.


Usage
-----

    ./bea.py blog-MM-DD-YYYY.xml


Sample output
-------------

    = Blogger Export Analyzer <x.y.z> ============================================

      <Blog Name> by <Blog Owner>
      <Blog Description>

    - General --------------------------------------------------------------------

           941 Posts       261.190 per year   21.766 per month
           395 Comments    109.639 per year    9.137 per months  0.420 per post
             2 Pages
             0 Drafts
         2,063 Labels

    First post                     <-  3.6 years ->                      Last post
    <Post Title>                   <-  43 months ->                   <Post Title>
    2008-09-13 16:13:00-07:00      <-  1315 days ->      2012-04-21 10:08:00-07:00

    - Posts ----------------------------------------------------------------------

       941 Posts    899 Updated (after 256 days, 14:30:00.346941 in average)

       250,853 Words     266.581 per post
     1,339,093 Chars   1,423.053 per post
         5,021 Labels      5.336 per post


    - 266 most used words --------------------------------------------------------

    8,234 i       7,205 the     7,128 to      4,752 a       4,340 you    
    4,298 is      3,499 and     3,242 it      2,904 of      2,693 in     
    <SNIP>

    - Comments -------------------------------------------------------------------

       34 out of 395 Comments are not counted in this section.

    . Top Commenters .............................................................

      126 ( 34.9%): <Commenter Name>
    <SNIP>
        3 (  0.8%): <Commenter Name>

    . Most Commented Posts .......................................................

       34 (  9.4%): <Post Title>
    <SNIP>
        8 (  2.2%): <Post Title>

    . Most Commented Posts Over Days Since Published aka. Popular Posts ..........

    0.500: <Post Title>
    <SNIP>
    0.037: <Post Title>

    - Posts and Comments Published Time ------------------------------------------


    . By Year and Month ..........................................................

    YYYY-MM  Posts                             |                          Comments
    2008-09  18                           #####|                                 1
    2008-10  25                        ########|##                               6
    <SNIP>
    2012-03  94 ###############################|#########                       20
    2012-04  65           #####################|############                    26

    . By Year ....................................................................

    Year Posts                               |                            Comments
    2008 151             ####################|############################      81
    2009 192       ##########################|################################# 93
    2010 236 ################################|##############################    86
    2011 145              ###################|#########################         72
    2012 217    #############################|######################            63

    . By Month of Year ...........................................................

    Month  Posts                              |                           Comments
      01    90           #####################|###########                      30
      02   114     ###########################|################                 42
    <SNIP>
      11   126  ##############################|#############                    35
      12    77              ##################|################################ 81

    . By Day of Month ............................................................

    Day  Posts                               |                            Comments
     01  29              ####################|########                          11
     02  38       ###########################|###                                4
    <SNIP>
     30  22                   ###############|#######                           10
     31  22                   ###############|#####                              7

    . By Hour of Day .............................................................

    Hour Posts                               |                            Comments
     01  29              ####################|########                          11
     02  38       ###########################|###                                4
    <SNIP>
     23  32            ######################|#############                     17
     24  30             #####################|#######                           10

    - General --------------------------------------------------------------------

         2,063 Labels labled      5,021 times      2.434 Labeled per label

    . Most Labeled Labels ........................................................

      117 (  2.3%): <Label>
       95 (  1.9%): <Label>
    <SNIP>
       53 (  1.1%): <Label>
       51 (  1.0%): <Label>

    . Least Labeled Rate .........................................................

     1403 ( 68.0%) Labels labeled   1 times
      302 ( 14.6%) Labels labeled   2 times
    <SNIP>
       14 (  0.7%) Labels labeled   9 times
        4 (  0.2%) Labels labeled  10 times

License
-------

    Copyright (c) 2012 Yu-Jie Lin
    This program is licensed under the MIT License, see COPYING
