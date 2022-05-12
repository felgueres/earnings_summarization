import sys
sys.path.append('./')
import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from nltk.tokenize import sent_tokenize
from flask import jsonify
import re
import json
import pandas as pd
import argparse 
from service import Service 
from schema import schema

SUMMARY_COLLECTION = 'summaryV1'
HEADERS = ('section','role', 'start_idx', 'end_idx', 'content', 'tokens')

def count_tokens(text: str, tokenizer = AutoTokenizer.from_pretrained("sshleifer/distilbart-cnn-12-6")) -> int:
    """count the number of tokens in a string"""
    return len(tokenizer.encode(text))

def extract_participants(config):
    """Extract the sections of a transcript, discarding the operator instructions and low information sections
    """
    if len(config.get('text',0)) ==0:
        return []
    participants = {'operator': {'role':'operator', 'idxs':[]}}
    people = re.findall(".* - .*", config.get('text'))
    assert len(people) > 0 
    for p in people:
        name_role = p.split('-')
        participants[name_role[0].strip()] = {'role': name_role[1].strip()}
    
    config['participants'] = participants
    
    return config 

def relative_lowest(val, li):
    '''Find the minimum value within iterable `li` that is greater than value `val`
    '''
    li=list(filter(lambda x: x>val, li))
    if li:
        return min(li)
    else:
        return 99999

def participant_pointers(config):
    '''Get the section pointers for each participants and Q&A
    '''
    participants_regex = list(zip([re.compile(k.lower()) for k in config.get('participants').keys()], config.get('participants').keys()))
    qanda = re.compile('question.*answer') 
    idxs = []
    for i, sentence in enumerate(config['text'].split('\n\n')):
        if qanda.search(sentence.lower()):
            config['qanda'] = i
        for reg, name in participants_regex:
            if reg.search(sentence.lower().strip()) and len(name.split(' ')) == len(sentence.split(' ')):
                idxs.append(i)
                if config['participants'].get(name).get('idx', None) is None:
                    config['participants'].get(name)['idx']=[i]
                else:
                    config['participants'].get(name)['idx'].append(i)
                break
    print('IDXs {}'.format(idxs))
    config['idxs'] = idxs
    return config

def sections(config):
    for p in config.get('participants').keys():
        sections = []
        idx = config.get('participants').get(p).get('idx')
        if idx:
            for i in idx:
                sections.append((i, relative_lowest(i,config.get('idxs'))))
            config.get('participants').get(p)['sections'] = sections
        else:
            pass
    return config


def sentence_chunker(sentences, max_size=450):
    '''Greedily constructs paragraphs of max_size tokens. Returns indeces only.
    '''
    ntokens = 0
    idxs = []
    for i, s in enumerate(sentences):
        if max_size > ntokens + count_tokens(s):
            ntokens += count_tokens(s) 
        else:
            idxs.append(i)
            ntokens = 0
    idxs.append(len(sentences))

    output = []
    cur_idx = 0
    for i,idx in enumerate(idxs):
        output.append((cur_idx,idx))
        cur_idx = idx
    return output

def participant_sections(config):
    article = config.get('text').split('\n\n')
    outputs = [HEADERS]
    for p in config.get('participants').keys():
        sections = config.get('participants').get(p).get('sections')
        if sections:
            business_outlook = [(s,e) for (s,e) in config.get('participants').get(p).get('sections') if s < config.get('qanda')]
            question_session = [(s,e) for (s,e) in config.get('participants').get(p).get('sections') if s >= config.get('qanda')]
            role = config.get('participants').get(p).get('role')
            if business_outlook:
                outputs += [('outlook', role, s+1, e, article[s+1:e], count_tokens(' '.join(article[s+1:e]))) for (s,e) in business_outlook]
            if question_session:
                outputs += [('qanda', role, s+1, e, article[s+1:e],count_tokens(' '.join(article[s+1:e]))) for (s,e) in question_session]
        else:
            pass
    return outputs

def _summarizer():
    return pipeline('summarization', do_sample=False, tokenizer = AutoTokenizer.from_pretrained("sshleifer/distilbart-cnn-12-6"), model = AutoModelForSeq2SeqLM.from_pretrained("sshleifer/distilbart-cnn-12-6"))


def summarize(text, max_length=150, summarizer = _summarizer()):
    text = ' '.join(text)
    sentences = sent_tokenize(text)
    idxs = sentence_chunker(sentences)
    chunked = [' '.join(sentences[s:e]) for (s,e) in idxs]
    summaries = summarizer(chunked, max_length=max_length)
    summary = ' '.join([s.get('summary_text') for s in summaries])
    return summary 

def read_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data

def build_dataframe(outputs):
    df = pd.DataFrame(outputs[1:], columns=outputs[0])
    df['summary'] = df.apply(lambda row: summarize(row.content) if row.tokens >150 else row.content, axis = 1)
    return df

def join_path(source_path, sub_path):
    return os.path.join(source_path, sub_path)

def _config(args):
    path = join_path(args.path, '{}.json'.format(args.cik))
    data = read_json(path) # first item in the list 
    text = data.get('text')
    source = data.get('source')
    cik = data.get('cik')
    assert str(args.cik) == cik
    return {'data': data, 'text': text, 'source': source, 'cik': cik } 

if __name__ == '__main__':
    args = argparse.ArgumentParser(description='Summarize an Earnings Call')
    args.add_argument('--cik', type=int)
    args.add_argument('--path', default='/Users/pablo/Desktop/transcripts/')
    args = args.parse_args()
    config = _config(args)
    config = extract_participants(config)
    config = participant_pointers(config)
    config = sections(config)
    outputs = participant_sections(config)
    df = build_dataframe(outputs) 
    for i, row in list(df.iterrows()):
        entry = row.to_dict()
        entry.update(config)
        print(Service('am').write(entry=entry, collection=SUMMARY_COLLECTION, schema=schema.EarningsCallSchema))
