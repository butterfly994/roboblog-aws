import random
import boto3
import datetime
import os
import base64
import urllib3
from boto3.dynamodb.conditions import Attr

def hasEndPunctuation(key):
    words = key.split(' ')
    word1 = words[0]
    word2 = words[1]
    word3 = words[2]
    if word1[-1] in '.?!':
        return True
    if word2[-1] in '.?!':
        return True
    if word3[-1] in '.?!':
        return True
    return False


def nextWords(table, current, starters, sentenceLen):
    """
    transition to the next state semi-randomly, taking into account the number of occurences of each transition
    additionally, control sentence length by weighting keys with end punctuation more as the sentence gets longer
    return a tuple where the second element indicates whether a random restart was required or not.
    """
    tableEntry = table.get_item(Key={'prefix': current})
    if tableEntry.get('Item'):
        dictEntry = tableEntry['Item'].get('suffixes')
    else:
        dictEntry = None

    # random restart if we lost the chain
    if dictEntry is None:
        return (starters[random.randint(0, len(starters) - 1)], True)

    sum = 0
    for suffix in dictEntry:
        if hasEndPunctuation(suffix):
            sum += (dictEntry[suffix] + sentenceLen)
        else:
            sum += dictEntry[suffix]

    randInt = random.randint(1, sum)
    next = ''
    for suffix in dictEntry:
        if hasEndPunctuation(suffix):
            randInt -= (dictEntry[suffix] + sentenceLen)
        else:
            randInt -= dictEntry[suffix]
        next = suffix
        if randInt <= 0:
            break

    return (next, False)


def getSpecials(table, attr):
    scan_kwargs = {
        'FilterExpression': Attr(attr).eq(True),
        'ProjectionExpression': "prefix"
    }

    specials = []
    done = False
    start_key = None
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = table.scan(**scan_kwargs)
        specials.extend(list(map(lambda el: list(el.values())[0], response.get('Items', []))))
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None

    return specials


def generateText(table, wordCount):
    # generate a random sample fitting roughly the specified word count
    starters = getSpecials(table, 'starter')
    enders = getSpecials(table, 'ender')

    randStarterIndex = random.randint(0, len(starters) - 1)
    current = starters[randStarterIndex]
    if current[0:3] == '<p>':
        string = current + ' '
    else:
        string = '<p>' + current + ' '
    sentenceLen = 0
    for i in range(0, wordCount - 3, 3):
        addition, random_restarted = nextWords(table, current, starters, sentenceLen)
        if random_restarted:
            string = string[:-1] if string[-1] != '>' else string  # remove the last if not part of an end tag
            string += '. ' + addition + ' '
        else:
            string += addition + ' '
        current = addition

        if not hasEndPunctuation(addition):
            sentenceLen += 3
        else:
            sentenceLen = 0

    randEnder = enders[random.randint(0, len(enders) - 1)]
    if randEnder[-3:] == '</p>':
        return string + randEnder
    else:
        return string + randEnder + '</p>'


def lambda_handler(event, context):
    randomLength = random.randint(1000, 2000)
    dynamo_db = boto3.resource('dynamodb')
    table = dynamo_db.Table(os.environ['DYNAMO_DB_NAME'])
    text = generateText(table, randomLength)
    now = datetime.datetime.now()
    todayTitle = now.strftime("%m/%d/%Y")

    ssm = boto3.client('ssm', region_name=os.environ['AWS_REGION'])
    wp_pwd = ssm.get_parameter(Name='WP_PWD', WithDecryption=True)['Parameter']['Value']
    auth = 'Basic ' + str(base64.b64encode(b'user:%s' % wp_pwd.encode('utf-8')), 'utf-8')
    headers = {'Authorization': auth}
    body = {'title': todayTitle,
            'content': text,
            'author': 1,
            'format': 'standard',
            'status': 'publish',
            'tags': 5,
            'categories': 6}
    http = urllib3.PoolManager()
    # change http to https for the last how-to
    r = http.request('POST', 'http://%s/wp-json/wp/v2/posts' % os.environ['WP_IP'], headers=headers, fields=body)

    return {
        'statusCode': r.status
    }
