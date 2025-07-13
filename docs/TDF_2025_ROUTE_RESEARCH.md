# TDF 2025 Official Route Research & Corrections

## Research Summary

Based on official Tour de France 2025 route information from letour.fr and ProcyclingStats, I've fact-checked and corrected our mission configuration to match the actual 2025 TDF route.

## Official Route Breakdown

**Total Statistics:**
- 21 stages total
- 7 flat stages  
- 6 hilly stages
- 6 mountain stages (with 5 mountain finishes)
- 2 time trials (stages 5 & 13)
- Distance: 3,338.8 km

## Key Corrections Made

### Stage 6: Bayeux > Vire Normandie (201.5km)
- **Before**: "mountain" 
- **After**: "hilly" ✅
- **Source**: Official letour.fr classification

### Stage 10: Ennezat > Le Mont-Dore Puy de Sancy (165.3km)  
- **Before**: "flat"
- **After**: "mountain" ✅
- **Source**: Official letour.fr classification + Mountain finish

### Complete Stage Classification Update

Updated our mission config with all 21 stages based on official data:

**Flat Stages (7)**: 1, 3, 8, 9, 11, 20, 21
**Hilly Stages (6)**: 2, 4, 6, 7, 15, 17  
**Mountain Stages (6)**: 10, 12, 14, 16, 18, 19
**Time Trials (2)**: 5 (Caen, 33km), 13 (Loudenvielle > Peyragudes, 10.9km)

## Mountain Finishes (5 confirmed)
- Stage 12: Auch > **Hautacam** (180.6km)
- Stage 14: Pau > **Luchon-Superbagnères** (182.6km) 
- Stage 16: Montpellier > **Mont Ventoux** (171.5km)
- Stage 18: Vif > **Courchevel Col de la Loze** (171.5km)
- Stage 19: Albertville > **La Plagne** (129.9km)

## TDF Points Data Corrections

Updated `output/tdf_points.json` to reflect corrected stage types:
- Stage 6: Changed from "mountain" (10 pts) to "hilly" (7 pts)
- Total points recalculated: 48 → 45 points

## Validation
All stage types now match official Tour de France 2025 route classifications, ensuring accurate simulation and points scoring.

---
*Generated on: 2025-07-13*
*Sources: letour.fr, ProcyclingStats*
