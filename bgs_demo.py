"""
SIMPLE SEED GROWTH ALGORITHM - 5 DISTRICTS
"""

import pandas as pd
import numpy as np
from collections import defaultdict

np.random.seed(42)

print("\n" + "="*60)
print("SIMPLE BALANCED GROWTH FROM SEEDS")
print("="*60)

# CREATE SIMPLE 5x5 GRID = 25 UNITS
print("\nCreating 25 geographic units in 5x5 grid...")

units = []
for row in range(5):
    for col in range(5):
        unit_id = row * 5 + col
        
        # Population around 100k each
        pop = 100000 + np.random.randint(-5000, 5000)
        
        # Voting: Left side more Dem, right side more Rep
        if col <= 1:  # Left columns
            dem_pct = 0.60
        elif col >= 3:  # Right columns
            dem_pct = 0.40
        else:  # Middle
            dem_pct = 0.50
        
        dem_pct += np.random.uniform(-0.05, 0.05)
        
        votes = 50000
        dem_votes = int(votes * dem_pct)
        rep_votes = votes - dem_votes
        
        units.append({
            'id': unit_id,
            'row': row,
            'col': col,
            'pop': pop,
            'dem': dem_votes,
            'rep': rep_votes,
            'dem_pct': dem_votes / votes
        })

df = pd.DataFrame(units)

total_dem = df['dem'].sum()
total_rep = df['rep'].sum()
statewide_dem_pct = total_dem / (total_dem + total_rep)

print(f"Created {len(df)} units")
print(f"Statewide: {statewide_dem_pct:.1%} D, {1-statewide_dem_pct:.1%} R")

# Target: 5 districts
N_DISTRICTS = 5
target_dem_seats = round(N_DISTRICTS * statewide_dem_pct)
target_rep_seats = N_DISTRICTS - target_dem_seats

print(f"Target: {target_dem_seats} D seats, {target_rep_seats} R seats")

# BUILD ADJACENCY (4-connectivity: up, down, left, right)

adjacency = defaultdict(set)
for _, u1 in df.iterrows():
    for _, u2 in df.iterrows():
        if u1['id'] != u2['id']:
            # Adjacent if next to each other (not diagonal)
            if (abs(u1['row'] - u2['row']) == 1 and u1['col'] == u2['col']) or \
               (abs(u1['col'] - u2['col']) == 1 and u1['row'] == u2['row']):
                adjacency[u1['id']].add(u2['id'])

# PHASE 1: PLACE 5 SEEDS STRATEGICALLY

print(f"\n{'='*60}")
print("PHASE 1: SEED PLACEMENT")
print(f"{'='*60}")

# Sort by Democratic lean
df_sorted = df.sort_values('dem_pct', ascending=False)

# Strategy: 
# - Place target_dem_seats seeds in most Democratic areas
# - Place target_rep_seats seeds in most Republican areas

seeds = []
seed_target = {}  # Track intended party for each seed

# Place Dem seeds
print(f"Placing {target_dem_seats} Democratic seeds...")
dem_pool = df_sorted.head(10)  # Top 10 most Dem units

for i in range(target_dem_seats):
    # Pick from Dem pool, spaced apart
    if i == 0:
        seed = dem_pool.iloc[0]['id']
    else:
        # Pick one far from existing seeds
        best_seed = None
        max_min_dist = 0
        for _, candidate in dem_pool.iterrows():
            if candidate['id'] not in seeds:
                # Calculate distance to nearest existing seed
                min_dist = 999
                for existing in seeds:
                    existing_unit = df[df['id'] == existing].iloc[0]
                    dist = abs(candidate['row'] - existing_unit['row']) + \
                           abs(candidate['col'] - existing_unit['col'])
                    min_dist = min(min_dist, dist)
                
                if min_dist > max_min_dist:
                    max_min_dist = min_dist
                    best_seed = candidate['id']
        
        if best_seed is not None:
            seed = best_seed
        else:
            # Fallback
            for _, c in dem_pool.iterrows():
                if c['id'] not in seeds:
                    seed = c['id']
                    break
    
    seeds.append(seed)
    seed_target[seed] = 'DEM'
    unit = df[df['id'] == seed].iloc[0]
    print(f"  Seed {i+1} at ({unit['row']},{unit['col']}): {unit['dem_pct']:.1%} D")

# Place Rep seeds
print(f"\nPlacing {target_rep_seats} Republican seeds...")
rep_pool = df_sorted.tail(10)  # Top 10 most Rep units

for i in range(target_rep_seats):
    if i == 0:
        seed = rep_pool.iloc[0]['id']
    else:
        best_seed = None
        max_min_dist = 0
        for _, candidate in rep_pool.iterrows():
            if candidate['id'] not in seeds:
                min_dist = 999
                for existing in seeds:
                    existing_unit = df[df['id'] == existing].iloc[0]
                    dist = abs(candidate['row'] - existing_unit['row']) + \
                           abs(candidate['col'] - existing_unit['col'])
                    min_dist = min(min_dist, dist)
                
                if min_dist > max_min_dist:
                    max_min_dist = min_dist
                    best_seed = candidate['id']
        
        if best_seed is not None:
            seed = best_seed
        else:
            for _, c in rep_pool.iterrows():
                if c['id'] not in seeds:
                    seed = c['id']
                    break
    
    seeds.append(seed)
    seed_target[seed] = 'REP'
    unit = df[df['id'] == seed].iloc[0]
    print(f"  Seed {i+1} at ({unit['row']},{unit['col']}): {unit['dem_pct']:.1%} D")

# PHASE 2: GROW DISTRICTS FROM SEEDS

print(f"\n{'='*60}")
print("PHASE 2: BALANCED GROWTH")
print(f"{'='*60}")

assignment = {}
district_target = {}

# Assign seeds to districts
for district_id, seed_id in enumerate(seeds, start=1):
    assignment[seed_id] = district_id
    district_target[district_id] = seed_target[seed_id]
    print(f"District {district_id} ({seed_target[seed_id]}): starts with unit {seed_id}")

unassigned = set(df['id']) - set(seeds)

iteration = 0
while unassigned and iteration < 50:
    iteration += 1
    assigned_this_round = []
    
    for unit_id in list(unassigned):
        # Find adjacent districts
        adjacent_districts = set()
        for neighbor in adjacency[unit_id]:
            if neighbor in assignment:
                adjacent_districts.add(assignment[neighbor])
        
        if not adjacent_districts:
            continue
        
        # Get unit info
        unit = df[df['id'] == unit_id].iloc[0]
        
        # Score each adjacent district
        best_district = None
        best_score = -999999
        
        for dist_id in adjacent_districts:
            score = 0
            
            # Prefer adding unit to district with matching partisan lean
            target = district_target[dist_id]
            if target == 'DEM' and unit['dem_pct'] > 0.5:
                score += 100  # Dem unit to Dem district
            elif target == 'REP' and unit['dem_pct'] < 0.5:
                score += 100  # Rep unit to Rep district
            else:
                score += 20  # Neutral/mismatched
            
            if score > best_score:
                best_score = score
                best_district = dist_id
        
        if best_district:
            assignment[unit_id] = best_district
            assigned_this_round.append(unit_id)
    
    for uid in assigned_this_round:
        unassigned.remove(uid)
    
    if iteration % 10 == 0:
        print(f"  Iteration {iteration}: {len(unassigned)} units remaining")
    
    if not assigned_this_round:
        break

# Handle any remaining unassigned units
if unassigned:
    print(f"  Assigning {len(unassigned)} isolated units...")
    for uid in unassigned:
        # Assign to district 1 as fallback
        assignment[uid] = 1

print(f"\nGrowth complete: All {len(assignment)} units assigned")

# PHASE 3: CALCULATE RESULTS

print(f"\n{'='*60}")
print("RESULTS")
print(f"{'='*60}")

results = []
for dist_id in range(1, N_DISTRICTS + 1):
    district_units = [u for u, d in assignment.items() if d == dist_id]
    district_df = df[df['id'].isin(district_units)]
    
    pop = district_df['pop'].sum()
    dem_votes = district_df['dem'].sum()
    rep_votes = district_df['rep'].sum()
    total_votes = dem_votes + rep_votes
    
    dem_pct = dem_votes / total_votes if total_votes > 0 else 0.5
    winner = 'DEM' if dem_pct > 0.5 else 'REP'
    target = district_target[dist_id]
    match = '✓' if winner == target else '✗'
    
    results.append({
        'district': dist_id,
        'units': len(district_units),
        'population': pop,
        'dem_votes': dem_votes,
        'rep_votes': rep_votes,
        'dem_pct': dem_pct * 100,
        'winner': winner,
        'target': target,
        'match': match
    })
    
    print(f"\nDistrict {dist_id} ({target} target):")
    print(f"  Units: {len(district_units)}")
    print(f"  Population: {pop:,}")
    print(f"  Votes: {dem_pct:.1%} D, {(1-dem_pct):.1%} R")
    print(f"  Winner: {winner} {match}")

results_df = pd.DataFrame(results)

# Summary
dem_wins = (results_df['winner'] == 'DEM').sum()
rep_wins = (results_df['winner'] == 'REP').sum()

print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")

print(f"\nSeat Distribution:")
print(f"  Democratic: {dem_wins}/{N_DISTRICTS} seats")
print(f"  Republican: {rep_wins}/{N_DISTRICTS} seats")
print(f"  Target: {target_dem_seats} D, {target_rep_seats} R")

if dem_wins == target_dem_seats:
    print(f"  ✓ PROPORTIONAL REPRESENTATION ACHIEVED!")
else:
    print(f"  Gap: {abs(dem_wins - target_dem_seats)} seats off target")

# Efficiency gap
total_dem_wasted = 0
total_rep_wasted = 0
total_votes = results_df['dem_votes'].sum() + results_df['rep_votes'].sum()

for _, row in results_df.iterrows():
    threshold = (row['dem_votes'] + row['rep_votes']) / 2
    if row['winner'] == 'DEM':
        total_dem_wasted += (row['dem_votes'] - threshold)
        total_rep_wasted += row['rep_votes']
    else:
        total_rep_wasted += (row['rep_votes'] - threshold)
        total_dem_wasted += row['dem_votes']

efficiency_gap = abs(total_dem_wasted - total_rep_wasted) / total_votes

print(f"\nEfficiency Gap: {efficiency_gap:.1%}")
if efficiency_gap < 0.07:
    print("  ✓ FAIR")
else:
    print(f"  ⚠ Above 7% threshold")

# Save
results_df.to_csv('/mnt/user-data/outputs/seed_5districts.csv', index=False)
print(f"\n✓ Results saved to seed_5districts.csv")

print(f"\n{'='*60}")
print("ALGORITHM DEMONSTRATES:")
print("  1. Strategic seed placement (in partisan areas)")
print("  2. Balanced growth (districts compete for units)")
print("  3. Partisan targeting (Dem seeds grow Dem districts)")
print(f"{'='*60}\n")