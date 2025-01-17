
% ------------------- Fire Intensity and Safety Zones -------------------

% Fire Spread Prediction
% I = Reaction Intensity
% P = Propagating Flux Ratio
% W = Wind Factor
% S = Slope Factor
% B = Bulk Density
% E = Effective Heating Number
% H = Heat of Preignition
rothermel(I, P, W, S, B, E, H) :-
   R is (I * P * (1 + W + S)) / (B * E * H),
   format('Rate of Spread: ~2f ft/min~n', [R]).

% Fireline Intensity
% H_Yield = Heat Yield
% A_Fuel = Amount of Fuel Consumed
byram(H, W, R) :-
   I_fireline is H * W * (R * 0.00508),
   format('Fireline Intensity: ~2f kW/m~n', [I_fireline]).

% Total fireline intensity
fireline_intensity(I, P, W, S, B, E, H, H_Yield, A_Fuel, Intensity) :-
   rothermel(I, P, W, S, B, E, H, R),
   byram(H_Yield, A_Fuel, R, Intensity).

% Flame Length
% I = Fireline Intensity
flame_length(I) :-
   L is 0.45 * (I ** 0.46),
   format('Flame Length: ~2f m~n', [L]).

% Flame Height
% C and N = Empirical coefficients that depend on fuel type and wind conditions.
% I = Fireline intensity
% H = Flame height
flame_height(C, I, N) :-
   H is C * (I ** N),
   format('Flame Height: ~2f m~n', [H]).

% Safety Zone
% H = Flame height (in feet or meters)
calculate_safety_zone(H) :-
   R is 4 * H,
   format('Safety Zone: ~2f m~n', [R]).

% Combined safety zone calculation based on inputs
safety_zone_given_flame_height(C, I, N, H, R) :-
   flame_height(C, I, N, H),
   calculate_safety_zone(H, R).

% Burn Area Estimation
% R = Rate of fire spread
% T = Time elapsed since ignition
calculate_burn_area(R, T) :-
   A is (R * T) ** 2,
   format('Burn Area Estimation: ~2f m^2~n', [A]).

% Escape Time
% D = Distance to nearest safe zone (m or ft).
% R = Rate of fire spread (m/s or ft/min).
calculate_escape_time(D, R) :-
   T is D / R,
   format('Escape Time: ~2f s~n', [T]).

% ------------------- Test Cases --------------------------------
% rothermel(1000, 0.5, 1.2, 0.3, 5, 0.4, 250).
% byram(8000, 1.5, 2.5).
% flame_length(152.4).
% flame_height(0.2, 152.4, 0.5).
% calculate_safety_zone(1.97).
% calculate_burn_area(2.5, 10).
% calculate_escape_time(500, 2.5).

% rothermel(1000, 0.5, 1.2, 0.3, 5, 0.4, 250), byram(8000, 1.5, 2.5), flame_length(152.4), flame_height(0.2, 152.4, 0.5), calculate_safety_zone(1.97), calculate_burn_area(2.5, 10), calculate_escape_time(500, 2.5).


% ------------------- Firefighters' Focus -------------------
% These predicates help firefighters determine the areas to focus on based on fire intensity, flame length, and flame height.

% ------------------- Monitoring Fires and First Responders -------------------

% National Fire Danger Rating System (NFDRS)
fuels(moist).
fuels(moderate).
fuels(dry).
fuels(extremely_dry).

temperature(low).
temperature(moderate).
temperature(high).
temperature(very_high).

humidity(high).
humidity(moderate).
humidity(low).
humidity(very_low).

wind_speed(low).
wind_speed(moderate).
wind_speed(strong).
wind_speed(extreme).

topography(flat).
topography(hilly).
topography(steep).
topography(very_steep).

population_density(low).
population_density(medium).
population_density(high).

infrastructure(no).
infrastructure(no_critical).
infrastructure(slightly_critical).
infrastructure(critical).

% Define the area details

area_details(area_1, extremely_dry, very_high, very_low, extreme, very_steep, high, critical).

area_details(area_2, moist, low, high, low, flat, low, no).

area_details(area_3, dry, moderate, moderate, moderate, hilly, medium, slightly_critical).

area_details(area_4, dry, high, low, strong, steep, high, critical).

area_details(area_5, dry, high, low, strong, steep, high, slightly_critical).

% Fire risk classification based on environmental factors
classify_fire_risk(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel) :-
    area_details(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra),
    calculate_risk(Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel).

% Calculate the risk level dynamically based on conditions
calculate_risk(Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel) :-
    (
        % Low Risk
        (Fuel = moist; Fuel = moderate),
        (Temp = low; Temp = moderate),
        (Hum = high; Hum = moderate),
        (Wind = low; Wind = moderate),
        (Topo = flat; Topo = hilly),
        Pop = low,
        (Infra = no; Infra = no_critical),
        \+ (Fuel = dry),
        \+ (Temp = high),
        \+ (Hum = low),
        \+ (Wind = strong),
        \+ (Topo = steep),
        \+ (Pop = high),
        \+ (Infra = critical)
    ->  RiskLevel = 'Low'
    ;
        % Medium Risk
        (Fuel = moderate; Fuel = dry),
        (Temp = moderate; Temp = high),
        (Hum = moderate; Hum = low),
        Wind = moderate,
        (Topo = hilly; Topo = steep),
        Pop = medium,
        Infra = slightly_critical,
        \+ (Fuel = extremely_dry),
        \+ (Temp = very_high),
        \+ (Hum = very_low),
        \+ (Wind = extreme),
        \+ (Topo = very_steep),
        \+ (Pop = high),
        \+ (Infra = critical)
    ->  RiskLevel = 'Medium'
    ;
        % High Risk
        Fuel = dry,
        Temp = high,
        Hum = low,
        (Wind = moderate; Wind = strong),
        (Topo = steep; Topo = very_steep),
        (Pop = medium; Pop = high),
        (Infra = slightly_critical),
        \+ (Fuel = extremely_dry),
        \+ (Temp = very_high),
        \+ (Hum = very_low),
        \+ (Wind = extreme)
    ->  RiskLevel = 'High'
    ;
        % Very High Risk
        (Fuel = dry; Fuel = extremely_dry),
        (Temp = high; Temp = very_high),
        Hum = low,
        Wind = strong,
        (Topo = steep; Topo = very_steep),
        (Pop = medium; Pop = high),
        Infra = critical,
        \+ (Hum = very_low),
        \+ (Wind = extreme)
    ->  RiskLevel = 'Very High'
    ;
        % Extreme Risk
        Fuel = extremely_dry,
        Temp = very_high,
        Hum = very_low,
        Wind = extreme,
        Topo = very_steep,
        Pop = high,
        Infra = critical
    ->  RiskLevel = 'Extreme'
    ;
        RiskLevel = 'Unknown'
    ).

% Evacuation and Resource Requirements based on Risk Level
evac_and_res(RiskLevel, Evac, Res) :-
    (
        RiskLevel = 'Low' -> Evac = no, Res = fire_engines;
        RiskLevel = 'Medium' -> Evac = maybe, Res = fire_engines_and_water_tankers;
        RiskLevel = 'High' -> Evac = maybe, Res = fire_engines_and_water_tankers;
        RiskLevel = 'Very High' -> Evac = yes, Res = fire_engines_and_water_tankers;
        RiskLevel = 'Extreme' -> Evac = yes, Res = fire_engines_and_water_tankers_and_aerial_support;
        Evac = no, Res = fire_engines
    ).

% New predicate to print areas
print_areas :-
    findall([Area, RiskLevel, Fuel, Temp, Hum, Wind, Topo, Pop, Infra],
            classify_fire_risk(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel),
            Results),
    print_areas(Results, 5).

print_areas([], _).
print_areas(_, 0).
print_areas([[Area, RiskLevel, Fuel, Temp, Hum, Wind, Topo, Pop, Infra]|Rest], N) :-
    evac_and_res(RiskLevel, Evac, Res),
    write('Area: '), write(Area), nl,
    write('Risk Level: '), write(RiskLevel), nl,
    write('Evacuation Needed: '), write(Evac), nl,
    write('Resources Needed: '), write(Res), nl,
    write('Fuel: '), write(Fuel), nl,
    write('Temperature: '), write(Temp), nl,
    write('Humidity: '), write(Hum), nl,
    write('Wind: '), write(Wind), nl,
    write('Topography: '), write(Topo), nl,
    write('Population Density: '), write(Pop), nl,
    write('Infrastructure: '), write(Infra), nl,
    nl,
    N1 is N - 1,
    print_areas(Rest, N1).

% Order areas by risk level dynamically
order_risks_by_level(OrderedResults) :-
    findall([RiskValue, Area, RiskLevel, Fuel, Temp, Hum, Wind, Topo, Pop, Infra],
    (
        classify_fire_risk(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel),
        risk_level_value(RiskLevel, RiskValue)
    ),
    Results),
    sort(1, @>=, Results, OrderedResults).

% Risk level values for sorting
risk_level_value('Extreme', 5).
risk_level_value('Very High', 4).
risk_level_value('High', 3).
risk_level_value('Medium', 2).
risk_level_value('Low', 1).
risk_level_value('Unknown', 0).

% Main query to print areas and get ordered results
main_query(OrderedResults) :-
    print_areas,
    order_risks_by_level(OrderedResults).

% ------------------- First Responders' Focus -------------------
% This part focuses on monitoring fire risks, evacuation status, and the required resources for first responders.


