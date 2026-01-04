# FireGuard Evacuation & Resource Recommendations - Improvements

## Overview
The evacuation and resource recommendations logic has been significantly enhanced to consider multiple contextual factors beyond just the risk level classification.

---

## What Was Weak Before

### 1. **Oversimplified Evacuation Logic**
- **Before**: Only mapped risk level → yes/no evacuation
- **Problem**: Ignored population density, infrastructure criticality, and active fire proximity
- **Example**: A "Low" risk rural area with 1 person ≠ "Low" risk urban area with 50,000 people

### 2. **Generic Resource Allocation**
- **Before**: Only 3-4 resource levels across 6 risk categories
- **Problem**: Didn't scale by population, infrastructure importance, or fire threat
- **Example**: All "High" risk areas got the same resources regardless of whether they had 100 or 100,000 residents

### 3. **No Fire Proximity Integration**
- **Before**: Resource recommendations ignored active fire locations and distance
- **Problem**: Late detection of dangerous situations until fires were detected
- **Example**: Recommending 2 water tankers when a wildfire is 5km away

### 4. **Missing Context-Aware Actions**
- **Before**: No specific action items or timeline recommendations
- **Problem**: Users didn't know what to do or when to do it
- **Example**: "Evacuation needed" without practical next steps

### 5. **No Escalation Strategy**
- **Before**: All-or-nothing evacuation decisions
- **Problem**: No "prepare" phase between normal operations and full evacuation
- **Example**: Missing the window to pre-position resources before evacuation becomes necessary

---

## Improvements Implemented

### 1. **Multi-Factor Evacuation Scoring**

The new system calculates evacuation urgency as a composite score:

```
Urgency Score = Base Risk + Population Factor + Infrastructure Factor + Fire Proximity Factor
```

**Evacuation Types:**
- `no_evac` (Score < 2): No evacuation needed
- `prepare` (2-6): Prepare residents and pre-position resources
- `evacuate` (6+): Execute evacuation plan

**Urgency Levels:**
- `none`: Monitor situation
- `low`: Start preparations
- `high`: Complete preparations, stand by
- `immediate`: Begin evacuation
- `mandatory`: Immediate evacuation required

### 2. **Population-Aware Recommendations**

Resources are now scaled by population density:

- **Low density**: 1x base allocation (rural areas, sparse homes)
- **Medium density**: 1.5x allocation (suburban, small towns)  
- **High density**: 2x allocation + ground crews (urban centers, dense populations)

This ensures high-population areas receive proportionally more resources.

### 3. **Infrastructure-Based Enhancements**

Critical infrastructure (hospitals, power plants, water facilities, etc.) triggers:
- Dedicated command centers
- Additional personnel
- Priority resource allocation
- Enhanced communication systems

### 4. **Fire Proximity Integration**

Active fire distance dynamically adjusts resources:

| Proximity | Distance | Resource Adjustment |
|-----------|----------|-------------------|
| `critical` | < 2km | +2 helicopters, +2 tankers, +200 ground crew, ambulances |
| `close` | 2-5km | +2 helicopters, +1 tanker, +100 ground crew, ambulances |
| `moderate` | 5-15km | +1 tanker, +ambulances, aerial reconnaissance |
| `distant` | 15-25km | Moderate scaling |
| `far` | 25+ km | Minimal adjustment |
| `none` | No fires | Base allocation |

### 5. **Enhanced Resource Allocation**

Specific resource types (instead of generic categories):

```json
{
  "fire_trucks": 4,
  "water_tankers": 3,
  "helicopters": 1,
  "command_centers": 1,
  "ground_crews": 50,
  "ambulance_units": 2,
  "heavy_equipment": 0
}
```

Resources now scale dynamically based on:
- Risk level baseline
- Population scaling multiplier
- Infrastructure requirements
- Active fire proximity

### 6. **Action Item Generation**

Specific, actionable recommendations based on situation:

**For High Risk Levels:**
- "Activate incident command system"
- "Pre-position firefighting resources"
- "Alert residents of potential evacuation"

**For Active Fire Threats:**
- "Establish evacuation centers and assembly points"
- "Deploy aerial reconnaissance"
- "Increase alert status"

**For Preparation Phase:**
- "Brief residents on evacuation procedures"
- "Identify evacuation routes and shelters"
- "Review mutual aid agreements"

**For Evacuation:**
- "Execute evacuation plan immediately"
- "Establish traffic control at evacuation routes"
- "Set up reception and care facilities"

### 7. **Timeline Recommendations**

Context-aware action timelines:

**Mandatory Evacuation:**
```
Immediate: Begin evacuation - lives at imminent risk
5 minutes: All resources deployed  
15 minutes: Evacuation routes secured
```

**Immediate Evacuation:**
```
15 minutes: Prepare evacuation
30 minutes: Begin evacuation if conditions worsen
```

**Preparation Phase:**
```
Now: Alert residents and activate emergency operations
30 minutes: Position resources at strategic locations
2 hours: Review evacuation readiness
```

### 8. **Human-Readable Rationale**

Every recommendation includes clear reasoning:

```
"High fire risk classification (Very High) | High population density requires 
priority protection | Active fire threat detected nearby (close) | Fire detected 
2.3km away (High confidence). Evacuation recommended."
```

---

## Technical Implementation

### Prolog Enhancements (`prolog.pl`)

**New Predicates:**
- `evac_recommendation/6`: Multi-factor evacuation logic
- `base_evac_need/2`: Risk level baseline (0-10 scale)
- `population_factor/2`: Population density amplification (0-4)
- `infrastructure_factor/2`: Infrastructure importance (0-3)
- `fire_proximity_factor/2`: Active fire proximity (0-8)
- `classify_evacuation/3`: Score-to-action mapping
- `allocate_resources/6`: Detailed resource allocation
- `generate_action_items/N`: Context-aware actions
- `generate_timeline/N`: Action sequencing

### Python Enhancements (`app.py`)

**New Functions:**
- `generate_enhanced_recommendations()`: Orchestrates all factors
- `calculate_evacuation_score()`: Computes urgency score
- `allocate_resources_enhanced()`: Resource scaling logic
- `generate_action_items()`: Specific action recommendations
- `generate_timeline()`: Action timing
- `generate_evac_rationale()`: Human-readable explanations
- `map_fire_proximity()`: Distance → category mapping

### API Response Structure

```json
{
  "enhanced_recommendations": {
    "evacuation": {
      "type": "evacuate|prepare|no_evac",
      "urgency": "none|low|high|immediate|mandatory",
      "population_at_risk": "low|medium|high",
      "rationale": "Human-readable explanation"
    },
    "resources": {
      "fire_trucks": 8,
      "water_tankers": 6,
      "helicopters": 3,
      "command_centers": 1,
      "ground_crews": 200,
      "ambulances": 10,
      "special_equipment": ["Heavy machinery", "Equipment X"]
    },
    "actions": [
      "Action 1",
      "Action 2",
      "..."
    ],
    "timeline": {
      "immediate": "Description",
      "5_minutes": "Description",
      "15_minutes": "Description"
    }
  },
  "active_fire_threat": {
    "has_nearby_fires": true,
    "closest_fire_distance_km": 4.2,
    "fire_threat_level": "severe",
    "evacuation_recommended": true,
    "evacuation_reason": "Fire detected 4.2km away (High confidence)"
  }
}
```

---

## Usage Examples

### Scenario 1: Rural Low-Risk Area
```
Risk: Low | Population: Low | Infrastructure: None | Fire Distance: 50km

Result:
- Evacuation: No evacuation needed
- Resources: 2 fire trucks
- Actions: Monitor conditions, maintain readiness
```

### Scenario 2: High-Risk Urban Area
```
Risk: High | Population: High | Infrastructure: Critical | Fire Distance: 8km

Result:
- Evacuation: Prepare for evacuation (high urgency)
- Resources: 8 fire trucks, 4-5 water tankers, 2 helicopters, 1 command center, 
  100+ ground crew, 2+ ambulances
- Actions: Activate incident command, pre-position resources, alert residents, 
  establish evacuation centers, deploy aerial reconnaissance
- Timeline: Resources deployed in 30 minutes, evacuation readiness established
```

### Scenario 3: Critical Active Fire Threat
```
Risk: Extreme | Population: High | Infrastructure: Critical | Fire Distance: 2km

Result:
- Evacuation: Mandatory evacuation (immediate urgency)
- Resources: 8 fire trucks, 8 water tankers, 5+ helicopters, command center, 
  200+ ground crew, 10 ambulances, heavy equipment
- Actions: Execute evacuation immediately, aerial support engaged, traffic control, 
  reception facilities set up
- Timeline: Immediate evacuation, all resources deployed in 5 minutes
```

---

## Backward Compatibility

The original `evac_and_res/2` Prolog predicate is maintained for backward compatibility:
- Still returns simple `yes/no/maybe` evacuation
- Maps resource lists to atom format
- Existing code continues to work

---

## Future Enhancements

1. **Wind Direction Integration**: Adjust evacuation zones based on fire wind
2. **Evacuation Route Optimization**: Recommend specific routes based on terrain
3. **Shelter Capacity Planning**: Calculate needed shelters by population size
4. **Mutual Aid Triggers**: Automatically request aid from neighboring jurisdictions
5. **Real-time Updates**: Stream updates as fire conditions change
6. **Historical Data**: Learn from past fires to improve predictions
7. **Communication Plans**: Generate specific messaging for residents
8. **Resource Staging Areas**: Recommend optimal pre-positioning locations

---

## Testing

Run the enhanced system:

```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 33.1960,
    "longitude": -96.7633,
    "area_name": "test_location"
  }'
```

Check the response for:
- `enhanced_recommendations` object with all components
- `active_fire_threat` when fires are nearby
- Specific action items and timeline
- Population-aware resource allocation
