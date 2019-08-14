import shutil
import copy
import nl_core_news_sm
import sys
from path import Path
import os.path
from pytorch_pretrained_bert import BertTokenizer, BertModel

import load_utils
import analysis_utils as analysis
import algorithm_utils as algorithm
import naf_utils as naf
import embeddings_utils as emb_utils
import config
    
################## Run iteration 1 or 2 or more #########################

def run_embeddings_system(factor_combo, data, id_embeddings, ids, iteration, naf_folder, nl_nlp, graph_filename):
    refined_news_items=copy.deepcopy(data)
    m2id=algorithm.construct_m2id(refined_news_items)
    new_ids=algorithm.cluster_identities(m2id, 
                                         id_embeddings)
    assert len(new_ids)==len(ids), 'Mismatch between old and new ids. Old=%d; new=%d' % (len(ids), 
                                                                                         len(new_ids))
    refined_news_items=algorithm.replace_identities(refined_news_items,
                                                    new_ids)

    # ANALYZE
#    inspect_data(refined_news_items)

    naf_iter = naf_folder / str(iteration)
    naf.create_nafs(naf_iter, 
                    refined_news_items, 
                    nl_nlp)

    naf.add_ext_references_to_naf(refined_news_items,
                               f'iteration{iteration}',
                               naf_folder / str(iteration-1),
                               naf_iter)

    algorithm.generate_graph(refined_news_items, graph_filename)

    ids=analysis.inspect_data(refined_news_items, graph_filename)
    
    return refined_news_items, ids

if __name__=="__main__":

    # LOAD CONFIG DATA
    all_factors=config.factors # all factors that we will use to distinguish identity in our baseline graphs
    bert_model=config.bert_model
    prefix=config.uri_prefix
    entity_layer=config.naf_entity_layer
    ner_system=config.ner

    system_name=config.sys_name  
  
    data_dir=Path(config.data_dir)
    input_dir=Path(config.input_dir)
    sys_dir=Path(config.sys_dir)
   
    if not os.path.exists(data_dir):
        data_dir.mkdir() 

    naf_dir=Path('%s/%s/naf' % (sys_dir, system_name))
    el_file=Path('%s/%s/el.pkl' % (sys_dir, system_name))
    graphs_file=Path('%s/%s/graphs.graph' % (sys_dir, system_name))

    if os.path.exists(naf_dir):
        shutil.rmtree(str(naf_dir))
    naf_dir.mkdir()

    # LOAD MODELS
    
    # Load pre-trained model tokenizer (vocabulary)
    tokenizer = BertTokenizer.from_pretrained(bert_model, 
                                              do_lower_case=False)
    print('BERT tokenizer loaded')

    # Load pre-trained model (weights)
    model = BertModel.from_pretrained(bert_model)
    print('BERT model loaded')
    
    nl_nlp=nl_core_news_sm.load()

    # ------ Generate NAFs and fill classes with entity mentions (Steps 1 and 2) --------------------

    #TODO: COMBINE NAFs with classes processing to run spacy only once!
    news_items_with_entities=load_utils.get_docs_with_entities(str(data_dir),
                                                               str(input_dir),
                                                               nl_nlp,
                                                               ner_system)

    naf_empty=naf_dir / 'empty'
    naf.create_nafs(naf_empty, news_items_with_entities, nl_nlp, ner_system)

    naf0=naf_dir / '0' # NAF folder before iteration 1
    if ner_system=='gold':
        naf.add_ext_references_to_naf(news_items_with_entities,
				       'gold',
				       naf_empty,
				       naf0)

    # ------- Run embeddings system -----------------

    iteration=1
    # BERT embeddings
    sent_embeddings=emb_utils.get_sentence_embeddings(naf_dir, 
                                                      iteration, 
                                                      model, 
                                                      tokenizer)
    print(sent_embeddings['Leipzig'].keys())
    id_embeddings=emb_utils.sent_to_id_embeddings(sent_embeddings, 
                                                  data)

    data, ids = run_embeddings_system(factor_combo, 
                                    data, 
                                    id_embeddings, 
                                    ids, 
                                    iteration, 
                                    naf_dir,
                                    nl_nlp,
                                    graphs_file)

        
