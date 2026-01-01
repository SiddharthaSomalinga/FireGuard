document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('locationForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultsSection = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const useLocationBtn = document.getElementById('useLocationBtn');
    const latitudeInput = document.getElementById('latitude');
    const longitudeInput = document.getElementById('longitude');
    const areaNameInput = document.getElementById('areaName');

    // Handle "Use My Location" button
    useLocationBtn.addEventListener('click', function(e) {
        e.preventDefault();
        useLocationBtn.disabled = true;
        useLocationBtn.textContent = '📍 Getting location...';

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const lat = position.coords.latitude.toFixed(4);
                    const lon = position.coords.longitude.toFixed(4);
                    
                    latitudeInput.value = lat;
                    longitudeInput.value = lon;
                    
                    // Auto-generate area name if not provided
                    if (!areaNameInput.value) {
                        areaNameInput.value = `My Location (${lat}, ${lon})`;
                    }
                    
                    useLocationBtn.disabled = false;
                    useLocationBtn.textContent = '📍 Use My Location';
                    errorDiv.style.display = 'none';
                    
                    // Focus on the form for better UX
                    analyzeBtn.focus();
                },
                function(error) {
                    let errorMsg = 'Unable to get your location. ';
                    if (error.code === error.PERMISSION_DENIED) {
                        errorMsg += 'Please enable location access in your browser settings.';
                    } else if (error.code === error.POSITION_UNAVAILABLE) {
                        errorMsg += 'Location information is unavailable.';
                    } else if (error.code === error.TIMEOUT) {
                        errorMsg += 'The request to get user location timed out.';
                    } else {
                        errorMsg += 'An error occurred while retrieving your location.';
                    }
                    showError(errorMsg);
                    useLocationBtn.disabled = false;
                    useLocationBtn.textContent = '📍 Use My Location';
                }
            );
        } else {
            showError('Geolocation is not supported by your browser.');
            useLocationBtn.disabled = false;
            useLocationBtn.textContent = '📍 Use My Location';
        }
    });

    // Handle preset buttons
    const presetBtns = document.querySelectorAll('.preset-btn');
    presetBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const lat = this.getAttribute('data-lat');
            const lon = this.getAttribute('data-lon');
            const name = this.getAttribute('data-name');
            const display = this.getAttribute('data-display');
            
            latitudeInput.value = lat;
            longitudeInput.value = lon;
            // Store Prolog-safe name in a data attribute for the form submission
            latitudeInput.dataset.prologName = name;
            areaNameInput.value = display;
            
            errorDiv.style.display = 'none';
            analyzeBtn.focus();
        });
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const latitude = parseFloat(document.getElementById('latitude').value);
        const longitude = parseFloat(document.getElementById('longitude').value);
        // Use Prolog-safe name if set (from preset), otherwise use areaName field
        const areaName = latitudeInput.dataset.prologName || document.getElementById('areaName').value || 'user_location';

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
                <span class="detail-item-value"><span class="badge badge-${getInfraClass(env.infrastructure)}">${formatResources(env.infrastructure) || 'N/A'}</span></span>
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

    // ============================================
    // CHATBOT FUNCTIONALITY
    // ============================================
    
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const quickActionBtns = document.querySelectorAll('.quick-action-btn');
    
    // Only initialize chatbot if all elements exist
    if (chatbotToggle && chatbotWindow && chatbotInput && chatbotSend && chatbotMessages) {
        let currentQuery = null;
        let awaitingParams = false;
        let paramSteps = [];
        let currentParamIndex = 0;
        let collectedParams = {};

        // Toggle chatbot window
        chatbotToggle.addEventListener('click', function() {
            const isOpen = chatbotWindow.style.display === 'block';
            chatbotWindow.style.display = isOpen ? 'none' : 'block';
            document.querySelector('.chatbot-icon').style.display = isOpen ? 'inline' : 'none';
            document.querySelector('.chatbot-close-icon').style.display = isOpen ? 'none' : 'inline';
        });

        // Quick action buttons
        quickActionBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const action = this.getAttribute('data-action');
                handleQuickAction(action);
            });
        });

        // Send message on button click
        chatbotSend.addEventListener('click', sendMessage);

        // Send message on Enter key
        chatbotInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        function sendMessage() {
            const message = chatbotInput.value.trim();
            if (!message) return;

            addMessage(message, 'user');
            chatbotInput.value = '';

            if (awaitingParams) {
                handleParamInput(message);
            } else {
                processMessage(message);
            }
        }

        function addMessage(text, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `chatbot-message ${type}-message`;
            messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
            chatbotMessages.appendChild(messageDiv);
            chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        }

        function handleQuickAction(action) {
            currentQuery = action;
            awaitingParams = true;
            currentParamIndex = 0;
            collectedParams = {};

            switch(action) {
                case 'fireline_intensity':
                    paramSteps = [
                        { name: 'I', label: 'Reaction Intensity (I)' },
                        { name: 'P', label: 'Propagating Flux Ratio (P)' },
                        { name: 'W', label: 'Wind Factor (W)' },
                        { name: 'S', label: 'Slope Factor (S)' },
                        { name: 'B', label: 'Bulk Density (B)' },
                        { name: 'E', label: 'Effective Heating Number (E)' },
                        { name: 'H', label: 'Heat of Preignition (H)' },
                        { name: 'H_Yield', label: 'Heat Yield' },
                        { name: 'A_Fuel', label: 'Amount of Fuel Consumed' }
                    ];
                    addMessage('🔥 Fireline Intensity Calculator<br><br>Please provide the following values:', 'bot');
                    askNextParam();
                    break;

                case 'flame_length':
                    paramSteps = [
                        { name: 'I', label: 'Fireline Intensity (I)' }
                    ];
                    addMessage('📏 Flame Length Calculator<br><br>Please provide:', 'bot');
                    askNextParam();
                    break;

                case 'safety_zone':
                    paramSteps = [
                        { name: 'C', label: 'Empirical Constant (C)' },
                        { name: 'I', label: 'Fireline Intensity (I)' },
                        { name: 'N', label: 'Exponent (N)' }
                    ];
                    addMessage('🛡️ Safety Zone Calculator<br><br>Please provide:', 'bot');
                    askNextParam();
                    break;

                case 'burn_area':
                    paramSteps = [
                        { name: 'R', label: 'Rate of fire spread (R) in ft/min' },
                        { name: 'T', label: 'Time elapsed since ignition (T) in minutes' }
                    ];
                    addMessage('📊 Burn Area Estimator<br><br>Please provide:', 'bot');
                    askNextParam();
                    break;

                case 'escape_time':
                    paramSteps = [
                        { name: 'D', label: 'Distance to nearest safe zone (D) in meters' },
                        { name: 'R', label: 'Rate of fire spread (R) in m/s' }
                    ];
                    addMessage('⏱️ Escape Time Calculator<br><br>Please provide:', 'bot');
                    askNextParam();
                    break;

                case 'risk_level':
                    paramSteps = [
                        { name: 'fuel', label: 'Fuel type (moist, moderate, dry, extremely_dry)' },
                        { name: 'temp', label: 'Temperature (low, moderate, high, very_high)' },
                        { name: 'hum', label: 'Humidity (high, moderate, low, very_low)' },
                        { name: 'wind', label: 'Wind speed (low, moderate, strong, extreme)' },
                        { name: 'topo', label: 'Topography (flat, hilly, steep, very_steep)' },
                        { name: 'pop', label: 'Population density (low, medium, high)' },
                        { name: 'infra', label: 'Infrastructure (no, no_critical, slightly_critical, critical)' }
                    ];
                    addMessage('⚠️ Risk Level Assessment<br><br>Please provide the following classifications:', 'bot');
                    askNextParam();
                    break;
            }
        }

        function askNextParam() {
            if (currentParamIndex < paramSteps.length) {
                const param = paramSteps[currentParamIndex];
                addMessage(`${currentParamIndex + 1}. ${param.label}:`, 'bot');
            }
        }

        function handleParamInput(value) {
            const param = paramSteps[currentParamIndex];
            collectedParams[param.name] = isNaN(value) ? value : parseFloat(value);
            
            currentParamIndex++;
            
            if (currentParamIndex < paramSteps.length) {
                askNextParam();
            } else {
                awaitingParams = false;
                executeChatbotQuery();
            }
        }

        async function executeChatbotQuery() {
            addMessage('<div class="chatbot-loading"></div> Calculating...', 'bot');
            
            try {
                const response = await fetch('/api/chatbot', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query_type: currentQuery,
                        params: collectedParams
                    })
                });

                const data = await response.json();

                // Remove loading message
                chatbotMessages.removeChild(chatbotMessages.lastChild);

                if (data.success) {
                    const result = data.data.result || 'Calculation complete!';
                    addMessage(`✅ Result:<br><br>${result}`, 'bot');
                } else {
                    addMessage(`❌ Error: ${data.error}`, 'bot');
                }
            } catch (error) {
                chatbotMessages.removeChild(chatbotMessages.lastChild);
                addMessage(`❌ Failed to connect: ${error.message}`, 'bot');
            }

            // Reset state
            currentQuery = null;
            collectedParams = {};
            currentParamIndex = 0;
        }

        function processMessage(message) {
            const lowerMsg = message.toLowerCase();
            
            // Check for help requests
            if (lowerMsg.includes('help') || lowerMsg.includes('what can you do')) {
                addMessage('I can help you with:<br><ul>' +
                    '<li>🔥 Fireline Intensity calculations</li>' +
                    '<li>📏 Flame Length estimates</li>' +
                    '<li>🛡️ Safety Zone distances</li>' +
                    '<li>📊 Burn Area estimations</li>' +
                    '<li>⏱️ Escape Time calculations</li>' +
                    '<li>⚠️ Risk Level assessments</li>' +
                    '</ul><br>Click any button above to start!', 'bot');
                return;
            }
            
            // Check for specific calculation requests
            if (lowerMsg.includes('fireline') || lowerMsg.includes('fire line') || lowerMsg.includes('intensity')) {
                handleQuickAction('fireline_intensity');
            } else if (lowerMsg.includes('flame') && lowerMsg.includes('length')) {
                handleQuickAction('flame_length');
            } else if (lowerMsg.includes('safety') && (lowerMsg.includes('zone') || lowerMsg.includes('distance'))) {
                handleQuickAction('safety_zone');
            } else if (lowerMsg.includes('burn') && lowerMsg.includes('area')) {
                handleQuickAction('burn_area');
            } else if (lowerMsg.includes('escape') && lowerMsg.includes('time')) {
                handleQuickAction('escape_time');
            } else if (lowerMsg.includes('risk') && lowerMsg.includes('level')) {
                handleQuickAction('risk_level');
            } else {
                addMessage('I\'m not sure how to help with that. You can:<br><br>' +
                    '• Type "<b>help</b>" to see what I can do<br>' +
                    '• Type a calculation name (e.g., "Fireline Intensity")<br>' +
                    '• Click one of the buttons above', 'bot');
            }
        }
    }
});