import requests
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from string import punctuation

def extract_text_from_url(url):
    ''' Extract text from HTML and generate a summary using word frequencies and sentence scoring.
        Returns:
            status: Boolean
            result: If status is True, result will be the summary text. If status is False, result will contain an error message.
    ''' 
    try:
        # Fetch HTML content from the URL
        response = requests.get(url.strip())
        html_content = response.text
        
        # Parse HTML content using BeautifulSoup
        bs_html_parser = BeautifulSoup(html_content, 'html.parser')
        
        # Extract text from the parsed HTML
        text = bs_html_parser.get_text()
        
        # Tokenize the text into words
        tokens = word_tokenize(text)
        
        # Remove stopwords and punctuation
        stop_words = set(stopwords.words('english'))
        punctuation_set = set(punctuation)
        
        filtered_tokens = [word.lower() for word in tokens if word.lower() not in stop_words and word.lower() not in punctuation_set]
        
        # Calculate word frequencies
        word_frequencies = {}
        for word in filtered_tokens:
            if word not in word_frequencies:
                word_frequencies[word] = 1
            else:
                word_frequencies[word] += 1
        
        # Normalize word frequencies
        max_frequency = max(word_frequencies.values())
        for word in word_frequencies:
            word_frequencies[word] /= max_frequency
        
        # Tokenize the text into sentences
        sentences = sent_tokenize(text)
        
        # Score each sentence based on the sum of word frequencies
        sentence_scores = {}
        for sentence in sentences:
            sentence_tokens = word_tokenize(sentence.lower())
            score = sum(word_frequencies[word] for word in sentence_tokens if word in word_frequencies)
            sentence_scores[sentence] = score
        
        # Select the top sentences for summary
        select_length = int(len(sentences) * 0.2)  # Select top 20% of sentences
        summary_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:select_length]
        
        # Combine selected sentences to form the summary
        summary = ' '.join(summary_sentences)
        
        return True, summary
    
    except Exception as e:
        return False, "Unable to extract text and summarize from URL."

# Example usage
if __name__ == "__main__":
    url = "https://medium.com/about"
    status, result = extract_text_from_url(url)
    if status:
        print("Summary:")
        print(result)
    else:
        print("Error:", result)
