import boto3
import os
import time


def addChain(table, prefix, suffix):
    # add an instance of this prefix-suffix transition to the dictionary
    table_entry = table.get_item(Key={'prefix': prefix})
    if table_entry.get('Item'):
        suffixes = table_entry['Item'].get('suffixes', {})
        if suffix in suffixes:
            suffixes[suffix] += 1
        else:
            suffixes[suffix] = 1
    else:
        suffixes = {suffix: 1}

    # reset ttl to 7 days from now
    new_ttl = int(time.time()) + 7*60*60*24
    table.update_item(Key={'prefix': prefix},
                      UpdateExpression='set suffixes=:r, #ts=:t',
                      ExpressionAttributeValues={
                          ':r': suffixes,
                          ':t': new_ttl
                      },
                      ExpressionAttributeNames={
                          "#ts": "ttl"
                      })


def buildDict(table, sample):
    # prefixes and suffixes are each three words long
    # additionally, keep track of keys that are the start of a sentence and keys that are the end of a sentence
    wordList = sample.split(' ')
    for i in range(len(wordList) - 6):
        key = wordList[i] + ' ' + wordList[i + 1] + ' ' + wordList[i + 2]
        if i != 0:
            prev = wordList[i - 1]
            if len(prev) != 0 and prev[len(prev) - 1] in '?!.':
                table.update_item(Key={'prefix': key},
                                  UpdateExpression='set starter=:b',
                                  ExpressionAttributeValues={
                                      ':b': True,
                                  })

        value = wordList[i + 3] + ' ' + wordList[i + 4] + ' ' + wordList[i + 5]
        last = wordList[i + 5]
        if len(last) != 0 and last[len(last) - 1] in '?!.':
            table.update_item(Key={'prefix': key},
                              UpdateExpression='set ender=:b',
                              ExpressionAttributeValues={
                                  ':b': True,
                              })

        addChain(table, key, value)


def lambda_handler(event, context):
    dynamo_db = boto3.resource('dynamodb')
    table = dynamo_db.Table(os.environ['DYNAMO_DB_NAME'])
    for sqs_message_event in event['Records']:
        text = sqs_message_event['body']
        buildDict(table, text)

    return {
        'statusCode': 200
    }

