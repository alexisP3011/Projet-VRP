import folium
import random
from folium.plugins import MarkerCluster
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, value, LpStatus

def create_vehicle_routing_model(n_cities, n_trucks, distances, deliveries, truck_capacity):
    """
    CVRP
    Parameters:
    n_cities (int): Number of cities
    n_trucks (int): Number of trucks
    distances (dict): Distances between cities {(i,j): distance}
    deliveries (dict): Deliveries per city {city: delivery}
    truck_capacity (float): Maximum capacity of each truck
    """
    prob = LpProblem("Vehicle_Routing_Problem", LpMinimize)
    
    cities = range(n_cities)
    trucks = range(n_trucks)
    
    x = LpVariable.dicts("route", 
                        ((i, j, k) for i in cities for j in cities for k in trucks),
                        cat='Binary')
    
    y = LpVariable.dicts("assignment",
                        ((i, k) for i in cities for k in trucks),
                        cat='Binary')
    
    prob += lpSum(distances[i, j] * x[i, j, k] for i in cities for j in cities for k in trucks if i != j)
    
    for k in trucks:
        prob += lpSum(deliveries[i] * y[i, k] for i in cities if i != 0) <= truck_capacity
    
    for i in cities:
        if i != 0:
            prob += lpSum(y[i, k] for k in trucks) == 1
    
    for h in cities:
        for k in trucks:
            prob += lpSum(x[i, h, k] for i in cities if i != h) == \
                   lpSum(x[h, j, k] for j in cities if j != h)
    
    for i in cities:
        if i != 0:
            for k in trucks:
                prob += lpSum(x[j, i, k] for j in cities if j != i) == y[i, k]
    
    for k in trucks:
        prob += lpSum(x[0, j, k] for j in cities if j != 0) == 1
        prob += lpSum(x[i, 0, k] for i in cities if i != 0) == 1
    
    prob.solve()
    
    return prob, x, y

def print_delivery_details(route, deliveries, city_names, truck_capacity):
    remaining_load = sum(deliveries[city_idx] for city_idx in route[1:-1])
    initial_load = remaining_load
    
    print("\nDelivery Details:")
    print(f"Total truck capacity: {truck_capacity} pallets")
    print(f"Departure from {city_names[0]} - Initial load: {initial_load} pallets")
    print(f"Initial fill rate: {(initial_load/truck_capacity)*100:.1f}%")
    
    for i, city_idx in enumerate(route[1:-1]):
        print(f"\nStop at {city_names[city_idx]}:")
        print(f"  - Delivering {deliveries[city_idx]} pallets")
        remaining_load -= deliveries[city_idx]
        print(f"   Remaining load: {remaining_load} pallets")
        print(f"   Fill rate: {(remaining_load/truck_capacity)*100:.1f}%")

def create_map(city_coords, routes, city_names):
    france_map = folium.Map(location=[46.603354, 1.888334], zoom_start=6)
    
    marker_cluster = MarkerCluster().add_to(france_map)
    
    for city, coords in city_coords.items():
        if city == 0:  # Nancy
            folium.Marker(
                location=coords,
                popup=city_names[city],
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(marker_cluster)
        else:
            folium.Marker(
                location=coords,
                popup=city_names[city]
            ).add_to(marker_cluster)
    
    colors = ['blue', 'green', 'red', 'purple', 'orange']
    
    for truck_id, route in enumerate(routes):
        complete_route = [0]
        complete_route.extend(route)
        if complete_route[-1] != 0:
            complete_route.append(0)
            
        route_coords = [city_coords[city] for city in complete_route]
        
        folium.PolyLine(
            route_coords,
            color=colors[truck_id % len(colors)],
            weight=3,
            opacity=0.8,
            popup=f"Truck {truck_id + 1}"
        ).add_to(france_map)
    
    return france_map

def main():
    n_cities = 7
    n_trucks = 3
    
    city_names = {
        0: "Nancy",      
        1: "Paris",
        2: "Reims",
        3: "Orléans",
        4: "Auxerre",
        5: "Dijon",
        6: "Metz"
    }
    
    city_coords = {
        0: [48.6921, 6.1844],  
        1: [48.8566, 2.3522],  
        2: [49.2583, 4.0317],  
        3: [47.9026, 1.9099],  
        4: [47.8128, 3.5633],  
        5: [47.3220, 5.0415],  
        6: [49.1193, 6.1757]
    }
    
    distances = {
        (0, 1): 372, (0, 2): 231, (0, 3): 500, (0, 4): 400, (0, 5): 235, (0, 6): 60,
        (1, 0): 372, (1, 2): 143, (1, 3): 130, (1, 4): 169, (1, 5): 310, (1, 6): 332,
        (2, 0): 231, (2, 1): 143, (2, 3): 325, (2, 4): 275, (2, 5): 382, (2, 6): 219,
        (3, 0): 500, (3, 1): 130, (3, 2): 325, (3, 4): 198, (3, 5): 383, (3, 6): 490,
        (4, 0): 400, (4, 1): 169, (4, 2): 275, (4, 3): 198, (4, 5): 155, (4, 6): 390,
        (5, 0): 235, (5, 1): 310, (5, 2): 382, (5, 3): 383, (5, 4): 155, (5, 6): 295,
        (6, 0): 60,  (6, 1): 332, (6, 2): 219, (6, 3): 490, (6, 4): 390, (6, 5): 295
    }
    
    deliveries = {
        0: 0,    # Nancy (depot)
        1: 15,   # Paris
        2: 18,   # Reims
        3: 12,   # Orléans
        4: 20,   # Auxerre
        5: 16,   # Dijon
        6: 14    # Metz
    }
    
    truck_capacity = 35
    
    prob, x, y = create_vehicle_routing_model(n_cities, n_trucks, distances, deliveries, truck_capacity)
    
    if LpStatus[prob.status] == 'Optimal':
        print("Optimal solution found!")
        print("\nDetailed route analysis:")
        print(f"Starting point: {city_names[0]} (depot)")
        
        total_distance = 0
        routes = []
        for k in range(n_trucks):
            print(f"\n{'='*50}")
            print(f"TRUCK {k+1}")
            print('='*50)
            
            route = [0]
            current_city = 0
            route_distance = 0
            route_deliveries = 0
            
            while True:
                next_city = None
                for j in range(n_cities):
                    if j != current_city and value(x[current_city, j, k]) > 0.5:
                        route.append(j)
                        if j != 0:  
                            route_deliveries += deliveries[j]
                        route_distance += distances[current_city, j]
                        current_city = j
                        next_city = j
                        break
                if next_city is None or next_city == 0:
                    if route[-1] != 0:
                        route.append(0)
                        route_distance += distances[current_city, 0]
                    break
            
            route_cities = [city_names[i] for i in route]
            print(f"Route: {' - '.join(route_cities)}")
            
            print_delivery_details(route, deliveries, city_names, truck_capacity)
            
            print(f"\nSummary for truck {k+1}:")
            print(f"- Total delivered: {route_deliveries} pallets")
            print(f"- Capacity utilization: {(route_deliveries/truck_capacity)*100:.1f}%")
            print(f"- Distance traveled: {route_distance} km")
            
            total_distance += route_distance
            routes.append(route)
        
        print(f"\n{'='*50}")
        print("GLOBAL SUMMARY")
        print(f"{'='*50}")
        print(f"Total distance traveled: {total_distance} km")
        print(f"Total solution cost: {value(prob.objective)}")
        
        total_deliveries = sum(deliveries.values())
        average_load = total_deliveries / n_trucks
        print(f"Average load per truck: {average_load:.1f} pallets")
        print(f"Average utilization rate: {(average_load/truck_capacity)*100:.1f}%")
        
        france_map = create_map(city_coords, routes, city_names)
        france_map.save("delivery_routes_map_final.html")
        print("Route map saved as 'delivery_routes_map_final.html'.")
    else:
        print("No optimal solution found")

if __name__ == "__main__":
    main()