:- discontiguous handle_input/1.
:- discontiguous area_details/8.
:- dynamic area_details/8.
:- dynamic risk_cache/9.
:- dynamic risk_order/1.
:- initialization(precompute_risk_order).
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
area_details(frisco_tx, moderate, low, moderate, moderate, flat, high, no_critical).
area_details(los_angeles_ca, moist, low, high, low, flat, high, no_critical).
area_details(san_francisco_ca, moist, low, high, moderate, flat, high, no_critical).
area_details(user_location, moist, low, high, low, flat, low, no_critical).
area_details(frisco_test, moist, high, low, moderate, flat, high, no_critical).

% ============================================
% RISK CLASSIFICATION LOGIC
% ============================================

classify_fire_risk(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel) :-
    area_details(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra),
    risk_for_area(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel).

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

% Cache risk calculation to avoid recomputation for the same area parameters
risk_for_area(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel) :-
    risk_cache(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel), !.
risk_for_area(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel) :-
    calculate_risk(Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel),
    assertz(risk_cache(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel)).

% ============================================
% EVACUATION & RESOURCE RECOMMENDATIONS
% ============================================

% Enhanced evacuation recommendation based on multiple factors
% evac_recommendation(RiskLevel, Population, Infrastructure, FireProximity, EvacType, EvacUrgency)
evac_recommendation(RiskLevel, Population, Infrastructure, FireProximity, EvacType, EvacUrgency) :-
    % Determine base evacuation need from risk level
    base_evac_need(RiskLevel, BaseNeed),
    % Amplify based on population at risk
    population_factor(Population, PopFactor),
    % Amplify based on infrastructure importance
    infrastructure_factor(Infrastructure, InfraFactor),
    % Amplify based on active fire proximity
    fire_proximity_factor(FireProximity, FireFactor),
    % Calculate combined urgency score
    UrgencyScore is BaseNeed + PopFactor + InfraFactor + FireFactor,
    classify_evacuation(UrgencyScore, EvacType, EvacUrgency).

% Base evacuation need by risk level (0-10 scale)
base_evac_need('Very Low', 0).
base_evac_need('Low', 1).
base_evac_need('Medium', 3).
base_evac_need('High', 6).
base_evac_need('Very High', 8).
base_evac_need('Extreme', 10).

% Population factor (amplifies evacuation need)
population_factor(low, 0).
population_factor(medium, 2).
population_factor(high, 4).

% Infrastructure criticality factor (amplifies evacuation need)
infrastructure_factor(no, 0).
infrastructure_factor(no_critical, 0).
infrastructure_factor(slightly_critical, 1).
infrastructure_factor(critical, 3).

% Fire proximity factor (0-5km, 5-15km, 15-25km, 25km+)
fire_proximity_factor(none, 0).           % No active fires
fire_proximity_factor(far, 0.5).          % 25+ km away
fire_proximity_factor(distant, 1).        % 15-25 km away
fire_proximity_factor(moderate, 3).       % 5-15 km away
fire_proximity_factor(close, 5).          % Within 5 km
fire_proximity_factor(critical, 8).       % Within 2 km

% Evacuation classification based on urgency score
classify_evacuation(Score, no_evac, none) :- Score < 2, !.
classify_evacuation(Score, prepare, low) :- Score < 4, !.
classify_evacuation(Score, prepare, high) :- Score < 6, !.
classify_evacuation(Score, evacuate, immediate) :- Score < 8, !.
classify_evacuation(_, evacuate, mandatory).

% Detailed resource allocation considering all factors
allocate_resources(RiskLevel, Population, Infrastructure, FireProximity, Resources, Quantities) :-
    allocate_base_resources(RiskLevel, BaseRes),
    scale_by_population(Population, BaseRes, PopScaled),
    enhance_for_infrastructure(Infrastructure, PopScaled, InfraEnhanced),
    enhance_for_proximity(FireProximity, InfraEnhanced, FinalRes),
    calculate_quantities(FinalRes, Population, FireProximity, Resources, Quantities).

allocate_base_resources('Very Low', [fire_trucks:1]).
allocate_base_resources('Low', [fire_trucks:2]).
allocate_base_resources('Medium', [fire_trucks:3, water_tankers:2, helicopters:0]).
allocate_base_resources('High', [fire_trucks:4, water_tankers:3, helicopters:1]).
allocate_base_resources('Very High', [fire_trucks:6, water_tankers:4, helicopters:2, command_center:1]).
allocate_base_resources('Extreme', [fire_trucks:8, water_tankers:6, helicopters:3, command_center:1, aerial_support:2]).

% Scale resources up for high population areas
scale_by_population(low, Resources, Resources).
scale_by_population(medium, Resources, Scaled) :-
    multiply_resource_list(Resources, 1.5, Scaled).
scale_by_population(high, Resources, Scaled) :-
    multiply_resource_list(Resources, 2.0, Scaled).

% Enhance for critical infrastructure
enhance_for_infrastructure(no, Resources, Resources).
enhance_for_infrastructure(no_critical, Resources, Resources).
enhance_for_infrastructure(slightly_critical, Resources, Enhanced) :-
    add_resource(Resources, command_posts:1, Enhanced).
enhance_for_infrastructure(critical, Resources, Enhanced) :-
    add_resource(Resources, command_center:1, R1),
    add_resource(R1, additional_personnel:50, Enhanced).

% Enhance for fire proximity (reduce response time)
enhance_for_proximity(none, Resources, Resources).
enhance_for_proximity(far, Resources, Resources).
enhance_for_proximity(distant, Resources, Resources).
enhance_for_proximity(moderate, Resources, Enhanced) :-
    add_resource(Resources, water_tankers:2, R1),
    add_resource(R1, aerial_reconnaissance:1, Enhanced).
enhance_for_proximity(close, Resources, Enhanced) :-
    add_resource(Resources, aerial_support:1, R1),
    add_resource(R1, ground_crews:100, R2),
    add_resource(R2, heavy_equipment:5, Enhanced).
enhance_for_proximity(critical, Resources, Enhanced) :-
    add_resource(Resources, aerial_support:2, R1),
    add_resource(R1, ground_crews:200, R2),
    add_resource(R2, heavy_equipment:8, R3),
    add_resource(R3, ambulance_units:10, Enhanced).

% Helper: multiply resource quantities
multiply_resource_list([], _, []).
multiply_resource_list([Resource:Qty|Rest], Factor, [Resource:ScaledQty|Scaled]) :-
    ScaledQty is ceiling(Qty * Factor),
    multiply_resource_list(Rest, Factor, Scaled).

% Helper: add a resource to list
add_resource(List, Resource, [Resource|List]).

% Calculate specific resource quantities based on area size and threat
calculate_quantities(ResourceList, PopDensity, FireProximity, FormattedResources, Quantities) :-
    format_resources(ResourceList, FormattedResources),
    quantity_adjustments(PopDensity, FireProximity, ResourceList, Quantities).

% Format resource list for output
format_resources([], []).
format_resources([Resource:_|Rest], [Resource|Formatted]) :-
    format_resources(Rest, Formatted).

% Provide specific quantity recommendations
quantity_adjustments(PopDensity, FireProximity, Resources, Adjustments) :-
    findall(Adj, resource_quantity_rule(PopDensity, FireProximity, Resources, Adj), Adjustments).

resource_quantity_rule(medium, moderate, Resources, "Dispatch helicopters within 30 minutes for water drops") :-
    member(helicopters:N, Resources), N > 0.
resource_quantity_rule(high, close, _, "Establish two command centers for coordinated response").
resource_quantity_rule(high, critical, _, "Activate emergency mutual aid agreements with neighboring jurisdictions").
resource_quantity_rule(_, moderate, Resources, "Pre-position water tankers at strategic locations") :-
    member(water_tankers:N, Resources), N >= 2.
resource_quantity_rule(_, close, _, "Establish evacuation shelters and assembly points immediately").
resource_quantity_rule(_, critical, _, "Activate state/federal emergency declaration procedures").

% Backward compatibility: simple recommendation
evac_and_res(RiskLevel, Evac, Res) :-
    evac_recommendation(RiskLevel, low, no, none, EvacType, _),
    evac_type_to_simple(EvacType, Evac),
    allocate_base_resources(RiskLevel, ResourceList),
    format_resources(ResourceList, ResNames),
    atom_concat_list(ResNames, Res).

evac_type_to_simple(no_evac, no).
evac_type_to_simple(prepare, maybe).
evac_type_to_simple(evacuate, yes).

% Helper: concatenate atoms
atom_concat_list([], '').
atom_concat_list([X], X) :- !.
atom_concat_list([H|T], Result) :-
    atom_concat_list(T, Rest),
    atomic_concat(H, '_and_', Temp),
    atomic_concat(Temp, Rest, Result).

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
    risk_order(OrderedResults), !.
order_risks_by_level(OrderedResults) :-
    findall([RiskValue, Area, RiskLevel, Fuel, Temp, Hum, Wind, Topo, Pop, Infra],
        (
            classify_fire_risk(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel),
            risk_level_value(RiskLevel, RiskValue)
        ),
        Results),
    sort(1, @>=, Results, OrderedResults),
    retractall(risk_order(_)),
    assertz(risk_order(OrderedResults)).

% Precompute cache and ordered list for faster startup queries
precompute_risk_order :-
    retractall(risk_cache(_, _, _, _, _, _, _, _, _)),
    retractall(risk_order(_)),
    findall(_, (
        area_details(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra),
        risk_for_area(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, _)
    ), _),
    order_risks_by_level(_).

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

% Additional predefined areas (atoms only to avoid parsing overhead)
area_details(my_location_33_1960_-96_7633, moderate, low, low, moderate, flat, high, no_critical).
area_details(southern_california_la_ventura, moist, low, high, strong, hilly, low, no_critical).
area_details(socal, moderate, moderate, low, moderate, flat, high, no_critical).
area_details(texas, moderate, moderate, very_low, moderate, flat, high, no_critical).
area_details(pacific_nw, moist, low, high, moderate, flat, high, no_critical).
area_details(arizona, moist, moderate, moderate, low, flat, high, no_critical).
area_details(colorado, moist, low, low, low, flat, high, no_critical).
area_details(norcal, moist, low, high, moderate, flat, high, no_critical).
