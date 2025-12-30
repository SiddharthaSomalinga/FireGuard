document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('locationForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultsSection = document.getElementById('results');
    const errorDiv = document.getElementById('error');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const latitude = parseFloat(document.getElementById('latitude').value);
        const longitude = parseFloat(document.getElementById('longitude').value);
        const areaName = document.getElementById('areaName').value || 'user_location';

        // Validate inputs
        if (isNaN(latitude) || isNaN(longitude)) {
            showError('Please enter valid latitude and longitude values.');
            return;
        }

        if (latitude < -90 || latitude > 90) {
            showError('Latitude must be between -90 and 90.');
            return;
        }

        if (longitude < -180 || longitude > 180) {
            showError('Longitude must be between -180 and 180.');
            return;
        }

        // Show loading state
        analyzeBtn.disabled = true;
        analyzeBtn.querySelector('.btn-text').style.display = 'none';
        analyzeBtn.querySelector('.btn-loader').style.display = 'inline';
        resultsSection.style.display = 'none';
        errorDiv.style.display = 'none';

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    latitude: latitude,
                    longitude: longitude,
                    area_name: areaName
                })
            });

            const data = await response.json();

            if (data.success) {
                displayResults(data.data);
            } else {
                showError(data.error || 'An error occurred during analysis.');
            }
        } catch (error) {
            showError('Failed to connect to server: ' + error.message);
        } finally {
            // Reset button state
            analyzeBtn.disabled = false;
            analyzeBtn.querySelector('.btn-text').style.display = 'inline';
            analyzeBtn.querySelector('.btn-loader').style.display = 'none';
        }
    });

    function displayResults(data) {
        // Display risk level
        const riskLevel = data.prolog_classification?.RiskLevel || 'Unknown';
        document.getElementById('riskLevel').textContent = riskLevel;
        document.getElementById('riskCard').className = 'risk-card ' + getRiskClass(riskLevel);

        // Display FDI
        const fdiValue = data.fdi?.value || 0;
        const fdiCategory = data.fdi?.category || 'Unknown';
        document.getElementById('fdiValue').textContent = fdiValue;
        document.getElementById('fdiCategory').textContent = fdiCategory;

        // Display weather details
        const weather = data.weather_data || {};
        document.getElementById('weatherDetails').innerHTML = `
            <div class="detail-item">
                <span class="detail-item-label">Temperature</span>
                <span class="detail-item-value">${weather.temperature?.toFixed(1) || 'N/A'}°C</span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Humidity</span>
                <span class="detail-item-value">${weather.humidity?.toFixed(1) || 'N/A'}%</span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Wind Speed</span>
                <span class="detail-item-value">${weather.wind_speed?.toFixed(1) || 'N/A'} km/h</span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Precipitation</span>
                <span class="detail-item-value">${weather.current_precipitation?.toFixed(2) || 'N/A'} mm</span>
            </div>
        `;

        // Display rain details
        const rain = data.rain_data || {};
        document.getElementById('rainDetails').innerHTML = `
            <div class="detail-item">
                <span class="detail-item-label">Last Rain Date</span>
                <span class="detail-item-value">${rain.last_rain_date || 'N/A'}</span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Rainfall Amount</span>
                <span class="detail-item-value">${rain.rainfall_amount?.toFixed(2) || 'N/A'} mm</span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Days Since Rain</span>
                <span class="detail-item-value">${rain.days_since_rain || 'N/A'} days</span>
            </div>
        `;

        // Display topography details
        const env = data.environmental || {};
        document.getElementById('topographyDetails').innerHTML = `
            <div class="detail-item">
                <span class="detail-item-label">Elevation</span>
                <span class="detail-item-value">${env.elevation?.toFixed(1) || 'N/A'} m</span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Slope</span>
                <span class="detail-item-value">${env.slope?.toFixed(2) || 'N/A'}°</span>
            </div>
        `;

        // Display population details
        document.getElementById('populationDetails').innerHTML = `
            <div class="detail-item">
                <span class="detail-item-label">Population Density</span>
                <span class="detail-item-value"><span class="badge badge-${env.population || 'medium'}">${env.population || 'N/A'}</span></span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Infrastructure</span>
                <span class="detail-item-value"><span class="badge badge-${getInfraClass(env.infrastructure)}">${env.infrastructure || 'N/A'}</span></span>
            </div>
        `;

        // Display classifications
        const classifications = data.classifications || {};
        document.getElementById('classificationsDetails').innerHTML = `
            <div class="detail-item">
                <span class="detail-item-label">Fuel Moisture</span>
                <span class="detail-item-value"><span class="badge badge-${classifications.fuel || 'moderate'}">${classifications.fuel || 'N/A'}</span></span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Temperature</span>
                <span class="detail-item-value"><span class="badge badge-${classifications.temperature || 'moderate'}">${classifications.temperature || 'N/A'}</span></span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Humidity</span>
                <span class="detail-item-value"><span class="badge badge-${classifications.humidity || 'moderate'}">${classifications.humidity || 'N/A'}</span></span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Wind</span>
                <span class="detail-item-value"><span class="badge badge-${classifications.wind || 'moderate'}">${classifications.wind || 'N/A'}</span></span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Topography</span>
                <span class="detail-item-value"><span class="badge badge-${classifications.topography || 'flat'}">${classifications.topography || 'N/A'}</span></span>
            </div>
        `;

        // Display recommendations
        const prolog = data.prolog_classification || {};
        document.getElementById('recommendationsDetails').innerHTML = `
            <div class="detail-item">
                <span class="detail-item-label">Evacuation Needed</span>
                <span class="detail-item-value"><span class="badge ${prolog.Evacuation === 'yes' ? 'badge-extreme' : prolog.Evacuation === 'maybe' ? 'badge-high' : 'badge-low'}">${prolog.Evacuation || 'N/A'}</span></span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Resources Required</span>
                <span class="detail-item-value">${formatResources(prolog.Resources || 'N/A')}</span>
            </div>
        `;

        // Show results
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function getRiskClass(riskLevel) {
        const level = riskLevel.toLowerCase();
        if (level.includes('extreme')) return 'risk-extreme';
        if (level.includes('very high')) return 'risk-very-high';
        if (level.includes('high')) return 'risk-high';
        if (level.includes('medium')) return 'risk-medium';
        if (level.includes('low')) return 'risk-low';
        return 'risk-very-low';
    }

    function getInfraClass(infra) {
        if (!infra) return 'medium';
        if (infra.includes('critical')) return 'extreme';
        if (infra.includes('slightly')) return 'high';
        return 'low';
    }

    function formatResources(resources) {
        if (typeof resources !== 'string') return resources;
        return resources.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
});

