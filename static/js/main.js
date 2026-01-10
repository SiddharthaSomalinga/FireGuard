// Dark Mode Functions
function initDarkMode() {
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;
    
    // Check for saved theme preference or system preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial theme
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        html.classList.add('dark-mode');
        updateThemeIcon(true);
    } else {
        html.classList.remove('dark-mode');
        updateThemeIcon(false);
    }
    
    // Handle toggle button click
    themeToggle.addEventListener('click', function() {
        html.classList.toggle('dark-mode');
        const isDarkMode = html.classList.contains('dark-mode');
        localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
        updateThemeIcon(isDarkMode);
    });
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            const html = document.documentElement;
            if (e.matches) {
                html.classList.add('dark-mode');
                updateThemeIcon(true);
            } else {
                html.classList.remove('dark-mode');
                updateThemeIcon(false);
            }
        }
    });
}

function updateThemeIcon(isDarkMode) {
    const themeIcon = document.querySelector('.theme-icon');
    if (themeIcon) {
        themeIcon.textContent = isDarkMode ? '☀️' : '🌙';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dark mode
    initDarkMode();

    // Per-card unit helpers (persist per card so toggles affect only that card)
    function getCardUnit(cardName) {
        return localStorage.getItem(`unit_${cardName}`) || 'metric';
    }

    function setCardUnit(cardName, system) {
        localStorage.setItem(`unit_${cardName}`, system);
        updateUnitButton(cardName);
        updateUnitsForCard(cardName);
    }

    function updateUnitButton(cardName) {
        const idMap = {
            weather: 'weatherUnitToggle',
            rain: 'rainUnitToggle',
            topo: 'topoUnitToggle'
        };
        const btn = document.getElementById(idMap[cardName]);
        if (!btn) return;
        const unit = getCardUnit(cardName);
        // Keep visible text constant to avoid layout shifts; show current units in tooltip/aria-label
        const labelMap = {
            weather: unit === 'metric' ? '°C · km/h · mm' : '°F · mph · in',
            rain: unit === 'metric' ? 'mm · in' : 'in · mm',
            topo: unit === 'metric' ? 'm · ft' : 'ft · m'
        };
        btn.textContent = 'Convert units';
        btn.title = labelMap[cardName];
        btn.setAttribute('aria-label', `Toggle units: ${labelMap[cardName]}`);
    }

    function cToF(c) { return (c * 9/5) + 32; }
    function kmhToMph(k) { return k * 0.621371; }

    function formatNumber(v, digits) {
        if (v === null || v === undefined || v === '') return 'N/A';
        const n = Number(v);
        if (Number.isNaN(n)) return 'N/A';
        return n.toFixed(digits);
    }

    function formatTempForUnit(celsius, cardName) {
        const sys = getCardUnit(cardName || 'weather');
        if (celsius === null || celsius === undefined || celsius === '') return 'N/A';
        const c = Number(celsius);
        if (sys === 'metric') return `${formatNumber(c,1)}°C`;
        return `${formatNumber(cToF(c),1)}°F`;
    }

    function formatSpeedForUnit(kmh, cardName) {
        const sys = getCardUnit(cardName || 'weather');
        if (kmh === null || kmh === undefined || kmh === '') return 'N/A';
        const k = Number(kmh);
        if (sys === 'metric') return `${formatNumber(k,1)} km/h`;
        return `${formatNumber(kmhToMph(k),1)} mph`;
    }

    function updateWeatherUnits(root) {
        root = root || document;
        // Update weather detail elements that have data attributes inside the provided root
        const tempEls = root.querySelectorAll('[data-temp-c]');
        tempEls.forEach(el => {
            const raw = el.getAttribute('data-temp-c');
            el.textContent = formatTempForUnit(raw, 'weather');
        });

        const windEls = root.querySelectorAll('[data-wind-kmh]');
        windEls.forEach(el => {
            const raw = el.getAttribute('data-wind-kmh');
            el.textContent = formatSpeedForUnit(raw, 'weather');
        });
        // Also convert precipitation inside this weather card if present
        const precipEls = root.querySelectorAll('[data-precip-mm]');
        precipEls.forEach(el => {
            const raw = el.getAttribute('data-precip-mm');
            el.textContent = formatPrecipForUnit(raw, 'weather');
        });
    }

    // Rain unit conversions (mm <-> inches)
    // Rain helpers (per-card)
    function getRainUnit() { return getCardUnit('rain'); }
    function setRainUnit(u) { setCardUnit('rain', u); }

    function mmToIn(mm) { return mm / 25.4; }
    function formatPrecipForUnit(mm, cardName) {
        if (mm === null || mm === undefined || mm === '') return 'N/A';
        const n = Number(mm);
        if (Number.isNaN(n)) return 'N/A';
        const unitSource = cardName ? getCardUnit(cardName) : getRainUnit();
        if (unitSource === 'metric') return `${n.toFixed(2)} mm`;
        return `${mmToIn(n).toFixed(2)} in`;
    }

    function updateRainUnits(root) {
        root = root || document;
        const precipEls = root.querySelectorAll('[data-precip-mm]');
        precipEls.forEach(el => {
            const raw = el.getAttribute('data-precip-mm');
            el.textContent = formatPrecipForUnit(raw);
        });
    }

    // Topography unit conversions (m <-> ft)
    // Topography helpers (per-card)
    function getTopoUnit() { return getCardUnit('topo'); }
    function setTopoUnit(u) { setCardUnit('topo', u); }

    function mToFt(m) { return m * 3.28084; }
    function formatElevationForUnit(m) {
        if (m === null || m === undefined || m === '') return 'N/A';
        const n = Number(m);
        if (Number.isNaN(n)) return 'N/A';
        if (getTopoUnit() === 'metric') return `${n.toFixed(1)} m`;
        return `${mToFt(n).toFixed(1)} ft`;
    }

    function updateTopoUnits(root) {
        root = root || document;
        const elevEls = root.querySelectorAll('[data-elevation-m]');
        elevEls.forEach(el => {
            const raw = el.getAttribute('data-elevation-m');
            el.textContent = formatElevationForUnit(raw);
        });
    }

    function updateAllUnits() {
        updateUnitsForCard('weather');
        updateUnitsForCard('rain');
        updateUnitsForCard('topo');
    }

    function updateUnitsForCard(cardName) {
        if (cardName === 'weather') {
            const root = document.getElementById('weatherDetails');
            if (root) updateWeatherUnits(root);
        } else if (cardName === 'rain') {
            const root = document.getElementById('rainDetails');
            if (root) updateRainUnits(root);
        } else if (cardName === 'topo') {
            const root = document.getElementById('topographyDetails');
            if (root) updateTopoUnits(root);
        }
    }

    // Attach click handler for the weather unit toggle button
    const weatherUnitBtn = document.getElementById('weatherUnitToggle');
    if (weatherUnitBtn) {
        weatherUnitBtn.addEventListener('click', function() {
            const current = getCardUnit('weather');
            setCardUnit('weather', current === 'metric' ? 'imperial' : 'metric');
        });
    }

    // Ensure button reflects stored preference on startup
    updateUnitButton('weather');

    // Attach handlers for rain and topo unit toggles
    const rainUnitBtn = document.getElementById('rainUnitToggle');
    if (rainUnitBtn) {
        rainUnitBtn.addEventListener('click', function() {
            const current = getRainUnit();
            setRainUnit(current === 'metric' ? 'imperial' : 'metric');
        });
    }
    updateUnitButton('rain');

    const topoUnitBtn = document.getElementById('topoUnitToggle');
    if (topoUnitBtn) {
        topoUnitBtn.addEventListener('click', function() {
            const current = getTopoUnit();
            setTopoUnit(current === 'metric' ? 'imperial' : 'metric');
        });
    }
    updateUnitButton('topo');

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
        // Display freshness indicators
        const analysisTimestamp = data.analysis_timestamp;
        const weatherTimestamp = data.weather_data_timestamp;
        const rainTimestamp = data.rain_data_timestamp;
        
        const now = new Date();
        
        if (analysisTimestamp || weatherTimestamp) {
            const weatherTime = weatherTimestamp ? new Date(weatherTimestamp) : new Date(analysisTimestamp);
            const weatherMinutesAgo = Math.round((now - weatherTime) / (1000 * 60));
            const weatherFreshnessText = formatTimeAgo(weatherMinutesAgo);
            document.getElementById('weatherFreshness').textContent = `Weather updated ${weatherFreshnessText}`;
        }
        
        if (rainTimestamp) {
            const lookbackDays = data.rain_data?.lookback_days || 90;
            document.getElementById('rainFreshness').textContent = `Rain history: last ${lookbackDays} days`;
        }
        
        // Display risk level
        const riskLevel = data.prolog_classification?.RiskLevel || 'Unknown';
        document.getElementById('riskLevel').textContent = riskLevel;
        document.getElementById('riskCard').className = 'risk-card ' + getRiskClass(riskLevel);

        // Display FDI with color coding
        const fdiValue = data.fdi?.value || 0;
        const fdiCategory = data.fdi?.category || 'Unknown';
        document.getElementById('fdiValue').textContent = fdiValue;
        const fdiCategoryEl = document.getElementById('fdiCategory');
        fdiCategoryEl.textContent = fdiCategory;
        fdiCategoryEl.className = 'fdi-category ' + getFDIClass(fdiCategory);

        // Display weather details
        const weather = data.weather_data || {};
        document.getElementById('weatherDetails').innerHTML = `
            <div class="detail-item">
                <span class="detail-item-label">Temperature</span>
                <span class="detail-item-value" data-temp-c="${weather.temperature ?? ''}">${weather.temperature !== undefined ? '...' : 'N/A'}</span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Humidity</span>
                <span class="detail-item-value">${weather.humidity?.toFixed(1) || 'N/A'}%</span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Wind Speed</span>
                <span class="detail-item-value" data-wind-kmh="${weather.wind_speed ?? ''}">${weather.wind_speed !== undefined ? '...' : 'N/A'}</span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Precipitation</span>
                <span class="detail-item-value" data-precip-mm="${weather.current_precipitation ?? ''}">${weather.current_precipitation !== undefined ? (weather.current_precipitation.toFixed(2) + ' mm') : 'N/A'}</span>
            </div>
        `;

        // After injecting raw data attributes, apply unit preferences to this card only
        updateUnitsForCard('weather');

        // Display rain details
        const rain = data.rain_data || {};
        document.getElementById('rainDetails').innerHTML = `
            <div class="detail-item">
                <span class="detail-item-label">Last Rain Date</span>
                <span class="detail-item-value">${rain.last_rain_date || 'N/A'}</span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Rainfall Amount</span>
                <span class="detail-item-value" data-precip-mm="${rain.rainfall_amount ?? ''}">${rain.rainfall_amount !== undefined ? '...' : 'N/A'}</span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Days Since Rain</span>
                <span class="detail-item-value">${rain.days_since_rain || 'N/A'} days</span>
            </div>
        `;

        // Apply rain unit formatting for this card only
        updateUnitsForCard('rain');

        // Display topography details
        const env = data.environmental || {};
        document.getElementById('topographyDetails').innerHTML = `
            <div class="detail-item">
                <span class="detail-item-label">Elevation</span>
                <span class="detail-item-value" data-elevation-m="${env.elevation ?? ''}">${env.elevation !== undefined ? '...' : 'N/A'}</span>
            </div>
            <div class="detail-item">
                <span class="detail-item-label">Slope</span>
                <span class="detail-item-value">${env.slope?.toFixed(2) || 'N/A'}°</span>
            </div>
        `;

        // Apply topo unit formatting for this card only
        updateUnitsForCard('topo');

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

        // Display risk explanation
        const explanation = data.risk_explanation || '';
        if (explanation) {
            document.getElementById('riskExplanation').innerHTML = convertMarkdownToHTML(explanation);
        }

        // Fetch and display NASA FIRMS active fires
        /* fetchAndDisplayFIRMSData(
            latitudeInput.value,
            longitudeInput.value,
            riskLevel
        ); */

        // Show results
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function convertMarkdownToHTML(markdown) {
        let html = markdown;
        
        // Split by double asterisks for bold sections first
        let parts = html.split(/\*\*([^*]+)\*\*/g);
        html = '';
        
        for (let i = 0; i < parts.length; i++) {
            if (i % 2 === 0) {
                // Regular text
                html += parts[i];
            } else {
                // Bold text
                html += '<strong>' + parts[i] + '</strong>';
            }
        }
        
        // Convert bullet points with emoji preservation
        html = html.replace(/^[•\-]\s+(.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.+<\/li>)/s, '<ul>$1</ul>');
        
        // Convert line breaks
        html = html.replace(/\n/g, '<br>');
        
        // Clean up multiple br tags
        html = html.replace(/<br>\s*<br>/g, '<br>');
        
        return html;
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function formatTimeAgo(minutes) {
        if (minutes < 1) {
            return 'just now';
        } else if (minutes < 60) {
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else {
            const hours = Math.floor(minutes / 60);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        }
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

    function getFDIClass(category) {
        const cat = category.toLowerCase();
        if (cat.includes('blue')) return 'fdi-blue';
        if (cat.includes('green')) return 'fdi-green';
        if (cat.includes('yellow')) return 'fdi-yellow';
        if (cat.includes('orange')) return 'fdi-orange';
        if (cat.includes('red')) return 'fdi-red';
        return '';
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

    // ============= Combined Wildfire + Risk Map =============

    // FIRMS detail card intentionally disabled
    async function fetchAndDisplayFIRMSData() { return; }
    function displayFIRMSResults() { return; }

    let combinedMap = null;
    let combinedBaseLayers = {};
    let overlayLayers = {};
    let layerControl = null;

    let firmsMarkerCluster = null;
    let firmsHeatLayer = null;
    let firmsCurrentFires = [];
    let firmsCurrentView = 'cluster';

    let riskHeatLayer = null;
    let riskGeoJSONLayer = null;
    let riskCurrentData = null;
    let riskCurrentView = 'grid';

    const combinedStatus = {
        fire: 'Loading live wildfire data...',
        risk: 'Loading risk layer...'
    };

    function updateCombinedStatus() {
        const el = document.getElementById('combinedMapContent');
        if (!el) return;
        el.innerHTML = `
            <div class="combined-status-row"><strong>Fires:</strong> ${combinedStatus.fire}</div>
            <div class="combined-status-row"><strong>Risk:</strong> ${combinedStatus.risk}</div>
        `;
    }

    function ensureCombinedMap() {
        const mapElement = document.getElementById('combinedMap');
        if (!mapElement) return null;
        if (combinedMap) return combinedMap;

        const centerLat = 45.0;
        const centerLon = -100.0;
        const zoomLevel = 4;

        combinedMap = L.map('combinedMap', {
            fullscreenControl: true,
            fullscreenControlOptions: {
                position: 'topleft'
            }
        }).setView([centerLat, centerLon], zoomLevel);

        const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        });

        const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles © Esri',
            maxZoom: 19
        });

        const topoLayer = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
            attribution: 'Map data: © OpenStreetMap, SRTM | Map style: © OpenTopoMap',
            maxZoom: 17
        });

        const darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '© OpenStreetMap, © CartoDB',
            maxZoom: 19
        });

        osmLayer.addTo(combinedMap);

        combinedBaseLayers = {
            "Street Map": osmLayer,
            "Satellite": satelliteLayer,
            "Topographic": topoLayer,
            "Dark Mode": darkLayer
        };

        rebuildLayerControl();
        L.control.scale({ imperial: true, metric: true }).addTo(combinedMap);
        return combinedMap;
    }

    function rebuildLayerControl() {
        if (!combinedMap) return;
        if (layerControl) {
            layerControl.remove();
        }
        layerControl = L.control.layers(combinedBaseLayers, overlayLayers, {
            position: 'topright',
            collapsed: false
        }).addTo(combinedMap);
    }

    function removeOverlay(name) {
        if (overlayLayers[name] && combinedMap) {
            combinedMap.removeLayer(overlayLayers[name]);
            delete overlayLayers[name];
        }
    }

    function formatAcres(value) {
        const num = Number(value);
        if (!Number.isFinite(num)) return 'N/A';
        if (num < 1) return `${num.toFixed(2)} acres`;
        return `${Math.round(num).toLocaleString('en-US')} acres`;
    }

    function formatPercent(value) {
        const num = Number(value);
        if (!Number.isFinite(num)) return 'N/A';
        return `${Math.round(num)}%`;
    }

    function formatCount(value) {
        if (value === 0) return '0';
        return value ? `${value}` : 'N/A';
    }

    function formatDateTime(dateStr, timeStr) {
        if (!dateStr && !timeStr) return 'Unknown';
        if (dateStr && timeStr) return `${dateStr} ${timeStr}`;
        return dateStr || timeStr || 'Unknown';
    }

    function formatPrettyDateTime(dateStr, timeStr) {
        // If date is ISO-like, prefer it and ignore timeStr to avoid double times
        const looksIso = typeof dateStr === 'string' && /\d{4}-\d{2}-\d{2}T/.test(dateStr);
        if (looksIso) {
            const parsed = new Date(dateStr);
            if (!Number.isNaN(parsed.getTime())) return parsed.toUTCString();
        }

        // If date already includes a time (hh:mm) or any colon, trust it alone
        if (dateStr && /\d{1,2}:\d{2}/.test(dateStr)) return dateStr;
        if (dateStr && dateStr.includes(':')) return dateStr;

        // If we have both and date isn't ISO and lacks time, combine once
        if (dateStr && timeStr && !looksIso) {
            const trimmedTime = timeStr.trim();
            const lowerDate = dateStr.toLowerCase();
            if (lowerDate.includes(trimmedTime.toLowerCase())) return dateStr;
            return formatDateTime(dateStr, timeStr);
        }

        const raw = dateStr || timeStr;
        if (!raw) return 'Unknown';

        try {
            if (/^\d{12,}$/.test(raw)) {
                const ms = Number(raw);
                const d = new Date(ms);
                if (!Number.isNaN(d.getTime())) return d.toUTCString();
            }
            const parsed = new Date(raw);
            if (!Number.isNaN(parsed.getTime())) {
                return parsed.toLocaleString('en-US', {
                    timeZone: 'UTC',
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    timeZoneName: 'short'
                });
            }
        } catch (e) {
            // Fallback below
        }
        return raw;
    }

    function buildFirePopup(fire) {
        const fireName = fire.fire_name || 'Wildfire';
        const typeLabel = (fire.fire_type || fire.type || 'Wildfire').toString().replace(/_/g, ' ');
        const location = [fire.county, fire.state].filter(Boolean).join(', ') || 'Location unavailable';
        const containment = formatPercent(fire.containment);
        const acres = formatAcres(fire.acres);
        const frp = Number.isFinite(Number(fire.frp)) ? `${Number(fire.frp).toFixed(1)} MW` : 'N/A';
        const brightness = Number.isFinite(Number(fire.brightness)) ? `${Number(fire.brightness).toFixed(1)}K` : 'N/A';
        const confidence = fire.confidence_level || 'unknown';
        const source = fire.source || 'ArcGIS';
        const discovered = formatPrettyDateTime(fire.discovery_date, fire.acq_time);
        // Only pass acq_time if update_time doesn't already have time info
        const updateTimeRaw = fire.update_time || fire.acq_date || '';
        const updated = formatPrettyDateTime(updateTimeRaw, 
            (updateTimeRaw && /\d{1,2}:\d{2}/.test(updateTimeRaw)) ? null : fire.acq_time);
        const residences = formatCount(fire.residences_destroyed);
        const structures = formatCount(fire.structures_destroyed);
        const personnel = formatCount(fire.personnel);
        const cause = fire.fire_cause || fire.status || 'Unknown';

        return `
            <div class="fire-popup">
                <div class="fire-popup-title">${typeLabel.toUpperCase()}</div>
                <div class="fire-popup-name">${fireName}</div>
                <div class="fire-popup-item"><span class="fire-popup-label">Acres Burned:</span><span class="fire-popup-value">${acres}</span></div>
                <div class="fire-popup-item"><span class="fire-popup-label">Percent Contained:</span><span class="fire-popup-value">${containment}</span></div>
                <div class="fire-popup-item"><span class="fire-popup-label">County of Origin:</span><span class="fire-popup-value">${location}</span></div>
                <div class="fire-popup-item"><span class="fire-popup-label">Cause/Status:</span><span class="fire-popup-value">${cause}</span></div>
                <div class="fire-popup-item"><span class="fire-popup-label">Residences Destroyed:</span><span class="fire-popup-value">${residences}</span></div>
                <div class="fire-popup-item"><span class="fire-popup-label">Other Structures Destroyed:</span><span class="fire-popup-value">${structures}</span></div>
                <div class="fire-popup-item"><span class="fire-popup-label">Fire Power (FRP):</span><span class="fire-popup-value">${frp}</span></div>
                <div class="fire-popup-item"><span class="fire-popup-label">Brightness:</span><span class="fire-popup-value">${brightness}</span></div>
                <div class="fire-popup-item"><span class="fire-popup-label">Confidence:</span><span class="fire-popup-value">${confidence}</span></div>
                <div class="fire-popup-item"><span class="fire-popup-label">Source:</span><span class="fire-popup-value">${source}</span></div>
                <div class="fire-popup-meta">Discovered: ${discovered}</div>
                <div class="fire-popup-meta">Current as of: ${updated}</div>
            </div>
        `;
    }

    function createFireMarker(fire) {
        // Validate required fields
        if (!fire || typeof fire.lat !== 'number' || typeof fire.lon !== 'number') {
            console.warn('Invalid fire data:', fire);
            return null;
        }
        
        const confidenceLevel = fire.confidence_level || 'nominal';
        const color = getConfidenceColor(confidenceLevel);
        const frpValue = Number.isFinite(Number(fire.frp)) ? Number(fire.frp) : 50;
        const size = Math.min(Math.max(frpValue / 100 * 12, 8), 20);

        const fireIcon = L.divIcon({
            className: 'fire-marker-icon',
            html: `<div style="background-color: ${color}; width: ${size}px; height: ${size}px; border-radius: 50%; border: 2px solid rgba(0, 0, 0, 0.4); box-shadow: 0 0 10px ${color}; animation: pulse 2s infinite;"></div>`,
            iconSize: [size, size],
            iconAnchor: [size/2, size/2]
        });

        const marker = L.marker([fire.lat, fire.lon], { icon: fireIcon });
        marker.bindPopup(buildFirePopup(fire));
        return marker;
    }

    function updateFirmsView(viewType) {
        const map = ensureCombinedMap();
        if (!map) return;

        removeOverlay('Fire Clusters');
        removeOverlay('Fire Heat');

        if (firmsMarkerCluster) {
            map.removeLayer(firmsMarkerCluster);
            firmsMarkerCluster = null;
        }
        if (firmsHeatLayer) {
            map.removeLayer(firmsHeatLayer);
            firmsHeatLayer = null;
        }

        firmsCurrentView = viewType;

        if (viewType === 'cluster') {
            const clusterRadius = firmsCurrentFires.length > 1000 ? 120 : 80;
            firmsMarkerCluster = L.markerClusterGroup({
                maxClusterRadius: clusterRadius,
                spiderfyOnMaxZoom: true,
                showCoverageOnHover: false,
                zoomToBoundsOnClick: true,
                disableClusteringAtZoom: 15,
                chunkedLoading: true,
                chunkInterval: 200,
                chunkDelay: 50,
                iconCreateFunction: function(cluster) {
                    const count = cluster.getChildCount();
                    let size = 'small';
                    if (count > 100) size = 'large';
                    else if (count > 20) size = 'medium';

                    return L.divIcon({
                        html: `<div><span>${count}</span></div>`,
                        className: 'marker-cluster marker-cluster-' + size,
                        iconSize: L.point(40, 40)
                    });
                }
            });

            firmsCurrentFires.forEach(fire => {
                const marker = createFireMarker(fire);
                if (marker) {
                    firmsMarkerCluster.addLayer(marker);
                }
            });

            map.addLayer(firmsMarkerCluster);
            overlayLayers['Fire Clusters'] = firmsMarkerCluster;
        } else if (viewType === 'heat') {
            const heatData = firmsCurrentFires.map(fire => {
                const weight = Math.min((fire.frp || 0) / 500, 1);
                return [fire.lat, fire.lon, weight];
            });

            firmsHeatLayer = L.heatLayer(heatData, {
                radius: 25,
                blur: 35,
                maxZoom: 10,
                max: 1.0,
                gradient: {
                    0.0: '#FFFF00',
                    0.3: '#FFA500',
                    0.6: '#FF4500',
                    0.8: '#FF0000',
                    1.0: '#8B0000'
                }
            });

            map.addLayer(firmsHeatLayer);
            overlayLayers['Fire Heat'] = firmsHeatLayer;
        }

        rebuildLayerControl();

        if (firmsCurrentFires.length > 0) {
            const bounds = L.latLngBounds(firmsCurrentFires.map(fire => [fire.lat, fire.lon]));
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }

    // Fetch recent global FIRMS fires (disabled UI preload)
    async function fetchRecentFires() {
        return; // No-op to avoid showing preload summary
    }

    // Fetch and display live wildfires for the combined map
    async function fetchLiveWildfires() {
        const mapContainer = document.getElementById('combinedMapContainer');
        if (mapContainer) mapContainer.style.display = 'block';
        combinedStatus.fire = 'Loading live wildfire data...';
        updateCombinedStatus();
        ensureCombinedMap();
        
        try {
            let fires = [];
            let dataSource = 'ArcGIS';
            
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 30000);
                const arcgisResp = await fetch('/api/arcgis/fires?days=30&hotspots=true', {
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                
                if (arcgisResp.ok) {
                    const arcgisJson = await arcgisResp.json();
                    if (arcgisJson.success && arcgisJson.data && arcgisJson.data.fires) {
                        fires = arcgisJson.data.fires;
                        fires = fires.filter(fire => 
                            fire && 
                            typeof fire.lat === 'number' && 
                            typeof fire.lon === 'number' &&
                            !isNaN(fire.lat) && 
                            !isNaN(fire.lon) &&
                            fire.lat >= -90 && fire.lat <= 90 &&
                            fire.lon >= -180 && fire.lon <= 180
                        );
                        dataSource = arcgisJson.data.sources ? arcgisJson.data.sources.join(', ') : 'ArcGIS';
                        console.log(`✅ Loaded ${fires.length} valid fires from ArcGIS (filtered invalid coordinates)`);
                    }
                }
            } catch (arcgisErr) {
                if (arcgisErr.name === 'AbortError') {
                    console.warn('⚠️ ArcGIS fetch timed out after 30s, trying FIRMS...');
                } else {
                    console.warn('⚠️ ArcGIS fetch failed, trying FIRMS:', arcgisErr);
                }
            }
            
            if (fires.length === 0) {
                try {
                    const firmsResp = await fetch('/api/firms/recent?days=7&max=2000');
                    if (firmsResp.ok) {
                        const firmsJson = await firmsResp.json();
                        if (firmsJson.success && firmsJson.data && firmsJson.data.fires) {
                            fires = firmsJson.data.fires;
                            dataSource = 'NASA FIRMS';
                            console.log(`✅ Loaded ${fires.length} fires from FIRMS`);
                        }
                    }
                } catch (firmsErr) {
                    console.error('❌ FIRMS fetch also failed:', firmsErr);
                }
            }
            
            if (fires && fires.length > 0) {
                firmsCurrentFires = fires.length > 2000
                    ? fires.sort((a, b) => (b.frp || 0) - (a.frp || 0)).slice(0, 2000)
                    : fires;
                combinedStatus.fire = `${firmsCurrentFires.length} active wildfires from ${dataSource}`;
                updateCombinedStatus();
                updateFirmsView(firmsCurrentView);
            } else {
                combinedStatus.fire = 'No recent wildfire data available.';
                updateCombinedStatus();
                removeOverlay('Fire Clusters');
                removeOverlay('Fire Heat');
                rebuildLayerControl();
            }
        } catch (err) {
            console.error('❌ Error fetching live wildfires:', err);
            combinedStatus.fire = 'Unable to load wildfire data.';
            updateCombinedStatus();
        }
    }

    function getThreatColor(level) {
        const colors = {
            'critical': 'threat-critical',
            'severe': 'threat-severe',
            'moderate': 'threat-moderate',
            'minor': 'threat-minor',
            'none': 'threat-none'
        };
        return colors[level] || 'threat-none';
    }

    function getThreatEmoji(level) {
        const emojis = {
            'critical': '🔴',
            'severe': '🟠',
            'moderate': '🟡',
            'minor': '🟢',
            'none': '✅'
        };
        return emojis[level] || '✅';
    }

    function getConfidenceColor(level) {
        const colors = {
            'high': '#FF0000',
            'nominal': '#FFA500',
            'low': '#FFFF00'
        };
        return colors[level] || '#FFFF00';
    }

    // ============= Risk Layer Functions =============

    function updateRiskView(viewType) {
        const map = ensureCombinedMap();
        if (!map || !riskCurrentData) return;

        removeOverlay('Risk Grid');
        removeOverlay('Risk Heat');

        if (riskGeoJSONLayer) {
            map.removeLayer(riskGeoJSONLayer);
            riskGeoJSONLayer = null;
        }
        if (riskHeatLayer) {
            map.removeLayer(riskHeatLayer);
            riskHeatLayer = null;
        }

        riskCurrentView = viewType;

        if (viewType === 'grid') {
            if (riskCurrentData.features) {
                riskGeoJSONLayer = L.geoJSON(riskCurrentData, {
                    style: function(feature) {
                        return {
                            fillColor: feature.properties.risk_color || '#FFA500',
                            weight: 1,
                            opacity: 0.5,
                            color: '#444',
                            dashArray: '3',
                            fillOpacity: 0.25
                        };
                    },
                    onEachFeature: function(feature, layer) {
                        const props = feature.properties;
                        const riskScore = props.risk_score || 50;
                        const riskCategory = props.risk_category || 'moderate';

                        const popup = `
                            <div class="risk-popup">
                                <div class="risk-popup-title">📊 Wildfire Risk Assessment</div>
                                <div class="risk-popup-item">
                                    <span class="risk-popup-label">Overall Risk Score:</span>
                                    <span class="risk-popup-value"><strong>${riskScore.toFixed(1)}/100</strong></span>
                                </div>
                                <div class="risk-popup-item">
                                    <span class="risk-popup-label">Risk Category:</span>
                                    <span class="risk-popup-value"><span class="badge badge-${riskCategory}">${riskCategory}</span></span>
                                </div>
                                <div class="risk-popup-divider"></div>
                                <div class="risk-popup-subtitle">Risk Components</div>
                                <div class="risk-popup-item">
                                    <span class="risk-popup-label">FDI Risk:</span>
                                    <span class="risk-popup-value">${props.fdi_risk.toFixed(1)}</span>
                                </div>
                                <div class="risk-popup-item">
                                    <span class="risk-popup-label">Fire Proximity Risk:</span>
                                    <span class="risk-popup-value">${props.fire_proximity_risk.toFixed(1)}</span>
                                </div>
                                ${props.closest_fire_km ? `
                                <div class="risk-popup-item">
                                    <span class="risk-popup-label">Closest Active Fire:</span>
                                    <span class="risk-popup-value">${props.closest_fire_km.toFixed(1)} km away</span>
                                </div>
                                ` : ''}
                                <div class="risk-popup-item">
                                    <span class="risk-popup-label">Active Fires Nearby:</span>
                                    <span class="risk-popup-value">${props.nearby_fires} detected</span>
                                </div>
                            </div>
                        `;
                        layer.bindPopup(popup);

                        layer.on('mouseover', function(e) {
                            const hovered = e.target;
                            hovered.setStyle({
                                weight: 2,
                                fillOpacity: 0.35
                            });
                        });

                        layer.on('mouseout', function(e) {
                            riskGeoJSONLayer.resetStyle(e.target);
                        });
                    }
                });

                map.addLayer(riskGeoJSONLayer);
                overlayLayers['Risk Grid'] = riskGeoJSONLayer;
            }
        } else if (viewType === 'heat') {
            const heatData = [];
            if (riskCurrentData.features) {
                riskCurrentData.features.forEach(feature => {
                    const coords = feature.geometry.coordinates[0];
                    let sumLat = 0, sumLon = 0;
                    coords.forEach(coord => {
                        sumLon += coord[0];
                        sumLat += coord[1];
                    });
                    const centerLon = sumLon / coords.length;
                    const centerLat = sumLat / coords.length;

                    const intensity = feature.properties.risk_score / 100;
                    heatData.push([centerLat, centerLon, intensity]);
                });
            }

            riskHeatLayer = L.heatLayer(heatData, {
                radius: 50,
                blur: 60,
                maxZoom: 8,
                max: 1.0,
                gradient: {
                    0.0: '#90EE90',
                    0.2: '#FFFF00',
                    0.4: '#FFA500',
                    0.6: '#FF0000',
                    0.8: '#8B0000',
                    1.0: '#4B0000'
                }
            });

            map.addLayer(riskHeatLayer);
            overlayLayers['Risk Heat'] = riskHeatLayer;
        }

        rebuildLayerControl();
    }

    async function fetchAndDisplayRiskLayer() {
        combinedStatus.risk = 'Generating geospatial risk layer...';
        updateCombinedStatus();
        ensureCombinedMap();
        
        try {
            const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
            const gridResolution = isProduction ? '2.0' : '1.0';
            const resp = await fetch(`/api/risk-layer/geojson?grid_resolution=${gridResolution}`);
            if (!resp.ok) throw new Error('Failed to fetch risk layer');
            const json = await resp.json();
            
            if (json.success && json.data) {
                const geojson = json.data;
                riskCurrentData = geojson;
                const metadata = geojson.metadata || {};
                combinedStatus.risk = `Risk layer ready (${metadata.total_cells || 'N/A'} cells, ${metadata.fire_count || 0} fires)`;
                updateCombinedStatus();
                updateRiskView(riskCurrentView || 'grid');
            } else {
                combinedStatus.risk = 'Unable to generate risk layer.';
                updateCombinedStatus();
            }
        } catch (err) {
            console.error('Error fetching risk layer:', err);
            combinedStatus.risk = 'Unable to load risk layer.';
            updateCombinedStatus();
        }
    }

    // Map toggle controls
    const riskToggleBtn = document.getElementById('riskLayerToggleBtn');
    if (riskToggleBtn) {
        riskToggleBtn.addEventListener('click', function() {
            riskCurrentView = riskCurrentView === 'grid' ? 'heat' : 'grid';
            updateRiskView(riskCurrentView);
            riskToggleBtn.classList.toggle('active', riskCurrentView === 'heat');
        });
    }

    const fireToggleBtn = document.getElementById('fireLayerToggleBtn');
    if (fireToggleBtn) {
        fireToggleBtn.addEventListener('click', function() {
            firmsCurrentView = firmsCurrentView === 'cluster' ? 'heat' : 'cluster';
            updateFirmsView(firmsCurrentView);
            fireToggleBtn.classList.toggle('active', firmsCurrentView === 'heat');
        });
    }

    const combinedRefreshBtn = document.getElementById('combinedRefreshBtn');
    if (combinedRefreshBtn) {
        combinedRefreshBtn.addEventListener('click', function() {
            combinedRefreshBtn.disabled = true;
            combinedRefreshBtn.innerHTML = '<span>⏳</span> Loading...';
            Promise.allSettled([fetchAndDisplayRiskLayer(), fetchLiveWildfires()]).finally(() => {
                combinedRefreshBtn.disabled = false;
                combinedRefreshBtn.innerHTML = '<span>🔄</span> Refresh';
            });
        });
    }

    // Initialize combined map layers on page load
    try {
        ensureCombinedMap();
        fetchAndDisplayRiskLayer();
        fetchLiveWildfires();

        // Auto-refresh risk every 15 minutes and fires every 10 minutes
        setInterval(() => {
            console.log('Auto-refreshing risk layer data...');
            fetchAndDisplayRiskLayer();
        }, 15 * 60 * 1000);

        setInterval(() => {
            console.log('Auto-refreshing live wildfire data...');
            fetchLiveWildfires();
        }, 10 * 60 * 1000);
    } catch (e) {
        console.warn('Failed to initialize combined map:', e);
    }

});
