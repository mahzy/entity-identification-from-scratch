import wikitextparser as wtp
import glob
import json

import classes

def shift_all(links_json, x):
    new_json={}
    for start, end in links_json.keys():
        new_start=start-x
        new_end=end-x
        new_json[tuple([new_start, new_end])]=links_json[(start, end)]
    return new_json

def get_text_and_links(wikitext):
    parsed = wtp.parse(wikitext)
    basic_info=parsed.sections[0]
    saved_links={}

    num_links=len(basic_info.wikilinks)
    for i in range(num_links):
        index=num_links-i-1
        link=basic_info.wikilinks[index]
        original_span=link.span
        start=original_span[0]
        end=original_span[1]
        target=link.target
        text=link.text
        if not target.startswith('w:'):
            basic_info[start:end]=""
            move_to_left=end-start
        else:
            basic_info[original_span[0]:original_span[1]]=text
            move_to_left=end-start-len(text)
        saved_links=shift_all(saved_links, move_to_left)
        if target.startswith('w:'):
            new_end=end-move_to_left
            saved_links[tuple([start, new_end])]=target

    return basic_info, saved_links


def create_gold_mentions(links, text):
    mentions=[]
    for offset, meaning in links.items():
        start, end=offset
        mention=text[start:end]
        obj=classes.EntityMention(
            mention=mention,
            begin_index=start,
            end_index=end,
            identity=meaning
        )
        mentions.append(obj)
    return mentions

def load_news_items(loc):
    """
    Load news items into objects defined in the classes file.
    """
    
    news_items=set()
    for file in glob.glob('%s/*.json' % loc):
        with open(file, 'r') as f:
            data=json.load(f)
        text, links=get_text_and_links(data['body'])
        news_item_obj=classes.NewsItem(
            content=text,
            title=data['title'],
            identifier=file.split('.')[0],
            collection=loc,
            gold_entity_mentions=create_gold_mentions(links, text)
        )

        news_items.add(news_item_obj)
    return news_items