:- discontiguous handle_input/1.
:- discontiguous area_details/8.
:- style_check(-singleton).

% ============================================
% SCORING SYSTEM (Define FIRST)
% ============================================

% Fuel moisture scoring (most critical factor)
fuel_score(extremely_dry, 30).
fuel_score(dry, 20).
fuel_score(moderate, 10).
fuel_score(moist, 0).

% Temperature scoring
temp_score(very_high, 20).
temp_score(high, 15).
temp_score(moderate, 8).
temp_score(low, 0).

% Humidity scoring (inverse - lower humidity = higher risk)
humidity_score(very_low, 20).
humidity_score(low, 15).
humidity_score(moderate, 8).
humidity_score(high, 0).

% Wind speed scoring
wind_score(extreme, 20).
wind_score(strong, 15).
wind_score(moderate, 8).
wind_score(low, 0).

% Topography scoring (steeper = faster spread)
topo_score(very_steep, 15).
topo_score(steep, 10).
topo_score(hilly, 5).
topo_score(flat, 0).

% Population density scoring (higher risk = more lives at stake)
pop_score(high, 10).
pop_score(medium, 5).
pop_score(low, 0).

% Infrastructure scoring (critical infrastructure = higher consequence)
infra_score(critical, 15).
infra_score(slightly_critical, 10).
infra_score(no_critical, 5).
infra_score(no, 0).

% Risk level classification based on total score
classify_by_score(Score, 'Extreme') :- Score >= 100, !.
classify_by_score(Score, 'Very High') :- Score >= 80, !.
classify_by_score(Score, 'High') :- Score >= 60, !.
classify_by_score(Score, 'Medium') :- Score >= 40, !.
classify_by_score(Score, 'Low') :- Score >= 20, !.
classify_by_score(_, 'Very Low').

% ============================================
% FIRE SPREAD PREDICTION (Rothermel Model)
% ============================================

rothermel(I, P, W, S, B, E, H, R) :-
   R is (I * P * (1 + W + S)) / (B * E * H),
   format('Rate of Spread: ~2f ft/min~n', [R]).

byram(H, W, R, I_fireline) :-
   I_fireline is H * W * (R * 0.00508).

fireline_intensity(I, P, W, S, B, E, H, H_Yield, A_Fuel) :-
   rothermel(I, P, W, S, B, E, H, R),
   byram(H_Yield, A_Fuel, R, Result),
   Result is H_Yield * A_Fuel * (R * 0.00508),
   format('Fireline Intensity: ~2f kW/m~n', [Result]).

flame_length(I) :-
   L is 0.45 * (I ** 0.46),
   format('Flame Length: ~2f m~n', [L]).

flame_height(C, I, N, H) :-
   H is C * (I ** N),
   format('Flame Height: ~2f m~n', [H]).

calculate_safety_zone(H, R) :-
   R is 4 * H,
   format('Safety Zone: ~2f m~n', [R]).

safety_zone(C, I, N, H, R) :-
   flame_height(C, I, N, H),
   calculate_safety_zone(H, R).

calculate_burn_area(R, T) :-
   A is (R * T) ** 2,
   format('Burn Area Estimation: ~2f m^2~n', [A]).

calculate_escape_time(D, R) :-
   T is D / R,
   format('Escape Time: ~2f s~n', [T]).

% ============================================
% AREA DEFINITIONS & PARAMETERS
% ============================================

fuels(moist). fuels(moderate). fuels(dry). fuels(extremely_dry).
temperature(low). temperature(moderate). temperature(high). temperature(very_high).
humidity(high). humidity(moderate). humidity(low). humidity(very_low).
wind_speed(low). wind_speed(moderate). wind_speed(strong). wind_speed(extreme).
topography(flat). topography(hilly). topography(steep). topography(very_steep).
population_density(low). population_density(medium). population_density(high).
infrastructure(no). infrastructure(no_critical). infrastructure(slightly_critical). infrastructure(critical).

% Predefined areas
area_details(area_1, extremely_dry, very_high, very_low, extreme, very_steep, high, critical).
area_details(area_2, moist, low, high, low, flat, low, no).
area_details(area_3, dry, moderate, moderate, moderate, hilly, medium, slightly_critical).
area_details(area_4, dry, high, low, strong, steep, high, critical).
area_details(area_5, dry, high, low, strong, steep, high, slightly_critical).
area_details(frisco_tx, moderate, low, low, moderate, flat, high, no_critical).
area_details(los_angeles_ca, moist, moderate, very_low, low, flat, high, no_critical).
area_details(san_francisco_ca, moist, low, moderate, low, flat, high, no_critical).

% ============================================
% RISK CLASSIFICATION LOGIC
% ============================================

classify_fire_risk(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel) :-
    area_details(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra),
    calculate_risk(Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel).

calculate_risk(Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel) :-
    fuel_score(Fuel, FuelScore),
    temp_score(Temp, TempScore),
    humidity_score(Hum, HumScore),
    wind_score(Wind, WindScore),
    topo_score(Topo, TopoScore),
    pop_score(Pop, PopScore),
    infra_score(Infra, InfraScore),
    TotalScore is FuelScore + TempScore + HumScore + WindScore + TopoScore + PopScore + InfraScore,
    classify_by_score(TotalScore, RiskLevel).

% ============================================
% EVACUATION & RESOURCE RECOMMENDATIONS
% ============================================

evac_and_res(RiskLevel, Evac, Res) :-
    (
        RiskLevel = 'Very Low' -> Evac = no, Res = fire_engines;
        RiskLevel = 'Low' -> Evac = no, Res = fire_engines;
        RiskLevel = 'Medium' -> Evac = maybe, Res = fire_engines_and_water_tankers;
        RiskLevel = 'High' -> Evac = maybe, Res = fire_engines_and_water_tankers;
        RiskLevel = 'Very High' -> Evac = yes, Res = fire_engines_and_water_tankers;
        RiskLevel = 'Extreme' -> Evac = yes, Res = fire_engines_and_water_tankers_and_aerial_support;
        Evac = no, Res = fire_engines
    ).

% ============================================
% PRIORITY ORDERING & REPORTING
% ============================================

risk_level_value('Extreme', 6).
risk_level_value('Very High', 5).
risk_level_value('High', 4).
risk_level_value('Medium', 3).
risk_level_value('Low', 2).
risk_level_value('Very Low', 1).
risk_level_value('Unknown', 0).

order_risks_by_level(OrderedResults) :-
    findall([RiskValue, Area, RiskLevel, Fuel, Temp, Hum, Wind, Topo, Pop, Infra],
    (
        classify_fire_risk(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel),
        risk_level_value(RiskLevel, RiskValue)
    ),
    Results),
    sort(1, @>=, Results, OrderedResults).

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

priority_list(OrderedResults) :-
    print_areas,
    order_risks_by_level(OrderedResults).

% ============================================
% JSON OUTPUT FOR PYTHON INTEGRATION
% ============================================

classify_fire_risk_json(Area) :-
    (   classify_fire_risk(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel)
    ->  evac_and_res(RiskLevel, Evac, Res),
        format('{"Area":"~w","RiskLevel":"~w","Fuel":"~w","Temp":"~w","Hum":"~w","Wind":"~w","Topo":"~w","Pop":"~w","Infra":"~w","Evacuation":"~w","Resources":"~w"}~n',
               [Area, RiskLevel, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, Evac, Res])
    ;   format('{"Area":"~w","RiskLevel":"Unknown","Evacuation":"no","Resources":"fire_engines"}~n', [Area])
    ).

% ============================================
% INTERACTIVE CHATBOT
% ============================================

chatbot :-
    write('Welcome to the FireGuard Chatbot! Type "exit" to quit.'), nl,
    repeat,
    write('What would you like to know? (fireline intensity, flame length, safety zone, burn area, escape time, risk level): '),
    read(Input),
    handle_input(Input),
    (Input == exit -> ! ; fail).

handle_input(fireline_intensity) :-
    write('Enter Reaction Intensity (I): '), read(I),
    write('Enter Propagating Flux Ratio (P): '), read(P),
    write('Enter Wind Factor (W): '), read(W),
    write('Enter Slope Factor (S): '), read(S),
    write('Enter Bulk Density (B): '), read(B),
    write('Enter Effective Heating Number (E): '), read(E),
    write('Enter Heat of Preignition (H): '), read(H),
    write('Enter Heat Yield (H_Yield): '), read(H_Yield),
    write('Enter Amount of Fuel Consumed (A_Fuel): '), read(A_Fuel),
    fireline_intensity(I, P, W, S, B, E, H, H_Yield, A_Fuel).

handle_input(flame_length) :-
    write('Please provide the Fireline Intensity (I): '), read(I),
    flame_length(I).

handle_input(safety_zone) :-
    write('Enter Empirical Constant (C): '), read(C),
    write('Enter Fireline Intensity (I): '), read(I),
    write('Enter Exponent (N): '), read(N),
    calculate_flame_height(C, I, N, H),
    safety_zone(C, I, N, H, _).

calculate_flame_height(C, I, N, H) :-
    H is C * I ^ N.

handle_input(burn_area) :-
    write('Please provide the Rate of fire spread (R): '), read(R),
    write('Please provide the Time elapsed since ignition (T): '), read(T),
    calculate_burn_area(R, T).

handle_input(escape_time) :-
    write('Distance to nearest safe zone (D): '), read(D),
    write(' Rate of fire spread (R): '), read(R),
    calculate_escape_time(D, R).

handle_input(risk_level) :-
    write('Please provide the Area (e.g., area_1): '), read(Area),
    write('Please provide the Fuel type (moist, moderate, dry, extremely_dry): '), read(Fuel),
    write('Please provide the Temperature (low, moderate, high, very_high): '), read(Temp),
    write('Please provide the Humidity (high, moderate, low, very_low): '), read(Hum),
    write('Please provide the Wind speed (low, moderate, strong, extreme): '), read(Wind),
    write('Please provide the Topography (flat, hilly, steep, very_steep): '), read(Topo),
    write('Please provide the Population density (low, medium, high): '), read(Pop),
    write('Please provide the Infrastructure (no, no_critical, slightly_critical, critical): '), read(Infra),
    calculate_risk(Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel),
    write('Fire Risk Level: '), write(RiskLevel), nl.

handle_input(exit) :-
    write('Goodbye!'), nl.