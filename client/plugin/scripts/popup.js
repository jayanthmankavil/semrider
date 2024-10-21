document.addEventListener('DOMContentLoaded', function() {
  var form = document.getElementById('search-form');

  form.addEventListener('submit', function(event) {
    event.preventDefault();
    var keywords = document.getElementById('keywords').value;
    var resultsCount = document.getElementById('results').value;

    searchAPI(keywords, resultsCount);
  });
});

function searchAPI(keywords, resultsCount) {
  var url = 'http://localhost:5000/search';

  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 'question':keywords, 'number_of_results':resultsCount })
  })
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      displayResults(data.top_sites, data.top_context, data.top_titles);
    })
    .catch(function(error) {
      console.error('Error:', error);
    });
}

function truncateText(text, maxLength) {
  if (text.length > maxLength) {
    return text.substring(0, maxLength) + '...';
  }
  return text;
}

function extractDomain(url) {
  var domain = (new URL(url)).hostname;

  // TODO: Handle URL Exception for malformed url
  if (domain.startsWith('www.')) {
    domain = domain.substring(4); 
  }
  return domain;
}



function displayResults(top_sites, top_context,top_titles) {
  var resultsContainer = document.getElementById('results-container');
  resultsContainer.innerHTML = '';

  // TODO: Instead of fixed truncatation threshold, use relative to window size
  const maxTitleLength = 15;
  const maxUrlLength = 20;

  for (var i = 0; i < top_sites.length; i++) {
    var item = top_sites[i];
    var title = top_titles[i] || extractDomain(item);
    var value = top_context[i];
    var truncatedTitle = truncateText(title, maxTitleLength);
    var truncatedUrl = truncateText(extractDomain(item), maxUrlLength);
    var resultNumb = document.createElement('div');
    resultNumb.textContent = (i+1) + '. ';
    //, Matches: ' + value;
    var resultTitle = document.createElement('span');
    resultTitle.textContent = truncatedTitle + ' - ';

    var resultText = document.createElement('a');
    resultText.setAttribute('href', item);
    resultText.textContent = truncatedUrl;

    resultsContainer.appendChild(resultNumb).appendChild(resultTitle);
    resultNumb.appendChild(resultText);
    //resultsContainer.appendChild(resultText);
    
    // Begin of Maheswaran's Old Code
    /*
    var resultText = document.createElement('a');
    var createAText = document.createTextNode(item);
    resultText.setAttribute('href', item);
    resultText.appendChild(createAText);

    resultsContainer.appendChild(resultNumb).appendChild(resultText);
    */
  }
}
