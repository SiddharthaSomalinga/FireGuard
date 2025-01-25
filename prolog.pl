:- discontiguous handle_input/1.
:- style_check(-singleton).

% Fire Spread Prediction using Rothermel equation
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

% National Fire Danger Rating System (NFDRS)
fuels(moist). fuels(moderate). fuels(dry). fuels(extremely_dry).
temperature(low). temperature(moderate). temperature(high). temperature(very_high).
humidity(high). humidity(moderate). humidity(low). humidity(very_low).
wind_speed(low). wind_speed(moderate). wind_speed(strong). wind_speed(extreme).
topography(flat). topography(hilly). topography(steep). topography(very_steep).
population_density(low). population_density(medium). population_density(high).
infrastructure(no). infrastructure(no_critical). infrastructure(slightly_critical). infrastructure(critical).

area_details(area_1, extremely_dry, very_high, very_low, extreme, very_steep, high, critical).
area_details(area_2, moist, low, high, low, flat, low, no).
area_details(area_3, dry, moderate, moderate, moderate, hilly, medium, slightly_critical).
area_details(area_4, dry, high, low, strong, steep, high, critical).
area_details(area_5, dry, high, low, strong, steep, high, slightly_critical).

classify_fire_risk(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel) :-
    area_details(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra),
    calculate_risk(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel).

calculate_risk(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel) :-
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

evac_and_res(RiskLevel, Evac, Res) :-
    (
        RiskLevel = 'Low' -> Evac = no, Res = fire_engines;
        RiskLevel = 'Medium' -> Evac = maybe, Res = fire_engines_and_water_tankers;
        RiskLevel = 'High' -> Evac = maybe, Res = fire_engines_and_water_tankers;
        RiskLevel = 'Very High' -> Evac = yes, Res = fire_engines_and_water_tankers;
        RiskLevel = 'Extreme' -> Evac = yes, Res = fire_engines_and_water_tankers_and_aerial_support;
        Evac = no, Res = fire_engines
    ).

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

order_risks_by_level(OrderedResults) :-
    findall([RiskValue, Area, RiskLevel, Fuel, Temp, Hum, Wind, Topo, Pop, Infra],
    (
        classify_fire_risk(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel),
        risk_level_value(RiskLevel, RiskValue)
    ),
    Results),
    sort(1, @>=, Results, OrderedResults).

risk_level_value('Extreme', 5).
risk_level_value('Very High', 4).
risk_level_value('High', 3).
risk_level_value('Medium', 2).
risk_level_value('Low', 1).
risk_level_value('Unknown', 0).

priority_list(OrderedResults) :-
    print_areas,
    order_risks_by_level(OrderedResults).



chatbot :-
    write('Welcome to the FireGuard Chatbot! Type "exit" to quit.'), nl,
    repeat,
    write('What would you like to know? (fireline intensity, flame length, safety zone, burn area, escape time, risk level): '),
    read(Input),
    handle_input(Input),
    (Input == exit -> ! ; fail).



handle_input(fireline_intensity) :-
    write('Enter Reaction Intensity (I): '), nl,
    read(I),
    write('Enter Propagating Flux Ratio (P): '), nl,
    read(P),
    write('Enter Wind Factor (W): '), nl,
    read(W),
    write('Enter Slope Factor (S): '), nl,
    read(S),
    write('Enter Bulk Density (B): '), nl,
    read(B),
    write('Enter Effective Heating Number (E): '), nl,
    read(E),
    write('Enter Heat of Preignition (H): '), nl,
    read(H),
    write('Enter Heat Yield (H_Yield): '), nl,
    read(H_Yield),
    write('Enter Amount of Fuel Consumed (A_Fuel): '), nl,
    read(A_Fuel),
    fireline_intensity(I, P, W, S, B, E, H, H_Yield, A_Fuel).

handle_input(flame_length) :-
    write('Please provide the Fireline Intensity (I): '), read(I),
    flame_length(I).

handle_input(safety_zone) :-
    write('Enter Empirical Constant (C): '), nl,
    read(C),
    write('Enter Fireline Intensity (I): '), nl,
    read(I),
    write('Enter Exponent (N): '), nl,
    read(N),
    calculate_flame_height(C, I, N, H),
    safety_zone(C, I, N, H, _).

calculate_flame_height(C, I, N, H) :-
    H is C * I ^ N.

handle_input(burn_area) :-
    write('Please provide the Rate of fire spread (R): '), nl,
    read(R),
    write('Please provide the Time elapsed since ignition (T): '), nl,
    read(T),
    calculate_burn_area(R, T).

handle_input(escape_time) :-
    write('Distance to nearest safe zone (D): '), nl,
    read(D),
    write(' Rate of fire spread (R): '), nl,
    read(R),
    calculate_escape_time(D, R).

handle_input(risk_level) :-
    write('Please provide the Area (e.g., area_1): '), nl, read(Area),
    write('Please provide the Fuel type (moist, moderate, dry, extremely_dry): '), nl, read(Fuel),
    write('Please provide the Temperature (low, moderate, high, very_high): '), nl, read(Temp),
    write('Please provide the Humidity (high, moderate, low, very_low): '), nl, read(Hum),
    write('Please provide the Wind speed (low, moderate, strong, extreme): '), nl, read(Wind),
    write('Please provide the Topography (flat, hilly, steep, very_steep): '), nl, read(Topo),
    write('Please provide the Population density (low, medium, high): '), nl, read(Pop),
    write('Please provide the Infrastructure (no, no_critical, slightly_critical, critical): '), nl, read(Infra),
    calculate_risk(Area, Fuel, Temp, Hum, Wind, Topo, Pop, Infra, RiskLevel),
    write('Fire Risk Level: '), write(RiskLevel), nl.

handle_input(exit) :-
    write('Goodbye!'), nl.
