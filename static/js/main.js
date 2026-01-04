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

    // ============= NASA FIRMS Active Fire Functions =============

    async function fetchAndDisplayFIRMSData(latitude, longitude, riskLevel) {
        const firmsCard = document.getElementById('firmsCard');
        const firmsContent = document.getElementById('firmsContent');
        
        try {
            // Show loading state
            firmsCard.style.display = 'block';
            firmsContent.innerHTML = '<div class="firms-loading">Loading satellite fire data...</div>';
            
            const response = await fetch('/api/firms/active-fires', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    latitude: parseFloat(latitude),
                    longitude: parseFloat(longitude),
                    current_risk_level: riskLevel
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch FIRMS data');
            }
            
            const result = await response.json();
            
            if (result.success && result.data) {
                displayFIRMSResults(result.data);
            } else {
                firmsContent.innerHTML = '<div class="firms-no-data">Unable to load satellite fire data</div>';
            }
        } catch (error) {
            console.warn('FIRMS data fetch error:', error);
            firmsContent.innerHTML = '<div class="firms-no-data">Satellite fire data unavailable</div>';
        }
    }

    function displayFIRMSResults(data) {
        const firmsContent = document.getElementById('firmsContent');
        const firmsMapContainer = document.getElementById('firmsMapContainer');
        const threatAnalysis = data.threat_analysis || {};
        const fires = data.fires || [];
        
        let html = '';
        
        if (!threatAnalysis.has_nearby_fires) {
            html = `
                <div class="firms-status good">
                    <div class="firms-status-icon">✅</div>
                    <div class="firms-status-text">
                        <div class="firms-status-title">No Active Fires Detected</div>
                        <div class="firms-status-desc">No satellite-detected fires within 100km radius</div>
                    </div>
                </div>
            `;
            firmsMapContainer.style.display = 'none';
        } else {
            const threatLevel = threatAnalysis.fire_threat_level || 'none';
            const threatColor = getThreatColor(threatLevel);
            const threatEmoji = getThreatEmoji(threatLevel);
            const closestFire = fires[0];
            
            html = `
                <div class="firms-status ${threatColor}">
                    <div class="firms-status-icon">${threatEmoji}</div>
                    <div class="firms-status-text">
                        <div class="firms-status-title">Threat Level: ${threatLevel.toUpperCase()}</div>
                        <div class="firms-status-desc">
                            ${threatAnalysis.nearby_fire_count} fire(s) detected, 
                            closest is ${closestFire.distance_km}km away (${closestFire.confidence_level} confidence)
                        </div>
                    </div>
                </div>
            `;
            
            // Add evacuation warning if needed
            if (threatAnalysis.evacuation_recommended) {
                html += `
                    <div class="firms-evacuation-warning">
                        <div class="warning-icon">🚨</div>
                        <div class="warning-text">
                            <div class="warning-title">Evacuation Alert</div>
                            <div class="warning-message">${threatAnalysis.evacuation_reason}</div>
                        </div>
                    </div>
                `;
            }
            
            // Add risk elevation info
            if (threatAnalysis.recommended_risk_elevation) {
                html += `
                    <div class="firms-risk-elevation">
                        <div class="elevation-label">Risk Auto-Elevated:</div>
                        <div class="elevation-badges">
                            <span class="badge badge-neutral">Original: ${data.current_risk_level || 'Unknown'}</span>
                            <span class="badge badge-${threatAnalysis.recommended_risk_elevation.toLowerCase()}">Adjusted: ${threatAnalysis.recommended_risk_elevation}</span>
                        </div>
                    </div>
                `;
            }
            
            // Add fires list
            html += '<div class="firms-fires-list">';
            html += '<div class="firms-list-title">🛰️ Detected Fire Hotspots:</div>';
            
            fires.forEach((fire, index) => {
                const confidenceColor = getConfidenceColor(fire.confidence_level);
                html += `
                    <div class="firms-fire-item">
                        <div class="fire-marker" style="background-color: ${confidenceColor}"></div>
                        <div class="fire-details">
                            <div class="fire-header">
                                <span class="fire-distance">${fire.distance_km} km away</span>
                                <span class="fire-confidence badge badge-${fire.confidence_level}">
                                    ${fire.confidence_level} confidence
                                </span>
                            </div>
                            <div class="fire-meta">
                                <span class="fire-power">Power: ${fire.frp.toFixed(0)} MW</span>
                                <span class="fire-date">${fire.acq_date} ${fire.acq_time}</span>
                                <span class="fire-satellite">${fire.satellite}</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            
            // Show map
            firmsMapContainer.style.display = 'block';
            // Initialize map after HTML is rendered with location-specific view (no user marker)
            setTimeout(() => {
                initializeFIRMSMap(data.location.lat, data.location.lon, fires, false);
            }, 100);
        }
        
        // Add data freshness note
        html += `
            <div class="firms-freshness">
                <span class="freshness-icon">⏰</span>
                <span class="freshness-text">Data updated: ${new Date(data.timestamp).toLocaleTimeString()}</span>
            </div>
        `;
        
        firmsContent.innerHTML = html;
    }

    let firmsMapInstance = null;
    let liveFirmsMapInstance = null;

    function initializeFIRMSMap(userLat, userLon, fires, isGlobalView = false) {
        const mapElement = document.getElementById('firmsMap');
        
        // Destroy existing map if it exists
        if (firmsMapInstance) {
            firmsMapInstance.remove();
        }
        
        // If global view, center on continental US; otherwise on user location
        let centerLat = isGlobalView ? 39.5 : userLat;
        let centerLon = isGlobalView ? -98.35 : userLon;
        let zoomLevel = isGlobalView ? 4 : 9;
        
        // Create new map
        firmsMapInstance = L.map('firmsMap').setView([centerLat, centerLon], zoomLevel);
        
        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(firmsMapInstance);
        
        // Add fire markers (no user location marker anymore)
        fires.forEach(fire => {
            const color = getConfidenceColor(fire.confidence_level);
            
            const fireIcon = L.divIcon({
                className: 'fire-marker-icon',
                html: `<div style="background-color: ${color}; width: 16px; height: 16px; border-radius: 50%; border: 2px solid rgba(0, 0, 0, 0.3); box-shadow: 0 0 8px ${color}; animation: pulse 2s infinite;"></div>`,
                iconSize: [16, 16],
                iconAnchor: [8, 8]
            });
            
            const popup = `
                <div class="fire-popup">
                    <div class="fire-popup-title">🔥 Fire Detection</div>
                    ${fire.distance_km ? `
                    <div class="fire-popup-item">
                        <span class="fire-popup-label">Distance:</span>
                        <span class="fire-popup-value">${fire.distance_km} km</span>
                    </div>
                    ` : ''}
                    <div class="fire-popup-item">
                        <span class="fire-popup-label">Confidence:</span>
                        <span class="fire-popup-value">${fire.confidence_level}</span>
                    </div>
                    <div class="fire-popup-item">
                        <span class="fire-popup-label">Power:</span>
                        <span class="fire-popup-value">${fire.frp.toFixed(0)} MW</span>
                    </div>
                    <div class="fire-popup-item">
                        <span class="fire-popup-label">Date/Time:</span>
                        <span class="fire-popup-value">${fire.acq_date} ${fire.acq_time}</span>
                    </div>
                    <div class="fire-popup-item">
                        <span class="fire-popup-label">Satellite:</span>
                        <span class="fire-popup-value">${fire.satellite}</span>
                    </div>
                </div>
            `;
            
            L.marker([fire.lat, fire.lon], { icon: fireIcon })
                .bindPopup(popup)
                .addTo(firmsMapInstance);
        });
        
        // Fit bounds to show all fires if not global view
        if (!isGlobalView && fires.length > 0) {
            const bounds = L.latLngBounds([[userLat, userLon]]);
            fires.forEach(fire => {
                bounds.extend([fire.lat, fire.lon]);
            });
            firmsMapInstance.fitBounds(bounds, { padding: [50, 50] });
        }
    }

    function initializeLiveFirmsMap(fires) {
        const mapElement = document.getElementById('liveFirmsMap');
        if (!mapElement) return;
        
        // Destroy existing map if it exists
        if (liveFirmsMapInstance) {
            liveFirmsMapInstance.remove();
        }
        
        // Center on continental USA/Canada
        const centerLat = 50.0;
        const centerLon = -100.0;
        const zoomLevel = 4;
        
        // Create new map
        liveFirmsMapInstance = L.map('liveFirmsMap').setView([centerLat, centerLon], zoomLevel);
        
        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(liveFirmsMapInstance);
        
        // Add fire markers (no user location marker)
        fires.forEach(fire => {
            const color = getConfidenceColor(fire.confidence_level);
            
            const fireIcon = L.divIcon({
                className: 'fire-marker-icon',
                html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid rgba(0, 0, 0, 0.3); box-shadow: 0 0 6px ${color}; animation: pulse 2s infinite;"></div>`,
                iconSize: [12, 12],
                iconAnchor: [6, 6]
            });
            
            const popup = `
                <div class="fire-popup">
                    <div class="fire-popup-title">🔥 Fire Detection</div>
                    <div class="fire-popup-item">
                        <span class="fire-popup-label">Confidence:</span>
                        <span class="fire-popup-value">${fire.confidence_level}</span>
                    </div>
                    <div class="fire-popup-item">
                        <span class="fire-popup-label">Power:</span>
                        <span class="fire-popup-value">${fire.frp.toFixed(0)} MW</span>
                    </div>
                    <div class="fire-popup-item">
                        <span class="fire-popup-label">Date/Time:</span>
                        <span class="fire-popup-value">${fire.acq_date} ${fire.acq_time}</span>
                    </div>
                    <div class="fire-popup-item">
                        <span class="fire-popup-label">Satellite:</span>
                        <span class="fire-popup-value">${fire.satellite}</span>
                    </div>
                </div>
            `;
            
            L.marker([fire.lat, fire.lon], { icon: fireIcon })
                .bindPopup(popup)
                .addTo(liveFirmsMapInstance);
        });
        
        // Fit bounds to show all fires
        if (fires.length > 0) {
            const bounds = L.latLngBounds(fires.map(fire => [fire.lat, fire.lon]));
            liveFirmsMapInstance.fitBounds(bounds, { padding: [50, 50] });
        }
        
        // Add pulse animation if not already added
        if (!document.querySelector('style[data-pulse]')) {
            const style = document.createElement('style');
            style.setAttribute('data-pulse', 'true');
            style.textContent = `
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.6; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    // Fetch recent global FIRMS fires and initialize map on page load
    async function fetchRecentFires() {
        const firmsContent = document.getElementById('firmsContent');
        const firmsMapContainer = document.getElementById('firmsMapContainer');
        try {
            firmsMapContainer.style.display = 'block';
            firmsContent.innerHTML = '<div class="firms-loading">Loading recent US/Canada wildfire data...</div>';

            const resp = await fetch('/api/firms/recent?days=7&max=2000');
            if (!resp.ok) throw new Error('Failed to fetch recent fires');
            const json = await resp.json();
            if (json.success && json.data) {
                const fires = json.data.fires || [];
                // Render a short summary in the content area
                firmsContent.innerHTML = `<div class="firms-list-title">🛰️ Active Hotspots (USA/Canada, last 7 days): ${fires.length}</div>`;
                // Initialize map for global USA/Canada view
                initializeFIRMSMap(39.5, -98.35, fires, true);
            } else {
                firmsContent.innerHTML = '<div class="firms-no-data">No recent FIRMS data available</div>';
            }
        } catch (err) {
            console.warn('Error fetching recent FIRMS fires:', err);
            firmsContent.innerHTML = '<div class="firms-no-data">Satellite fire data unavailable</div>';
        }
    }

    // Fetch and display live wildfires for the main page map
    async function fetchLiveWildfires() {
        const liveFirmsContent = document.getElementById('liveFirmsContent');
        const liveFirmsMapContainer = document.getElementById('liveFirmsMapContainer');
        
        try {
            liveFirmsMapContainer.style.display = 'block';
            liveFirmsContent.innerHTML = '<div class="firms-loading">Loading live wildfire data from NASA FIRMS...</div>';

            const resp = await fetch('/api/firms/recent?days=7&max=2000');
            if (!resp.ok) throw new Error('Failed to fetch recent fires');
            const json = await resp.json();
            
            if (json.success && json.data) {
                const fires = json.data.fires || [];
                
                // Update content with fire count
                liveFirmsContent.innerHTML = `
                    <div class="firms-status good">
                        <div class="firms-status-icon">🔥</div>
                        <div class="firms-status-text">
                            <div class="firms-status-title">${fires.length} Active Wildfires Detected</div>
                            <div class="firms-status-desc">Live satellite data from NASA FIRMS (last 7 days)</div>
                        </div>
                    </div>
                `;
                
                // Initialize map with all fires
                setTimeout(() => {
                    initializeLiveFirmsMap(fires);
                }, 100);
            } else {
                liveFirmsContent.innerHTML = '<div class="firms-no-data">No recent FIRMS data available</div>';
            }
        } catch (err) {
            console.error('Error fetching live wildfires:', err);
            liveFirmsContent.innerHTML = '<div class="firms-no-data">Unable to load satellite fire data. Please try again later.</div>';
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

    // Initialize global FIRMS view on page load
    try {
        fetchRecentFires();
    } catch (e) {
        console.warn('Failed to initialize recent FIRMS fires:', e);
    }

    // Initialize live wildfires map on page load
    try {
        fetchLiveWildfires();
    } catch (e) {
        console.warn('Failed to initialize live wildfires map:', e);
    }

});
