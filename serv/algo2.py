from collections import OrderedDict
import pickle
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize
from transformers import AutoTokenizer
import onnxruntime as ort
import serv.iops as iops
import pickle as pkl


class S2PSimilarity:
    ''' Sentence 2 Paragraph Similarity
    '''
    def __init__(self, model_file, ort_format):
        '''
           embed_data = array/np.array of embeddings
           meta_data = OrderedDict({url:{kwords:'keyword', topic:'topic', label:'label;, indexes=[indexes]]}
           rev_map = maps index_id -> url
           url can later be paths/file resource handler etc as well
        '''
        self.embd_dim = int(768)
        nltk.download('punkt')
        model_ckpt = model_file
        self.tokenizer = AutoTokenizer.from_pretrained(model_ckpt)
        self.session = ort.InferenceSession(ort_format)
        self.embed_data = np.empty((0, self.embd_dim))
        self.meta_data = {}
        self.rev_data = {}

    def load_data(self, embed_file, meta_file):
        ''' Load previous data
            Returns
              - status: Boolean
            Updates
              - self.embed_data
              - self.meta_data
        '''
        status = True
        try:
            self.embed_data = pkl.load(open(embed_file, "rb"))
            self.embed_data = np.array(self.embed_data).reshape(len(self.embed_data), -1)
        except FileNotFoundError:
            status = False

        try:
            self.meta_data = pkl.load(open(meta_file, "rb"))
            self.rev_data = {idx:key for key,value in self.meta_data.items() for idx in value['emd_indxs']}
        except FileNotFoundError:
            status = False

        return status


    def save_data(self, embed_file, meta_file):
        ''' Save state (embed and meta) into storage
            FIX: Will have consistency issue if pickling fails, with mismatched embed/meta files
            Return
              - status: Boolean
        '''
        status = True

        if not (embed_file and meta_file):
            return False

        if embed_file: pkl.dump(self.embed_data, open(embed_file, "wb"))
        else: status = False
        
        if meta_file: pkl.dump(self.meta_data, open(meta_file, "wb"))
        else: status = False

        return status


    def is_url_indexed(self, url):
        ''' Check if given url is already indexed
        '''
        if url in self.meta_data:
            ##TODO: Temprorary, remove
            #if self.meta_data[url]['emd_indxs'] == []:
            #    return False
            return True
        else:
            return False

    def check_info(self, index):
        ''' Given embedding index, return all meta info about it
        '''
        return self.rev_data[index]

    def get_embedding(self, text):
        ''' Given text, return embedding
        '''
        embedded_text = self.tokenizer(text, padding="max_length", truncation=True)
        ort_inputs = {"input_ids": np.array(embedded_text["input_ids"]).reshape(1, -1),
                      "attention_mask": np.array(embedded_text["attention_mask"]).reshape(1, -1)}
        ort_outputs = self.session.run(None, ort_inputs)
        return ort_outputs[0]


    def _chunk_text(self, text, chunk_size=200):
        ''' Internal function to chunk and embed text, returns chunked text
            TODO: Refactor this code
        '''
        sentences = sent_tokenize(text)
        idx = 0
        chunk = ""
        chunks = []
        for sentence in sentences:
            idx = idx + len(self.tokenizer.tokenize(sentence))
            chunk += sentence
            if idx >= chunk_size:
                chunks.append(chunk)
                chunk = ""
                idx = 0
        else:
            if len(chunk) == 0:
                return chunks
            chunks.append(chunk)
        return chunks


    def insert_largetext(self, url, meta_data_value, text):
        ''' Given a large text, chunk it and insert it
            chunk : Text that is broken to pieces
            chunke: A chunke that is embedded 
            Input:
             - text: parsed text
             - meta_data_value = One row of metadata, each is url -> value
              - value same as meta_data, see init
            Return
             - status: Boolean
            Updates 
             - embedded data
             - meta_data : Updated meta data, corresponding to current url
               - so this will be bunch of url -> embed1, url -> embed2 etc, since one url's text is chunked
        '''
        
        # Check if url is already inserted
        #if url in self.meta_data:
        #    return False

        # Chunk the text
        chunks = self._chunk_text(text)
        chunks_len = len(chunks)

        # Now update meta_data, incl the indexs and update rev_map, since one url/text has many chunks/embeddings
        embd_len = len(self.embed_data)
        curr_indx = max(0, embd_len-1)
        self.meta_data[url] = meta_data_value             # Update initial params, indexes updated later
        indxs = list(range(curr_indx+1, curr_indx+chunks_len+1))        # curr_indx -> curr_idx + chunks_len
        self.meta_data[url]['emd_indxs'].extend(indxs)
        self.rev_data.update({idx:url for idx in range(curr_indx+1, curr_indx + chunks_len+1)})

        # Compute embeddings and save it
        chunkes_gen = map(self.get_embedding, chunks)          # compute embedding for the chunks
        for chunke in chunkes_gen:
          self.embed_data = np.vstack([self.embed_data, chunke])

        return True

        # TODO: Then update test_phrase and find_phrase

    def find_phrase(self, phrase_embed, k_val=5, params=None):
        ''' Given a phrase embed, find sites which is closest
            phrase_embed: is given embedded phrase, for which we want to find closest data
            k_val       : 
            params      : List of string params one wants back, eg: topic, 
            return      : Tuples of site, index in embedding, sim_score
        '''
        scores = self.embed_data.dot(phrase_embed.T)
        top_idxs = np.argsort(-np.max(scores, axis=1))[:k_val] #Get max of all chunks in kword & neg for descending
        top_scores = np.sort(-np.max(scores, axis=1))[:k_val]
        top_k_urls = []
        for idx, item in enumerate(top_idxs):
            print(str(idx) + " " + str(top_scores[idx]) + " " + self.rev_data[item])
            top_k_urls.append(self.rev_data[item])
 
        #top_idxs = np.argsort(scores.flatten())
        return top_idxs, top_k_urls

    def test_phrases(self, eval_phrases, eval_embedding, eval_sites):
        ''' Given a set of eval phrases, find closest items and report metrics
        '''
        for test in eval_phrases:
            test_embed_data = sim_evltr.get_embedding(test)
        results = map(test_embed_data, sim_valtr.find_phrase(x, k_val=5))
        return results

if __name__ == "__main__":

    # C1: Case of Testing, Init
    model_file = "sentence-transformers/multi-qa-mpnet-base-dot-v1"
    ort_format = "serv/res/traced_bert.onnx"
    embed_file = "serv/res/embed_train_v02_rc.pkl"
    meta_file = "serv/res/meta_train_v02_rc.pkl"
    confsbl_file = "serv/data/confsbl_hn_url_gt_100.csv"
    eval_file = "serv/data/eval_100_samples.csv"
    rawdata_file = "serv/data/rawtext.csv"
    sim_evltr = S2PSimilarity(model_file, ort_format)
    DO_ADD_TRAIN = False
    DO_ADD_TEST = False
    DO_EVAL = True

    # C1: Insert/Load Training data (both confusable content and eval content)
    sim_evltr.load_data(embed_file, meta_file)                 # Load previously embedded data

    # C1: Insert/Load Training data (add new data)
    if DO_ADD_TRAIN:
        for idx,row in enumerate(iops.lazy_csv_reader(confsbl_file)):
            if idx == 1000:
                break
            url = row[0]                                           # Url
            if sim_evltr.is_url_indexed(url):
                print("NotProcess Test Doc", idx,": ", url)
                continue
            print("Processing Train Doc", idx,": ", url)
            meta_data_value =  {'label':'train', 'emd_indxs':[]}
            status, text = iops.extract_text_from_url(url)
            if not status: 
                print("Error in extracting text")
                continue
            sim_evltr.insert_largetext(url, meta_data_value, text) # Load new corpus of data
            iops.csv_writer(rawdata_file, url + " , " + repr(text) + "\n")

            if idx % 100 == 0:                                     # Save data after every 1000
                sim_evltr.save_data(embed_file, meta_file)

        sim_evltr.save_data(embed_file, meta_file)

    # C1: Insert/Load Test data
    if DO_ADD_TEST:
        for idx, row in enumerate(iops.lazy_csv_reader(eval_file)):
            url = row[0]
            topic = row[1]
            kwords = row[2]
            if sim_evltr.is_url_indexed(url):
                print("NotProcess Test Doc", idx,": ", url)
                continue
            print("Processing Test Doc", idx,": ", url)
            meta_data_value = {'label':'test', 'kwords':kwords, 'topic':topic, 'emd_indxs':[]}
            status, text = iops.extract_text_from_url(url)
            if not status:
                print("Error in extracting text")
                continue
            sim_evltr.insert_largetext(url, meta_data_value, text)

        sim_evltr.save_data(embed_file, meta_file)

    ### C1: For a set of phrases or their embedding, find similarity and get metrics
    if DO_EVAL:
        embd_dim = 768
        test_embed_data = np.empty((0, embd_dim))
        test_meta_data = []
        total_correct = 0
        total = 0
        for idx, row in enumerate(iops.lazy_csv_reader(eval_file)):
            test_url = row[0]
            test_topic = row[1]
            test_kwords = row[2]
            embd_data = sim_evltr.get_embedding(test_kwords)
            test_embed_data = np.vstack([test_embed_data, embd_data])
            test_pred_data, top_k_urls = sim_evltr.find_phrase(embd_data, k_val=5)
            test_meta_data.extend([test_url, test_topic, test_kwords, test_pred_data])
            
            if test_url in top_k_urls:
                total_correct += 1
            total += 1

        print(100*total_correct/total)
    ### C2: Case of Prod Use, Init
    ##model_file = "sentence-transformers/multi-qa-mpnet-base-dot-v1"
    ##ort_format = "serv/res/traced_bert.onnx"
    ##embed_file = "serv/res/prod.pkl"
    ##sim_sys = S2PSimilarity(model_file, ort_format, embed_file)

    ### C2: Case of Prod Use, Load data
    ##sim_sys.load_data()                                      # Load previously embedded data

    ### C2: Cold Start Insertion
    ##for data in datum:
    ##    sim_sys.insert_largetext(text, meta_data)            # Load new corpus of data

    ### C2: Hot Running
    ##while request:
    ##    query_embed = sim_sys.get_embedding(request.text)
    ##    res = sim_sys.find_phrase(query_embed, k_val=5)
    ##    print(res['top_sites'], res['top_contexts'])

