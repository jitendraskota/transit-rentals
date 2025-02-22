document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('search-form');
  const addressInput = document.getElementById('address');
  const addressInput2 = document.getElementById('address2');
  const addressInput3 = document.getElementById('address3');
  const addressInput4 = document.getElementById('address4');
  const addressInput5 = document.getElementById('address5');
  const addressInput6 = document.getElementById('address6');
  const resultsContainer = document.getElementById('results');

  // Initialize Google Places Autocomplete
  const autocomplete = new google.maps.places.Autocomplete(addressInput, {
    types: ['geocode'], // Restrict to geocode results
    componentRestrictions: { country: 'us' } // Restrict to US addresses
  });
    
  const autocomplete2 = new google.maps.places.Autocomplete(addressInput2, {
  types: ['geocode'], // Restrict to geocode results
  componentRestrictions: { country: 'us' } // Restrict to US addresses
  });
      
  const autocomplete3 = new google.maps.places.Autocomplete(addressInput3, {
  types: ['geocode'], // Restrict to geocode results
  componentRestrictions: { country: 'us' } // Restrict to US addresses
  });
                          
  const autocomplete4 = new google.maps.places.Autocomplete(addressInput4, {
  types: ['geocode'], // Restrict to geocode results
  componentRestrictions: { country: 'us' } // Restrict to US addresses
      
});
    
  const autocomplete5 = new google.maps.places.Autocomplete(addressInput5, {
  types: ['geocode'], // Restrict to geocode results
  componentRestrictions: { country: 'us' } // Restrict to US addresses
      
});
    
  const autocomplete6 = new google.maps.places.Autocomplete(addressInput6, {
  types: ['geocode'], // Restrict to geocode results
  componentRestrictions: { country: 'us' } // Restrict to US addresses
      
});


  autocomplete.addListener('place_changed', () => {
    const place = autocomplete.getPlace();
    if (!place.geometry) {
      console.warn("Autocomplete returned no geometry. Ensure the address is valid.");
    }
  });
    
  autocomplete2.addListener('place_changed', () => {
  const place = autocomplete2.getPlace();
  if (!place.geometry) {
    console.warn("Autocomplete returned no geometry. Ensure the address is valid.");
  }
});
    
    
    autocomplete3.addListener('place_changed', () => {
  const place = autocomplete3.getPlace();
  if (!place.geometry) {
    console.warn("Autocomplete returned no geometry. Ensure the address is valid.");
  }
});

      autocomplete4.addListener('place_changed', () => {
  const place = autocomplete4.getPlace();
  if (!place.geometry) {
    console.warn("Autocomplete returned no geometry. Ensure the address is valid.");
  }
});

      autocomplete5.addListener('place_changed', () => {
  const place = autocomplete5.getPlace();
  if (!place.geometry) {
    console.warn("Autocomplete returned no geometry. Ensure the address is valid.");
  }
});

      autocomplete6.addListener('place_changed', () => {
  const place = autocomplete6.getPlace();
  if (!place.geometry) {
    console.warn("Autocomplete returned no geometry. Ensure the address is valid.");
  }
});


  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const address = addressInput.value;
    const address_list =[addressInput.value,addressInput2.value,addressInput3.value,addressInput4.value,addressInput5.value,addressInput6.value]; 
    //const address2 = addressInput2.value;
    //const address3 = addressInput3.value;
    //const address4 = addressInput4.value;
    //const address5 = addressInput5.value;
    //const address6 = addressInput6.value;
    const frequency_list = [document.getElementById('frequency1').value,document.getElementById('frequency2').value,document.getElementById('frequency3').value,document.getElementById('frequency4').value,document.getElementById('frequency5').value];
    //const frequency1 = document.getElementById('frequency1').value;
    //const frequency2 = document.getElementById('frequency2').value;
    //const frequency3 = document.getElementById('frequency3').value;
    //const frequency4 = document.getElementById('frequency4').value;
    //const frequency5 = document.getElementById('frequency5').value;
    const time_list = [document.getElementById('time1').value,document.getElementById('time2').value,document.getElementById('time3').value,document.getElementById('time4').value,document.getElementById('time5').value];
    //const time1 = document.getElementById('time1').value;
    //const time2 = document.getElementById('time2').value;
    //const time3 = document.getElementById('time3').value;
    //const time4 = document.getElementById('time4').value;
    //const time5 = document.getElementById('time5').value;
    const radius = document.getElementById('radius').value || 20; // Default radius is 20 miles
    const limit = document.getElementById('limit').value || 10; // Default limit is 10 results
    console.log("Sending data:", { address_list, frequency_list, time_list, radius, limit }); // Log the data
      
      
    //Need to edit further for the POST process
      
    if (!address) {
      resultsContainer.innerHTML = "<p>Please enter a valid address.</p>";
      return;
    }

    try {
      // Send a POST request to the backend
      const response = await fetch('http://127.0.0.1:5000/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address_list, frequency_list, time_list, radius, limit }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to fetch results");
      }

      const data = await response.json();
      console.log(data[0]);  // Log the first element in the array to inspect it
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
          <strong>${item.Address || "N/A"}</strong><br>
          Price: $${item.Price || "N/A"}<br>
          Bedrooms: ${item.Bedrooms || "N/A"}<br>
          Bathrooms: ${item.Bathrooms || "N/A"}<br>
          Square Footage: ${item.SquareFootage || "N/A"}<br>
          Utility Score: ${item.Utility_Score || "N/A"}
        </li>`
      ).join('') +
      '</ul>';
  }
});
