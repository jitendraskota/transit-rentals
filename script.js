document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('search-form');
  const addressInput = document.getElementById('address');
  const resultsContainer = document.getElementById('results');

  // Initialize Google Places Autocomplete
  const autocomplete = new google.maps.places.Autocomplete(addressInput, {
    types: ['geocode'], // Restrict to geocode results
    componentRestrictions: { country: 'us' } // Restrict to US addresses
  });

  autocomplete.addListener('place_changed', () => {
    const place = autocomplete.getPlace();
    if (!place.geometry) {
      console.warn("Autocomplete returned no geometry. Ensure the address is valid.");
    }
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const address = addressInput.value;
    const radius = document.getElementById('radius').value || 2000; // Default radius is 2000 miles
    const limit = document.getElementById('limit').value || 10; // Default limit is 10 results
    console.log("Sending data:", { address, radius, limit }); // Log the data
      
    if (!address) {
      resultsContainer.innerHTML = "<p>Please enter a valid address.</p>";
      return;
    }

    try {
      // Send a POST request to the backend
      const response = await fetch('http://127.0.0.1:5000/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address, radius, limit }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to fetch results");
      }

      const data = await response.json();
      displayResults(data);
    } catch (error) {
      resultsContainer.innerHTML = `<p>Error: ${error.message}</p>`;
    }
  });

  // Display results in the results container
  function displayResults(data) {
    if (!data || data.length === 0) {
      resultsContainer.innerHTML = "<p>No results found.</p>";
      return;
    }

    // Generate HTML for results
    resultsContainer.innerHTML = '<ul>' +
      data.map(item =>
        `<li>
          <strong>${item.id || "N/A"}</strong><br>
          Price: $${item.price || "N/A"}<br>
          Average Distance to public transit: ${item.Distance || "N/A"} miles
        </li>`
      ).join('') +
      '</ul>';
  }
});
