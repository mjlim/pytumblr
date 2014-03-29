#!/usr/bin/python

import pytumblr
import yaml
import os
import argparse
import urlparse
import code
import oauth2 as oauth

# BEGIN CONFIG

# add rules to disallow tags in here. return false if the tag is not allowed and true otherwise.
def tag_allowed(tag):
    tag = tag.lower()
    if tag[0:2] == u"my" or u"my" in tag.split():
        return False
    if tag in [u'funny', u'meme', u'lol', u'win']:
        return False
    return True

# return true if this tag should always be shown regardless of threshold.
def tag_bypass_threshold(tag):
    if tag[:3] == u"tw:" or tag[:3] == u"tw ": # always include trigger warnings
        return True
    if u"spoiler" in tag: # always include spoiler tags
        return True
    if u"warning" in tag: # include anything that has 'warning'
        return True
    if u"nsf" in tag:
        return True

    return False

debug_messages = True
commit_new_tags = True
num_posts_to_read = 20
redo_autotags = False
start_threshold = 3
min_threshold = 3
reblog_recursion_depth = 35
num_notes_origin = 50

# specify a different tag weight for tags coming from certain blogs.
blog_tag_weight = {
        u'blogname1': 2,
        u'blogname2': 2
        }

# END CONFIG

def new_oauth(yaml_path):
    '''
    Return the consumer and oauth tokens with three-legged OAuth process and
    save in a yaml file in the user's home directory.
    '''

    print 'Retrieve consumer key and consumer secret from http://www.tumblr.com/oauth/apps'
    consumer_key = raw_input('Paste the consumer key here: ')
    consumer_secret = raw_input('Paste the consumer secret here: ')

    request_token_url = 'http://www.tumblr.com/oauth/request_token'
    authorize_url = 'http://www.tumblr.com/oauth/authorize'
    access_token_url = 'http://www.tumblr.com/oauth/access_token'

    consumer = oauth.Consumer(consumer_key, consumer_secret)
    client = oauth.Client(consumer)

    # Get request token
    resp, content = client.request(request_token_url, "POST")
    request_token =  urlparse.parse_qs(content)

    # Redirect to authentication page
    print '\nPlease go here and authorize:\n%s?oauth_token=%s' % (authorize_url, request_token['oauth_token'][0])
    redirect_response = raw_input('Allow then paste the full redirect URL here:\n')

    # Retrieve oauth verifier
    url = urlparse.urlparse(redirect_response)
    query_dict = urlparse.parse_qs(url.query)
    oauth_verifier = query_dict['oauth_verifier'][0]

    # Request access token
    token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'][0])
    token.set_verifier(oauth_verifier)
    client = oauth.Client(consumer, token)

    resp, content = client.request(access_token_url, "POST")
    access_token = urlparse.parse_qs(content)

    tokens = {
        'consumer_key': consumer_key,
        'consumer_secret': consumer_secret,
        'oauth_token': access_token['oauth_token'][0],
        'oauth_token_secret': access_token['oauth_token_secret'][0]
    }

    yaml_file = open(yaml_path, 'w+')
    yaml.dump(tokens, yaml_file, indent=2)
    yaml_file.close()

    return tokens

# concise way to add toggleable debug messages
def debug_msg(msg):
    if debug_messages:
        print msg

# get the tags present in the reblog chain up to a certain depth
def get_reblog_chain_tags(mypost, max_notes_read=50, recurse_depth=35):

    num_posts_read = 0
    num_notes_read = 0

    tagdict = {}

    next_post_ref = get_next_post_ref(mypost)

    # add tags from the origin. get info too
    origin_ref = get_origin_post_ref(mypost)
    if origin_ref != False:
        origin = get_post(origin_ref, notes_info=True)
        if origin != False:
            # use weight of 2; tags from src are worth more
            ft = get_filtered_tags_from_post(origin)
            if origin_ref[0] in blog_tag_weight: 
                add_tags_to_dict(ft, tagdict, blog_tag_weight[origin_ref[0]]*2)
            else:
                add_tags_to_dict(ft, tagdict, 2)

            # get tags from notes on origin
            for note in origin[u'notes']:
                if num_notes_read >= max_notes_read:
                    break
                if u'blog_name' not in note or u'post_id' not in note:
                    continue
                ref = (note[u'blog_name'], note[u'post_id'])
                p = get_post(ref)
                if p == False:
                    continue # skip this post- can't find it
                tags = get_filtered_tags_from_post(p)
                if ref[0] in blog_tag_weight: 
                    add_tags_to_dict(tags, tagdict, blog_tag_weight[ref[0]])
                else:
                    add_tags_to_dict(tags, tagdict)
                num_notes_read += 1



    # recursively follow reblogs for tags as well
    while num_posts_read < recurse_depth:
        if next_post_ref == False:
            debug_msg("chain broke -- no known next post")
            break
        if origin_ref != False and next_post_ref[1] == origin_ref[1]:
            debug_msg("reached origin through reblog recursion")
            break
        p = get_post(next_post_ref, True)
        if p == False:
            debug_msg("chain is broken-- couldn't get info about the next post")
            break 
        tags = get_filtered_tags_from_post(p)
        #debug_msg(str(tags))
        add_tags_to_dict(tags, tagdict)
        next_post_ref = get_next_post_ref(p)
        num_posts_read += 1

    debug_msg("notes read: {}. reblogs recursed: {}.".format(num_notes_read, num_posts_read))

    return tagdict



def get_post(ref, reblog_info=False, notes_info=False):
    (blogname, postid) = ref
    # todo: make this more elegant
    if notes_info and reblog_info:
        blog = client.posts(blogname, id=postid, reblog_info='true', notes_info='true')
    elif notes_info:
        blog = client.posts(blogname, id=postid, notes_info='true')
    elif reblog_info:
        blog = client.posts(blogname, id=postid, reblog_info='true')
    else:
        blog = client.posts(blogname, id=postid)
    if u'posts' not in blog:
        debug_msg("post not found")
        return False # post not found
    return blog[u'posts'][0]

def get_next_post_ref(post):
    if u'reblogged_from_name' in post and u'reblogged_from_id' in post:
        return (post[u'reblogged_from_name'], post[u'reblogged_from_id'])
    else:
        debug_msg("post has no next post ref: {}".format(post[u'post_url']))
        debug_msg(str(post.keys()))
        return False

def get_origin_post_ref(post):
    if u'source_url' not in post:
        debug_msg("no src url")
        return False
    source_url = post[u'source_url']
    source_url_split = source_url.split('/')
    if len(source_url_split) < 5:
        debug_msg("url not long")
        return False
    src_blog_name = source_url_split[2]
    src_post_id = source_url_split[4]
    return (src_blog_name, src_post_id)

# return a list of tags in this post, filtered to remove disallowed tags.
def get_filtered_tags_from_post(post):
    return [t.lower() for t in post[u'tags'] if tag_allowed(t)]

def add_tags_to_dict(taglist, tagdict, weight=1):
    for tag in taglist:
        if tag in tagdict:
            tagdict[tag] += weight
        else:
            tagdict[tag] = weight


#get a sorted list of tags with occurrence counts greater than or equal to a threshold.
#also include any trigger warning tags.
def get_tags_over_threshold(tagdict, threshold):
    tags = [t for t in tagdict.keys() if tagdict[t] >= threshold or tag_bypass_threshold(t)]
    # sort
    return sorted(tags, key=tagdict.get, reverse=True)

def update_post_tags(blogname, postid, tags):
    return client.edit_post(blogname, id=int(postid), tags=tags)


if __name__ == '__main__':

    argparser = argparse.ArgumentParser(description='Automatically tag posts on Tumblr.')
    argparser.add_argument('blogname', help='The name of your blog (name.tumblr.com or a custom domain)')
    argparser.add_argument('-D', '--debug-messages', action='store_true', help='Display debug messages')
    argparser.add_argument('-c', '--dont-commit-tags', action='store_false', help='Don\'t write new tags to posts')
    argparser.add_argument('-n', '--num-posts-to-tag', type=int, help='How many of your posts to be tagged, starting from the most recent')
    argparser.add_argument('-r', '--redo-autotags', action='store_true', help='Reassign tags for posts that have previously been autotagged')
    argparser.add_argument('--start-threshold', type=int, default=3, help='the number of times a tag should appear before it is included on a post. will step down towards min-threshold if no tags are found at this level. default 3.')
    argparser.add_argument('--min-threshold', type=int, default=3, help='the minimum number of times a tag should appear before it is used on a post. default 3')
    argparser.add_argument('-d', '--reblog-recursion-depth', type=int, default=15, help='The maximum number of reblogs to follow up the chain from the post you reblogged. Increases runtime but can yield better results.')
    argparser.add_argument('-N', '--num-notes-origin', type=int, default=50, help='The maximum number of notes at the origin to look at')

    args = argparser.parse_args()

    # load args into config variables. todo: design a better way to deal with these config vars
    debug_message = args.debug_messages
    commit_new_tags = args.dont_commit_tags
    num_posts_to_read = args.num_posts_to_tag
    redo_autotags = args.redo_autotags
    start_threshold = args.start_threshold
    min_threshold = args.min_threshold
    reblog_recursion_depth = args.reblog_recursion_depth
    num_notes_origin = args.num_notes_origin

    yaml_path = os.path.expanduser('~') + '/.tumblr'

    if not os.path.exists(yaml_path):
        tokens = new_oauth(yaml_path)
    else:
        yaml_file = open(yaml_path, "r")
        tokens = yaml.safe_load(yaml_file)
        yaml_file.close()

    client = pytumblr.TumblrRestClient(
        tokens['consumer_key'],
        tokens['consumer_secret'],
        tokens['oauth_token'],
        tokens['oauth_token_secret']
    )

    posts = ['not empty'] # hack to allow loop to begin
    num_posts_read = 0
    num_posts_tagged = 0
    while num_posts_read < num_posts_to_read and posts != []:
        debug_msg("requesting posts")
        posts = client.posts(args.blogname, reblog_info='true', offset=num_posts_read)[u'posts']

        for post in posts:
            if num_posts_read >= num_posts_to_read:
                break
            num_posts_read += 1
            tags = post[u'tags']
            if tags == [] or (redo_autotags and u'auto-tagged' in tags):
                debug_msg("looking for tags for this post: {}".format(post[u'post_url']))
                # no tags assigned to this post

                newtags = []
                threshold = start_threshold
                tagdict = get_reblog_chain_tags(post, max_notes_read=num_notes_origin, recurse_depth=reblog_recursion_depth)
                print tagdict

                # if no tags meet the cutoff, reduce threshold until there are tags to assign.
                while newtags == [] and threshold > 0 and threshold >= min_threshold:
                    newtags = get_tags_over_threshold(tagdict,threshold)
                    threshold -= 1
                print newtags

                if commit_new_tags:
                    if newtags == []:
                        debug_msg("No new tags found")
                        continue
                    newtags.insert(0, u'auto-tagged')

                    ret = update_post_tags(args.blogname, post[u'id'], newtags)
                    num_posts_tagged += 1
                    debug_msg("committed change, return val {}".format(ret))
    debug_msg("Finished. Your posts read: {}. Your posts tagged: {}.".format(num_posts_read, num_posts_tagged))
