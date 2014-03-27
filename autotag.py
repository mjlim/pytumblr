#!/usr/bin/python

import pytumblr
import yaml
import os
import urlparse
import code
import oauth2 as oauth

# BEGIN CONFIG

blogname = "your-blog-name-here"
# add rules to disallow tags in here. return false if the tag is not allowed and true otherwise.
def tag_allowed(tag):
    if tag[0:2] == "my":
        return False
    return True

debug_messages = False

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



if __name__ == '__main__':
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

    posts = client.posts(blogname)[u'posts']

    for post in posts:
        tags = post[u'tags']
        if tags == []:
            # no tags assigned to this post

            if u'source_url' in post:
                # has a source; was a reblog
                source_url = post[u'source_url']
                source_url_split = source_url.split('/')
                if debug_messages:
                    print source_url
                    print source_url_split
                if len(source_url_split) < 4:
                    if debug_messages:
                        print "skipping because url not long enough" 
                    continue

                src_blog_name = source_url_split[2]
                src_post_id = source_url_split[4]

                src_blog = client.posts(src_blog_name, id=int(src_post_id))

                if u'posts' not in src_blog:
                    if debug_messages:
                        print "origin post was deleted :("
                    continue

                src_blog_post = src_blog[u'posts'][0]

                newtags = [t for t in src_blog_post[u'tags'] if tag_allowed(t)]

                if newtags == []:
                    if debug_messages:
                        print "the origin post has no tags, skipping."
                    continue

                newtags.insert(0, u'tags copied from source automatically')
                if debug_messages:
                    print newtags

                # update the original post
                mypost_id = post[u'id']
                returned = client.edit_post(blogname, id=int(mypost_id), tags=newtags)
                if debug_messages:
                    print "ret:", returned


                # done update

        if debug_messages:
            print post[u'tags']
