# autotag

Uses pytumblr to automatically assign tags to your most recent posts. 
```
$ python autotag.py -h
Automatically tag posts on Tumblr.

positional arguments:
  blogname              The name of your blog (name.tumblr.com or a custom
                        domain)

optional arguments:
  -h, --help            show this help message and exit
  -D, --debug-messages  Display debug messages
  -c, --dont-commit-tags
                        Don't write new tags to posts
  -n NUM_POSTS_TO_TAG, --num-posts-to-tag NUM_POSTS_TO_TAG
                        How many of your posts to be tagged, starting from the
                        most recent
  -r, --redo-autotags   Reassign tags for posts that have previously been
                        autotagged
  --start-threshold START_THRESHOLD
                        the number of times a tag should appear before it is
                        included on a post. will step down towards min-
                        threshold if no tags are found at this level. default
                        3.
  --min-threshold MIN_THRESHOLD
                        the minimum number of times a tag should appear before
                        it is used on a post. default 3
  -d REBLOG_RECURSION_DEPTH, --reblog-recursion-depth REBLOG_RECURSION_DEPTH
                        The maximum number of reblogs to follow up the chain
                        from the post you reblogged. Increases runtime but can
                        yield better results.
  -N NUM_NOTES_ORIGIN, --num-notes-origin NUM_NOTES_ORIGIN
                        The maximum number of notes at the origin to look at
```

You can create rules to handle certain tags (exclude or always include) by modifying the functions near the top of autotag.py. You can also add bias towards or against tags from certain blogs in the blog_tag_weight dict.


# PyTumblr

[![Build Status](https://travis-ci.org/tumblr/pytumblr.png?branch=master)](https://travis-ci.org/tumblr/pytumblr)

## Create a client

A `pytumblr.TumblrRestClient` is the object you'll make all of your calls to the
Tumblr API through.  Creating one is this easy:

``` python
client = pytumblr.TumblrRestClient(
    '<consumer_key>',
    '<consumer_secret>',
    '<oauth_token>',
    '<oauth_secret>',
)

client.info() # Grabs the current user information
```

Two easy ways to get your credentials to are:

1.  The built-in `interactive_console.py` tool (if you already have a consumer key & secret)
2.  The Tumblr API console at https://api.tumblr.com/console

## Supported Methods

### User Methods

``` python
client.info() # get information about the authenticating user
client.dashboard() # get the dashboard for the authenticating user
client.likes() # get the likes for the authenticating user
client.following() # get the blogs followed by the authenticating user

client.follow('codingjester.tumblr.com') # follow a blog
client.unfollow('codingjester.tumblr.com') # unfollow a blog

client.like(id, reblogkey) # like a post
client.unlike(id, reblogkey) # unlike a post
```

### Blog Methods

``` python
client.blog_info('codingjester') # get information about a blog
client.posts('codingjester', **params) # get posts for a blog
client.avatar('codingjester') # get the avatar for a blog
client.blog_likes('codingjester') # get the likes on a blog
client.followers('codingjester') # get the followers of a blog
client.queue('codingjester') # get the queue for a given blog
client.submission('codingjester') # get the submissions for a given blog
```

### Post Methods

``` python
client.edit_post(blogName, **params); # edit a post

client.reblog(blogName, id, reblogkey); # reblog a post

client.delete_post(blogName, id); # delete a post

# some helper methods for creating posts of varying types
client.create_photo(blogName, **params)
client.create_quote(blogName, **params)
client.create_text(blogName, **params)
client.create_link(blogName, **params)
client.create_chat(blogName, **params)
client.create_audio(blogName, **params)
client.create_video(blogName, **params)
```

A note on tags: When passing tags, as params, please pass them as a list (not
a comma-separated string):

``` python
client.create_text('seejohnrun', tags=['hello', 'world'], ...)
```

### Tagged Methods

```python
client.tagged(tag, **params); # get posts with a given tag
```

## Using the interactive console

This client comes with a nice interactive console to run you through the OAuth
process, grab your tokens (and store them for future use).

You'll need `pyyaml` installed to run it, but then it's just:

``` bash
$ python interactive-console.py
```

and away you go!  Tokens are stored in `~/.tumblr` and are also shared by other
Tumblr API clients like the Ruby client.

## Running tests

The tests (and coverage reports) are run with nose, like this:

``` bash
python setup.py test
```

# Copyright and license

Copyright 2013 Tumblr, Inc.

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this work except in compliance with the License. You may obtain a copy of
the License in the LICENSE file, or at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations.
